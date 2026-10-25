"""Identidad: usuarios, roles, sesiones revocables y bloqueo por intentos.

Reglas (documento 02 del expediente, adaptadas al núcleo):
- Contraseña individual mínima de 12 caracteres, hash adaptativo con sal.
- Sin contraseña predeterminada ni cuenta oculta.
- Bloqueo temporal tras 5 intentos fallidos (15 minutos).
- Sesiones de servidor revocables; cambiar la contraseña revoca las demás.
- Sin dependencias de Flask: este módulo sólo recibe la URL de la base.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from psycopg.errors import UniqueViolation
from werkzeug.security import check_password_hash, generate_password_hash

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row

MIN_PASSWORD_LENGTH = 12
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15
SESSION_HOURS = 12
ROLES = ('admin', 'user')

USERNAME_TAKEN = 'username_taken'
WEAK_PASSWORD = 'weak_password'
INVALID_USERNAME = 'invalid_username'
INVALID_ROLE = 'invalid_role'
BAD_CREDENTIALS = 'bad_credentials'
LOCKED = 'locked'
INACTIVE = 'inactive'
NOT_FOUND = 'not_found'
WRONG_PASSWORD = 'wrong_password'


def _now(clock=None):
    current = clock or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current


def _hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _public_user(user):
    data = row(user)
    data.pop('password_hash', None)
    return data


def _validate_username(username):
    name = (username or '').strip().lower()
    if not name or not name.replace('_', '').replace('.', '').replace('-', '').isalnum():
        return None
    return name


def create_user(url, *, username, password, full_name='', role='user', is_active=True):
    """Crea un usuario validando nombre, política de contraseña y rol."""
    name = _validate_username(username)
    if not name or len(name) > 40:
        return {'ok': False, 'code': INVALID_USERNAME,
                'message': 'Nombre de usuario no válido (letras, números, . _ -)'}
    if role not in ROLES:
        return {'ok': False, 'code': INVALID_ROLE, 'message': 'Rol no válido'}
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return {'ok': False, 'code': WEAK_PASSWORD,
                'message': f'La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres'}
    try:
        with transaction(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO users (username, password_hash, full_name, role, is_active)
                       VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                    (name, generate_password_hash(password, method='scrypt'),
                     (full_name or '').strip()[:120], role, is_active))
                user = cur.fetchone()
    except UniqueViolation:
        return {'ok': False, 'code': USERNAME_TAKEN,
                'message': 'Ese nombre de usuario ya existe'}
    return {'ok': True, 'code': 'created', 'user': _public_user(user)}


def authenticate(url, *, username, password, clock=None):
    """Verifica credenciales con bloqueo temporal y crea la sesión."""
    current = _now(clock)
    name = (username or '').strip().lower()
    if not name or not isinstance(password, str) or not password:
        return {'ok': False, 'code': BAD_CREDENTIALS,
                'message': 'Usuario o contraseña incorrectos'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (name,))
            user = cur.fetchone()
            if not user:
                return {'ok': False, 'code': BAD_CREDENTIALS,
                        'message': 'Usuario o contraseña incorrectos'}
            if user['locked_until'] and user['locked_until'] > current:
                return {'ok': False, 'code': LOCKED,
                        'message': 'Cuenta bloqueada por intentos fallidos; espere unos minutos',
                        'retry_at': row(user)['locked_until']}
            if not user['is_active']:
                return {'ok': False, 'code': INACTIVE,
                        'message': 'La cuenta está desactivada; contacte al administrador'}
            if not check_password_hash(user['password_hash'], password):
                attempts = user['failed_attempts'] + 1
                locked_until = None
                if attempts >= MAX_FAILED_ATTEMPTS:
                    locked_until = current + timedelta(minutes=LOCK_MINUTES)
                    attempts = 0
                cur.execute(
                    """UPDATE users SET failed_attempts=%s, locked_until=%s,
                       updated_at=%s WHERE id=%s""",
                    (attempts, locked_until, current, user['id']))
                return {'ok': False, 'code': BAD_CREDENTIALS,
                        'message': 'Usuario o contraseña incorrectos'}
            if user['failed_attempts'] or user['locked_until']:
                cur.execute(
                    """UPDATE users SET failed_attempts=0, locked_until=NULL
                       WHERE id=%s""", (user['id'],))
            token = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(24)
            expires = current + timedelta(hours=SESSION_HOURS)
            cur.execute(
                """INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at)
                   VALUES (%s, %s, %s, %s)""",
                (_hash_token(token), user['id'], csrf, expires))
    return {'ok': True, 'code': 'authenticated', 'token': token, 'csrf': csrf,
            'expires_at': expires.astimezone(timezone.utc).isoformat(),
            'user': _public_user(user)}


def user_for_session(url, *, token, clock=None):
    """Devuelve (usuario, sesión) si el token sigue vigente y activo."""
    if not token:
        return None, None
    current = _now(clock)
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT s.* FROM sessions s
                   WHERE s.token_hash = %s AND s.revoked_at IS NULL
                     AND s.expires_at > %s""",
                (_hash_token(token), current))
            session = cur.fetchone()
            if not session:
                return None, None
            cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
            user = cur.fetchone()
            if not user or not user['is_active']:
                return None, None
    return _public_user(user), {'id': session['id'], 'csrf_token': session['csrf_token'],
                                'expires_at': row(session)['expires_at']}


def logout(url, *, token):
    """Revoca una sesión concreta."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE sessions SET revoked_at = now() WHERE token_hash = %s',
                (_hash_token(token),))
    return {'ok': True, 'code': 'logged_out'}


def revoke_all_sessions(url, *, user_id):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE sessions SET revoked_at = now() WHERE user_id = %s',
                (user_id,))
    return {'ok': True, 'code': 'revoked'}


def change_password(url, *, user_id, current_password, new_password, clock=None):
    """Cambia la contraseña tras verificar la actual; revoca todas las sesiones."""
    if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
        return {'ok': False, 'code': WEAK_PASSWORD,
                'message': f'La nueva contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cur.fetchone()
            if not user:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Usuario no encontrado'}
            if not check_password_hash(user['password_hash'], current_password or ''):
                return {'ok': False, 'code': WRONG_PASSWORD,
                        'message': 'La contraseña actual no es correcta'}
            cur.execute(
                """UPDATE users SET password_hash=%s, updated_at=%s WHERE id=%s""",
                (generate_password_hash(new_password, method='scrypt'),
                 _now(clock), user_id))
            cur.execute('UPDATE sessions SET revoked_at=now() WHERE user_id=%s', (user_id,))
    return {'ok': True, 'code': 'changed'}


def list_users(url):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM users ORDER BY id')
            users = cur.fetchall()
    return [_public_user(u) for u in users]


def set_user_role(url, *, user_id, role):
    """Cambia el rol y revoca TODAS sus sesiones en la misma transacción
    (CORR01/R06): ningún token anterior conserva privilegios."""
    if role not in ROLES:
        return {'ok': False, 'code': INVALID_ROLE, 'message': 'Rol no válido'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE sessions SET revoked_at=now() '
                        'WHERE user_id=%s AND revoked_at IS NULL', (user_id,))
            cur.execute('UPDATE users SET role=%s, updated_at=now() WHERE id=%s '
                        'RETURNING id', (role, user_id))
            if not cur.fetchone():
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Usuario no encontrado'}
    return {'ok': True, 'code': 'updated'}


def set_user_active(url, *, user_id, active):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            if active:
                cur.execute(
                    """UPDATE users SET is_active=true, failed_attempts=0,
                       locked_until=NULL, updated_at=now() WHERE id=%s RETURNING id""",
                    (user_id,))
            else:
                cur.execute(
                    'UPDATE sessions SET revoked_at=now() WHERE user_id=%s',
                    (user_id,))
                cur.execute(
                    'UPDATE users SET is_active=false, updated_at=now() '
                    'WHERE id=%s RETURNING id', (user_id,))
            if not cur.fetchone():
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Usuario no encontrado'}
    return {'ok': True, 'code': 'updated'}


def admin_reset_password(url, *, username, new_password):
    """CORR01B/R01: reinicio interactivo seguro usado por el CLI (getpass).
    Exige la política de contraseña; revoca todas las sesiones del usuario."""
    if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
        return {'ok': False, 'code': WEAK_PASSWORD,
                'message': f'La nueva contraseña debe tener al menos '
                           f'{MIN_PASSWORD_LENGTH} caracteres'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE username = %s',
                        ((username or '').strip().lower(),))
            found = cur.fetchone()
            if not found:
                return {'ok': False, 'code': NOT_FOUND,
                        'message': 'Usuario no encontrado'}
            cur.execute(
                'UPDATE users SET password_hash=%s, failed_attempts=0, '
                'locked_until=NULL, updated_at=now() WHERE id=%s',
                (generate_password_hash(new_password, method='scrypt'),
                 found['id']))
            cur.execute('UPDATE sessions SET revoked_at=now() WHERE user_id=%s',
                        (found['id'],))
    return {'ok': True, 'code': 'rotated', 'user_id': found['id']}
