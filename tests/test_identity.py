"""Identidad: usuarios, bloqueo, sesiones revocables y cambio de contraseña."""
from datetime import datetime, timedelta, timezone

from crm_premium.modules.identity import service as identity


def test_usuario_duplicado_rechazado(db_url):
    first = identity.create_user(db_url, username='ana', password='ClaveLarga.2026')
    assert first['ok']
    again = identity.create_user(db_url, username='ANA', password='OtraClave.2026')
    assert not again['ok'] and again['code'] == 'username_taken'


def test_contrasena_debil_rechazada(db_url):
    result = identity.create_user(db_url, username='ana', password='corta123')
    assert not result['ok'] and result['code'] == 'weak_password'


def test_usuario_invalido_rechazado(db_url):
    result = identity.create_user(db_url, username='mal usuario!',
                                  password='ClaveLarga.2026')
    assert not result['ok'] and result['code'] == 'invalid_username'


def test_autenticacion_ok_y_erronea(db_url):
    identity.create_user(db_url, username='ana', password='ClaveLarga.2026')
    ok = identity.authenticate(db_url, username='ana', password='ClaveLarga.2026')
    assert ok['ok'] and ok['token']
    bad = identity.authenticate(db_url, username='ana', password='Incorrecta.2026')
    assert not bad['ok'] and bad['code'] == 'bad_credentials'


def test_bloqueo_tras_cinco_intentos(db_url):
    identity.create_user(db_url, username='beto', password='ClaveLarga.2026')
    result = {}
    for _ in range(5):
        result = identity.authenticate(db_url, username='beto', password='mal')
    assert result['code'] == 'bad_credentials'
    sixth = identity.authenticate(db_url, username='beto', password='ClaveLarga.2026')
    assert not sixth['ok'] and sixth['code'] == 'locked'


def test_sesion_y_revocacion(db_url):
    created = identity.create_user(db_url, username='cara', password='ClaveLarga.2026')
    auth = identity.authenticate(db_url, username='cara', password='ClaveLarga.2026')
    user, session = identity.user_for_session(db_url, token=auth['token'])
    assert user['id'] == created['user']['id']
    assert session['csrf_token'] == auth['csrf']
    identity.revoke_all_sessions(db_url, user_id=user['id'])
    user2, session2 = identity.user_for_session(db_url, token=auth['token'])
    assert user2 is None and session2 is None


def test_cambio_contrasena_revoca_sesiones(db_url):
    identity.create_user(db_url, username='dana', password='ClaveLarga.2026')
    auth = identity.authenticate(db_url, username='dana', password='ClaveLarga.2026')
    wrong = identity.change_password(db_url, user_id=auth['user']['id'],
                                     current_password='NoEsLaClave.2026',
                                     new_password='NuevaClaveLarga.2026')
    assert not wrong['ok'] and wrong['code'] == 'wrong_password'
    changed = identity.change_password(db_url, user_id=auth['user']['id'],
                                       current_password='ClaveLarga.2026',
                                       new_password='NuevaClaveLarga.2026')
    assert changed['ok']
    user, _ = identity.user_for_session(db_url, token=auth['token'])
    assert user is None
    reauth = identity.authenticate(db_url, username='dana',
                                   password='NuevaClaveLarga.2026')
    assert reauth['ok']


def test_expiracion_de_sesion(db_url):
    identity.create_user(db_url, username='eva', password='ClaveLarga.2026')
    auth = identity.authenticate(db_url, username='eva', password='ClaveLarga.2026')
    future = datetime.now(timezone.utc) + timedelta(hours=13)
    user, _ = identity.user_for_session(db_url, token=auth['token'], clock=future)
    assert user is None


def test_desactivar_usuario_rechaza_login_y_revoca(db_url):
    created = identity.create_user(db_url, username='fede', password='ClaveLarga.2026')
    auth = identity.authenticate(db_url, username='fede', password='ClaveLarga.2026')
    identity.set_user_active(db_url, user_id=created['user']['id'], active=False)
    user, _ = identity.user_for_session(db_url, token=auth['token'])
    assert user is None
    login = identity.authenticate(db_url, username='fede', password='ClaveLarga.2026')
    assert not login['ok'] and login['code'] == 'inactive'
