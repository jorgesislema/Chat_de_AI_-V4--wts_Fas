"""Ámbitos por sede (E01): rol de ámbito independiente, denegación por
defecto y filtros de alcance para consultas.

Contrato E00B/E01:
- users.role conserva admin/user (cuenta); el alcance viene de
  user_branch_roles (director global o rol por sede).
- Sin filas de ámbito ⇒ sin acceso a datos por sede (denegación por
  defecto), salvo director explícito.
- El servidor aplica el alcance en agenda, ventas, inventario, BI,
  exportaciones y herramientas del asistente; ocultar menú no basta.
- Datos sin sede (NULL) no se abren a todos: visibles sólo para director
  (los backfills dejan NULL sólo transitoriamente).
"""
from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row

SCOPE_ROLES = ('director', 'gerente', 'asesor', 'almacen', 'finanzas',
               'analista')

#: Matriz acción → roles de ámbito autorizados (denegación por defecto).
#: «propias» se modela aparte (responsable = usuario) cuando aplique.
ACTION_ROLES = {
    'clients.view': SCOPE_ROLES,                    # alcance aplica a notas
    'clients.edit': ('director', 'gerente', 'asesor'),
    'agenda.view': SCOPE_ROLES,
    'agenda.create': ('director', 'gerente', 'asesor'),
    'agenda.transition': ('director', 'gerente', 'asesor'),
    'agenda.admin_correct': ('director', 'gerente'),
    'sales.view': ('director', 'gerente', 'asesor', 'finanzas'),
    'sales.create': ('director', 'gerente', 'asesor'),
    'sales.reverse': ('director', 'finanzas'),
    'inventory.view': SCOPE_ROLES,
    'inventory.manage': ('director', 'almacen'),
    'inventory.price': ('director',),
    'analytics.view': SCOPE_ROLES,
    'analytics.rebuild': ('director',),
    'assistant.ask': SCOPE_ROLES,
    'assistant.history_global': ('director',),
    'settings.manage': ('director',),
    'users.manage': ('director',),
    'branches.manage': ('director',),
}


class ScopeContext:
    """Alcance efectivo de un usuario en una petición."""

    def __init__(self, is_director, branches, role_at):
        self.is_director = is_director          # director global (todas)
        self.branches = branches                # ids con rol asignado
        self.role_at = role_at                  # {branch_id: scope_role}

    @property
    def authenticated(self):
        return self.is_director or bool(self.branches)

    def allowed(self, branch_id):
        if branch_id is None:
            # Datos sin sede: sólo director (los backfills evitan NULL).
            return self.is_director
        if self.is_director:
            return True
        return branch_id in self.branches

    def can(self, action, branch_id=None):
        roles = ACTION_ROLES.get(action, ())
        if branch_id is None:
            # Acción global (p. ej. settings, rebuild): sólo director.
            return self.is_director and (not roles or 'director' in roles)
        if self.is_director:
            return 'director' in roles or bool(roles)
        role = self.role_at.get(branch_id)
        return role is not None and role in roles

    def branch_filter(self):
        """Lista de sedes consultables; None = todas (director)."""
        return None if self.is_director else sorted(self.branches)

    def branches_for(self, action):
        """Sedes autorizadas PARA ESA ACCIÓN (E01-R/A2); None = todas.

        Corrige el cruce de roles: un usuario gerente en A y almacén en B
        obtiene [A] para 'sales.view' y [B] para 'inventory.manage'; el filtro
        genérico branch_filter() mezclaba ambas y abría ventas de B.
        """
        roles = ACTION_ROLES.get(action, ())
        if self.is_director:
            return None
        return sorted(b for b, r in self.role_at.items() if r in roles)

    def can_any(self, action):
        """Vista del recurso en ALGUNA sede del ámbito (p. ej. listados)."""
        roles = ACTION_ROLES.get(action, ())
        if self.is_director:
            return 'director' in roles or bool(roles)
        return any(r in roles for r in self.role_at.values())


def load_scope(url, user_id, is_admin=False):
    """Carga el alcance de un usuario. El admin de cuenta conserva su papel
    histórico como director global (compatibilidad núcleo de dos roles)."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT scope_role, branch_id FROM user_branch_roles
                   WHERE user_id = %s""", (user_id,))
            rows = cur.fetchall()
    role_at = {}
    branches = []
    is_director = is_admin
    for r in rows:
        if r['scope_role'] == 'director':
            is_director = True
        elif r['branch_id'] is not None:
            role_at[r['branch_id']] = r['scope_role']
            branches.append(r['branch_id'])
    return ScopeContext(is_director=is_director, branches=branches,
                        role_at=role_at)


def assign_scope(url, *, user_id, scope_role, branch_id):
    if scope_role not in SCOPE_ROLES:
        return {'ok': False, 'code': 'invalid_scope',
                'message': 'Rol de ámbito no válido'}
    if branch_id is None and scope_role != 'director':
        return {'ok': False, 'code': 'invalid_scope',
                'message': 'Sólo el director tiene ámbito global'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_branch_roles (user_id, branch_id, scope_role)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (user_id, branch_id, scope_role) DO NOTHING""",
                (user_id, branch_id, scope_role))
    return {'ok': True, 'code': 'assigned'}


def revoke_scope(url, *, user_id, scope_role, branch_id):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM user_branch_roles
                   WHERE user_id=%s AND scope_role=%s
                     AND ((branch_id IS NULL AND %s IS NULL)
                          OR branch_id=%s)""",
                (user_id, scope_role, branch_id, branch_id))
            # Regla de seguridad: al cambiar el alcance se revocan sesiones
            # (mismo criterio que el cambio de rol de cuenta).
            cur.execute('UPDATE sessions SET revoked_at=now() '
                        'WHERE user_id=%s AND revoked_at IS NULL', (user_id,))
    return {'ok': True, 'code': 'revoked'}


def list_assignments(url, user_id=None):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.*, u.username, b.name AS branch_name
                   FROM user_branch_roles r
                   JOIN users u ON u.id = r.user_id
                   LEFT JOIN branches b ON b.id = r.branch_id
                   WHERE (%s::bigint IS NULL OR r.user_id = %s)
                   ORDER BY u.username, r.scope_role""", (user_id, user_id))
            return [row(r) for r in cur.fetchall()]


def ensure_principal(url, zone='UTC'):
    """E01-M: sede «Principal» id=1 garantizada (idempotente) y re-backfill
    de filas sin sede. Se invoca desde organization.ensure().

    E01-R/A3: ya NO concede ámbitos (user_branch_roles). El backfill de
    permisos es operación única de las migraciones 0006/0007 (con
    procedencia); reparar permisos durante un GET podría reponer un ámbito
    revocado. Un usuario nuevo sin asignación sigue sin acceso (denegación
    por defecto); los ámbitos se asignan explícitamente en /branches.
    """
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO branches (id, name, timezone)
                   VALUES (1, 'Principal', %s)
                   ON CONFLICT (id) DO NOTHING""", (zone,))
            # Tras insertar con id explícito, alinea la secuencia (si no, el
            # próximo INSERT colisiona con id=1).
            cur.execute("SELECT setval('branches_id_seq', "
                        'GREATEST((SELECT COALESCE(max(id), 1) FROM branches), 1))')
            for table in ('resources', 'appointments', 'products', 'sales',
                          'stock_movements'):
                cur.execute(f'UPDATE {table} SET branch_id = 1 '
                            'WHERE branch_id IS NULL')
            cur.execute(
                """INSERT INTO bi.dim_sede (branch_id, nombre)
                   SELECT id, name FROM branches
                   ON CONFLICT (branch_id) DO NOTHING""")


def list_branches(url, include_inactive=False):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM branches %s ORDER BY id' %
                ('' if include_inactive else 'WHERE is_active'))
            return [row(r) for r in cur.fetchall()]


def create_branch(url, *, name, timezone):
    clean = (name or '').strip()[:120]
    if not clean:
        return {'ok': False, 'code': 'invalid_name',
                'message': 'El nombre de la sede es obligatorio'}
    try:
        from ...shared.timeutil import resolve_zone
        resolve_zone(timezone)
    except Exception:
        return {'ok': False, 'code': 'invalid_zone',
                'message': 'Zona horaria no válida'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO branches (name, timezone) VALUES (%s, %s)
                   ON CONFLICT (name) DO UPDATE SET timezone = EXCLUDED.timezone
                   RETURNING *""", (clean, timezone))
            return {'ok': True, 'code': 'created', 'branch': row(cur.fetchone())}


def sql_in(allowed, column, placeholder_slot):
    """Fragmento SQL seguro para filtro por sedes: la lista proviene del
    servidor (scope), nunca del cliente. Devuelve (cláusula, parámetro)."""
    if allowed is None:
        return '', None
    if not allowed:
        # Sin sedes asignadas: no ver nada (predicado imposible).
        return f' AND {column} = -1', None
    ids = sorted(set(int(b) for b in allowed))
    marks = ', '.join(['%s'] * len(ids))
    return f' AND {column} IN ({marks})', ids
