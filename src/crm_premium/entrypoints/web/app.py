"""Punto de entrada web del CRM Premium (Flask/Jinja, sin CDN externo).

Seguridad del núcleo:
- Sesiones de servidor (cookie HttpOnly/SameSite=Lax) revocables.
- CSRF: cabecera ``X-CSRF-Token`` en la API y campo ``csrf_token`` en formularios;
  el login usa par anónimo cookie+campo para proteger el formulario inicial.
- Cabeceras: CSP ``default-src 'self'``, anti-clickjacking y sin sniffing.
- Autorización por rol (admin/user) en usuarios y correcciones administrativas.
"""
import os
import secrets
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (Flask, g, jsonify, make_response, redirect, render_template,
                   request, url_for)

from ...modules.scheduling import service as scheduling
from ...modules.assistant import service as assistant
from ...modules.analytics import service as analytics
from ...modules.commerce import service as commerce
from ...modules.contacts import service as contacts_module
from ...modules.dashboard import service as dashboard_module
from ...modules.identity import service as identity
from ...modules.organization import service as organization
from ...modules.scope import service as scope_service
from ...shared.timeutil import (InvalidZone, view_range, period_label, local_parts,
                                resolve_zone)

PRESENTATION = Path(__file__).resolve().parents[2] / 'presentation'
SESSION_COOKIE = 'crm_session'
LOGIN_CSRF_COOKIE = 'csrf_login'

#: Códigos de servicio → estado HTTP de la API.
STATUS_BY_CODE = {
    'bad_credentials': 401, 'locked': 401, 'inactive': 401,
    'forbidden': 403, 'not_found': 404,
    'overlap': 409, 'version_conflict': 409, 'outside_business_hours': 409,
    'invalid_transition': 409, 'too_late': 409, 'too_early': 409,
    'reason_required': 400, 'already_closed': 409, 'no_resurrection': 409,
    'past_datetime': 400, 'invalid_datetime': 400, 'invalid_range': 400,
    'invalid_zone': 400, 'nonexistent_local_time': 400, 'ambiguous_local_time': 400,
    'missing_resource': 400, 'inactive_resource': 400, 'resource_mismatch': 409,
    'cancelled_appointment': 409, 'invalid_title': 400, 'note_required': 400,
    'weak_password': 400, 'username_taken': 409, 'invalid_username': 400,
    'invalid_role': 400, 'wrong_password': 400, 'invalid_opening': 400,
    'invalid_sku': 400, 'invalid_kind': 400, 'sku_taken': 409,
    'price_required': 400, 'empty_sale': 400, 'invalid_line': 400,
    'insufficient_stock': 409, 'negative_stock': 409, 'already_reversed': 409,
}


def _api_error(result):
    return jsonify(ok=False, code=result['code'], message=result['message']), \
        STATUS_BY_CODE.get(result['code'], 400)


def _load_profile(url):
    profile = organization.get(url)
    if profile is None:
        profile = organization.ensure(url)
    return profile


def create_app(db_url=None):
    load_dotenv(Path(__file__).resolve().parents[4] / '.env')
    app = Flask(
        __name__,
        template_folder=str(PRESENTATION / 'templates'),
        static_folder=str(PRESENTATION / 'static'),
    )
    app.config['DATABASE_URL'] = db_url or os.environ['DATABASE_URL']
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', 'false') == 'true'
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

    def db():
        return app.config['DATABASE_URL']

    from contextlib import contextmanager as _cm
    from ...infrastructure.persistence.db import connect as _connect

    @_cm
    def _db_conn():
        conn = _connect(db())
        try:
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------ sesión
    @app.before_request
    def load_session_user():
        g.user = None
        g.session = None
        g.scope = None
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            user, session = identity.user_for_session(db(), token=token)
            if user:
                g.user = user
                g.session = session
                g.scope = scope_service.load_scope(
                    db(), user['id'], is_admin=user['role'] == 'admin')

    def scope_branches():
        """Sedes consultables del usuario (None = todas, director)."""
        return g.scope.branch_filter() if g.scope else []

    def branches_for(action):
        """Sedes autorizadas PARA ESA ACCIÓN (E01-R/A2); None = todas.

        Un usuario gerente en A y almacén en B recibe [A] para 'sales.view'
        y [B] para 'inventory.manage': el filtro por membresía genérica
        mezclaba roles y abría ventas de B.
        """
        return g.scope.branches_for(action) if g.scope else []

    def _resource_branch(cur, resource_id):
        cur.execute('SELECT branch_id FROM resources WHERE id=%s', (resource_id,))
        found = cur.fetchone()
        return found['branch_id'] if found else None

    def _appointment_branch(appointment_id):
        """Identidad mínima de la cita (sede) sin leer notas ni contenido."""
        with _db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT branch_id FROM appointments WHERE id=%s',
                            (appointment_id,))
                found = cur.fetchone()
        return found['branch_id'] if found else 'missing'

    def _product_branch(product_id):
        with _db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT branch_id FROM products WHERE id=%s',
                            (product_id,))
                found = cur.fetchone()
        return found['branch_id'] if found else 'missing'

    def _sale_branch(sale_id):
        with _db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT branch_id FROM sales WHERE id=%s', (sale_id,))
                found = cur.fetchone()
        return found['branch_id'] if found else 'missing'

    def _matrix_role(action, branch_id):
        """'admin' si la MATRIZ autoriza la acción en esa sede, si no 'user'.

        E01-R/A4: los servicios heredados exigen role='admin' de cuenta; la
        ruta traduce el permiso real (acción+sede) sin pasarlo indiscriminadamente.
        """
        return 'admin' if g.scope.can(action, branch_id) else 'user'

    def require(action, branch_id=None):
        """Denegación por defecto: comprueba la matriz y devuelve respuesta
        de error si el alcance no autoriza (403 API / redirect web)."""
        if g.scope and g.scope.can(action, branch_id):
            return None
        if request.path.startswith('/api/'):
            return jsonify(ok=False, code='forbidden',
                           message='Sin permiso para esta acción en este '
                                   'ámbito'), 403
        return redirect(url_for('dashboard'))

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                if request.path.startswith('/api/'):
                    return jsonify(ok=False, code='unauthenticated',
                                   message='Inicie sesión'), 401
                return redirect(url_for('login', next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None or g.user['role'] != 'admin':
                if request.path.startswith('/api/'):
                    return jsonify(ok=False, code='forbidden',
                                   message='Requiere administrador'), 403
                return redirect(url_for('dashboard'))
            return view(*args, **kwargs)
        return login_required(wrapped)

    def _csrf_ok():
        """CSRF de sesión (API por cabecera; formularios por campo)."""
        if g.session is None:
            return False
        provided = request.headers.get('X-CSRF-Token') or \
            request.form.get('csrf_token') or ''
        return secrets.compare_digest(provided, g.session['csrf_token'])

    @app.after_request
    def security_headers(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'")
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response

    # ------------------------------------------------------------------ login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            token = secrets.token_urlsafe(24)
            response = make_response(render_template('login.html', csrf_token=token))
            response.set_cookie(LOGIN_CSRF_COOKIE, token, httponly=True,
                                samesite='Lax', secure=app.config['COOKIE_SECURE'])
            return response
        form_token = request.form.get('csrf_token', '')
        cookie_token = request.cookies.get(LOGIN_CSRF_COOKIE, '')
        if not form_token or not cookie_token or \
                not secrets.compare_digest(form_token, cookie_token):
            return render_template('login.html', csrf_token=secrets.token_urlsafe(24),
                                   error='Sesión de formulario expirada; intente de nuevo.'), 400
        result = identity.authenticate(db(), username=request.form.get('username'),
                                       password=request.form.get('password'))
        if not result['ok']:
            # CORR01/R07: se regenera el PAR cookie+formulario coherente tras
            # el fallo, para que reintentar con la contraseña correcta funcione
            # sin recargar la página.
            fresh = secrets.token_urlsafe(24)
            response = make_response(render_template(
                'login.html', csrf_token=fresh,
                error=result['message']), 401)
            response.set_cookie(LOGIN_CSRF_COOKIE, fresh, httponly=True,
                                samesite='Lax', secure=app.config['COOKIE_SECURE'])
            return response
        next_url = request.args.get('next') or ''
        if not next_url.startswith('/') or next_url.startswith('//'):
            next_url = url_for('dashboard')
        response = make_response(redirect(next_url))
        response.set_cookie(SESSION_COOKIE, result['token'], httponly=True,
                            samesite='Lax', secure=app.config['COOKIE_SECURE'],
                            max_age=identity.SESSION_HOURS * 3600, path='/')
        response.delete_cookie(LOGIN_CSRF_COOKIE)
        return response

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        if _csrf_ok():
            identity.logout(db(), token=request.cookies.get(SESSION_COOKIE))
        response = make_response(redirect(url_for('login')))
        response.delete_cookie(SESSION_COOKIE)
        return response

    # ------------------------------------------------------------------ panel
    @app.route('/')
    @login_required
    def dashboard():
        profile = _load_profile(db())
        # E01-R/A2: el panel respeta el ámbito por acción; sin sedes para la
        # acción, ese bloque muestra cero (nunca el agregado global). El
        # resumen sólo agrega citas (y un conteo de contactos sin contenido).
        data = dashboard_module.summary(
            db(), zone=profile['zone'],
            appointment_branch_ids=branches_for('agenda.view'))
        return render_template('dashboard.html', profile=profile, summary=data)

    # ------------------------------------------------------------------ agenda
    @app.route('/agenda')
    @login_required
    def agenda_page():
        denied = None if g.scope.can_any('agenda.view') else require('agenda.view')
        if denied:
            return denied
        profile = _load_profile(db())
        branches = branches_for('agenda.view')
        resources = [r for r in scheduling.list_resources(db())
                     if r.get('branch_id') is None
                     or branches is None or r['branch_id'] in branches]
        services = [p for p in commerce.list_products(
            db(), kind='servicio', branch_ids=branches) if p['is_active']]
        return render_template('agenda.html', profile=profile,
                               resources=resources, branches=branches,
                               is_director=g.scope.is_director,
                               services=services)

    @app.route('/api/agenda')
    @login_required
    def api_agenda():
        denied = None if g.scope.can_any('agenda.view') else require('agenda.view')
        if denied:
            return denied
        profile = _load_profile(db())
        date_value = request.args.get('date')
        if not date_value:
            from datetime import datetime as _dt
            date_value = _dt.now(resolve_zone(profile['zone'])).date().isoformat()
        try:
            rng = view_range(request.args.get('view', 'week'),
                             date_value, profile['zone'])
        except ValueError as exc:
            return jsonify(ok=False, code='invalid_range', message=str(exc)), 400
        try:
            events = scheduling.list_appointments(
                db(), start_utc=rng['start_utc'], end_utc=rng['end_utc'],
                resource=request.args.get('resource'),
                status=request.args.get('status') or None,
                include_cancelled=request.args.get('cancelled') == '1',
                branch_ids=branches_for('agenda.view'))
        except ValueError as exc:
            return jsonify(ok=False, code='invalid_range', message=str(exc)), 400
        for event in events:
            start_local = local_parts(event['start_utc'], profile['zone'])
            end_local = local_parts(event['end_utc'], profile['zone'])
            event['start_date'] = start_local['date']
            event['start_time'] = start_local['time']
            event['end_date'] = end_local['date']
            event['end_time'] = end_local['time']
        return jsonify(ok=True, range=rng, label=period_label(rng), events=events,
                       zone=profile['zone'],
                       statuses=scheduling.STATUS_LABELS)

    @app.route('/api/appointments', methods=['POST'])
    @login_required
    def api_create_appointment():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        profile = _load_profile(db())
        data = request.get_json(silent=True) or {}
        resource_id = data.get('resource_id')
        try:
            resource_id = int(resource_id)
        except (TypeError, ValueError):
            return jsonify(ok=False, code='invalid_resource',
                           message='Recurso no válido'), 400
        with _db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT branch_id FROM resources WHERE id=%s',
                            (resource_id,))
                row = cur.fetchone()
        branch_id = row['branch_id'] if row else None
        denied = require('agenda.create', branch_id)
        if denied:
            return denied
        result = scheduling.save_appointment(
            db(), resource_id=resource_id,
            start=data.get('start'), end=data.get('end'),
            title=data.get('title'), zone=profile['zone'],
            contact_id=data.get('contact_id'), actor=g.user['id'],
            channel='web', role=g.user['role'],
            reason=data.get('reason'), service_id=data.get('service_id'),
            window_policy=organization.build_window_policy(profile))
        if not result['ok']:
            return _api_error(result)
        return jsonify(result), 201

    @app.route('/api/appointments/<int:appointment_id>')
    @login_required
    def api_appointment_detail(appointment_id):
        # E01-R/A1: autorización por acción+sede ANTES de leer notas/historial.
        branch = _appointment_branch(appointment_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Cita no encontrada'), 404
        denied = require('agenda.view', branch)
        if denied:
            return denied
        result = scheduling.appointment_detail(
            db(), appointment_id=appointment_id, role=g.user['role'])
        if not result['ok']:
            return _api_error(result)
        profile = _load_profile(db())
        for key in ('start_utc', 'end_utc'):
            result['appointment'][key.replace('_utc', '_local')] = \
                local_parts(result['appointment'][key], profile['zone'])
        return jsonify(result)

    #: Acción de transición → acción de matriz exigida sobre la sede de la cita.
    TRANSITION_ACTIONS = {
        'confirm': 'agenda.transition', 'cancel': 'agenda.transition',
        'attend': 'agenda.transition', 'no_show': 'agenda.transition',
        'reprogram': 'agenda.transition', 'note': 'agenda.transition',
        'correct': 'agenda.admin_correct',
    }

    @app.route('/api/appointments/<int:appointment_id>/transition', methods=['POST'])
    @login_required
    def api_transition(appointment_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        profile = _load_profile(db())
        data = request.get_json(silent=True) or {}
        action = data.get('action')
        required = TRANSITION_ACTIONS.get(action)
        if not required:
            # E01-R/A1: acciones desconocidas se deniegan siempre.
            return jsonify(ok=False, code='invalid_action',
                           message='Acción no válida'), 400
        # E01-R/A1: identidad mínima de la cita y guardia de matriz ANTES de
        # tocar el servicio; el actor/sede vienen de la sesión, no del JSON.
        branch = _appointment_branch(appointment_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Cita no encontrada'), 404
        denied = require(required, branch)
        if denied:
            return denied
        common = dict(appointment_id=appointment_id, actor=g.user['id'],
                      expected_version=data.get('expected_version'))
        service = scheduling
        if action == 'confirm':
            result = service.confirm_appointment(db(), **common)
        elif action == 'cancel':
            result = service.cancel_appointment(db(), **common,
                                                reason=data.get('reason'))
        elif action in ('attend', 'no_show'):
            result = service.mark_attendance(
                db(), appointment_id=appointment_id, outcome=action,
                expected_version=data.get('expected_version'), actor=g.user['id'])
        elif action == 'reprogram':
            result = service.reprogram_appointment(
                db(), appointment_id=appointment_id, start=data.get('start'),
                end=data.get('end'), title=data.get('title'),
                zone=profile['zone'],
                expected_version=data.get('expected_version'),
                reason=data.get('reason'), actor=g.user['id'],
                role=g.user['role'],
                window_policy=organization.build_window_policy(profile))
        elif action == 'correct':
            # E01-R/A2: la matriz (director/gerente en esa sede) decide el
            # rol de servicio; el rol de cuenta solo ya no basta.
            result = service.admin_correct_status(
                db(), appointment_id=appointment_id, target=data.get('target'),
                reason=data.get('reason'),
                expected_version=data.get('expected_version'),
                actor=g.user['id'],
                role=_matrix_role('agenda.admin_correct', branch))
        elif action == 'note':
            result = service.add_note(db(), appointment_id=appointment_id,
                                      body=data.get('body'), author=g.user['id'])
        else:  # pragma: no cover - cubierto por el mapa de acciones
            return jsonify(ok=False, code='invalid_action',
                           message='Acción no válida'), 400
        if not result['ok']:
            return _api_error(result)
        return jsonify(result)

    # ------------------------------------------------------------------ contactos
    @app.route('/contacts')
    @login_required
    def contacts_page():
        # E01-R/A1: los contactos son PII; sin membresía con clients.view no
        # se lista nada (denegación por defecto).
        denied = None if g.scope.can_any('clients.view') else require('clients.view')
        if denied:
            return denied
        q = request.args.get('q', '')
        page = max(1, int(request.args.get('page', 1) or 1))
        result = contacts_module.list_contacts(
            db(), q=q, limit=20, offset=(page - 1) * 20)
        return render_template('contacts.html', q=q, page=page, listing=result)

    @app.route('/contacts', methods=['POST'])
    @login_required
    def contacts_create():
        denied = None if g.scope.can_any('clients.edit') else require('clients.edit')
        if denied:
            return denied
        if not _csrf_ok():
            return render_template('contacts.html', q='', page=1,
                                   listing=contacts_module.list_contacts(db()),
                                   error='Token CSRF no válido; recargue e intente de nuevo'), 403
        result = contacts_module.create(
            db(), full_name=request.form.get('full_name'),
            phone=request.form.get('phone'), email=request.form.get('email'),
            notes=request.form.get('notes'), channel='web')
        if not result['ok']:
            listing = contacts_module.list_contacts(db())
            return render_template('contacts.html', q='', page=1, listing=listing,
                                   error=result['message']), 400
        return redirect(url_for('contacts_page'))

    @app.route('/contacts/<int:contact_id>')
    @login_required
    def contact_detail(contact_id):
        contact = contacts_module.get(db(), contact_id)
        if not contact:
            return redirect(url_for('contacts_page'))
        # E01-R/A1: el perfil del contacto no revela citas fuera del ámbito
        # agenda.view del usuario (ni notas: el listado no las incluye).
        denied = None if g.scope.can_any('clients.view') else require('clients.view')
        if denied:
            return denied
        appointments = scheduling.appointments_for_contact(
            db(), contact_id=contact_id, limit=50,
            branch_ids=branches_for('agenda.view'))
        return render_template('contact_detail.html', contact=contact,
                               appointments=appointments,
                               status_labels=scheduling.STATUS_LABELS)

    # ------------------------------------------------------------------ ajustes
    @app.route('/settings')
    @login_required
    def settings():
        profile = _load_profile(db())
        return render_template('settings.html', profile=profile,
                               saved=request.args.get('saved') == '1')

    @app.route('/settings', methods=['POST'])
    @admin_required
    def settings_save():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        days = [int(d) for d in request.form.getlist('days')]
        opening = {'days': days,
                   'start': request.form.get('open_start', ''),
                   'end': request.form.get('open_end', '')} if days else {}
        result = organization.update(
            db(), name=request.form.get('name'), zone=request.form.get('zone'),
            currency=request.form.get('currency'), opening=opening or None)
        if not result['ok']:
            profile = _load_profile(db())
            return render_template('settings.html', profile=profile,
                                   error=result['message']), 400
        return redirect(url_for('settings', saved=1))

    @app.route('/settings/password', methods=['POST'])
    @login_required
    def settings_password():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        result = identity.change_password(
            db(), user_id=g.user['id'],
            current_password=request.form.get('current'),
            new_password=request.form.get('new'))
        if not result['ok']:
            profile = _load_profile(db())
            return render_template('settings.html', profile=profile,
                                   error=result['message']), 400
        response = make_response(redirect(url_for('login')))
        response.delete_cookie(SESSION_COOKIE)
        return response

    # ------------------------------------------------------------------ usuarios
    @app.route('/users')
    @admin_required
    def users_page():
        users = identity.list_users(db())
        return render_template('users.html', users=users,
                               saved=request.args.get('saved') == '1')

    @app.route('/users', methods=['POST'])
    @admin_required
    def users_create():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        result = identity.create_user(
            db(), username=request.form.get('username'),
            password=request.form.get('password'),
            full_name=request.form.get('full_name'),
            role=request.form.get('role', 'user'))
        if not result['ok']:
            return render_template('users.html', users=identity.list_users(db()),
                                   error=result['message']), 400
        return redirect(url_for('users_page', saved=1))

    @app.route('/users/<int:user_id>/role', methods=['POST'])
    @admin_required
    def users_role(user_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        result = identity.set_user_role(db(), user_id=user_id,
                                        role=request.form.get('role'))
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('users_page', saved=1))

    @app.route('/users/<int:user_id>/active', methods=['POST'])
    @admin_required
    def users_active(user_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        active = request.form.get('active') == '1'
        result = identity.set_user_active(db(), user_id=user_id, active=active)
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('users_page', saved=1))

    # ------------------------------------------------- búsqueda de contactos
    @app.route('/api/contacts/search')
    @login_required
    def api_contacts_search():
        denied = None if g.scope.can_any('clients.view') else require('clients.view')
        if denied:
            return denied
        q = (request.args.get('q') or '').strip()
        if not q:
            return jsonify(ok=True, items=[])
        result = contacts_module.list_contacts(db(), q=q, limit=10)
        return jsonify(ok=True,
                       items=[{'id': c['id'], 'name': c['full_name'],
                               'phone': c.get('phone')}
                              for c in result['items']])

    # ------------------------------------------------------- sedes y ámbitos
    @app.route('/branches')
    @login_required
    def branches_page():
        denied = require('branches.manage')
        if denied:
            return denied
        return render_template('branches.html',
                               branches=scope_service.list_branches(
                                   db(), include_inactive=True),
                               assignments=scope_service.list_assignments(db()),
                               users=identity.list_users(db()),
                               roles=scope_service.SCOPE_ROLES,
                               saved=request.args.get('saved') == '1')

    @app.route('/branches', methods=['POST'])
    @login_required
    def branches_create():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        denied = require('branches.manage')
        if denied:
            return denied
        result = scope_service.create_branch(
            db(), name=request.form.get('name'),
            timezone=request.form.get('zone'))
        if not result['ok']:
            return render_template('branches.html',
                                   branches=scope_service.list_branches(
                                       db(), include_inactive=True),
                                   assignments=scope_service.list_assignments(db()),
                                   users=identity.list_users(db()),
                                   roles=scope_service.SCOPE_ROLES,
                                   error=result['message']), 400
        return redirect(url_for('branches_page', saved=1))

    @app.route('/branches/assign', methods=['POST'])
    @login_required
    def branches_assign():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        denied = require('branches.manage')
        if denied:
            return denied
        branch_raw = request.form.get('branch_id')
        result = scope_service.assign_scope(
            db(), user_id=int(request.form.get('user_id')),
            scope_role=request.form.get('scope_role'),
            branch_id=int(branch_raw) if branch_raw else None)
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('branches_page', saved=1))

    @app.route('/branches/revoke', methods=['POST'])
    @login_required
    def branches_revoke():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        denied = require('branches.manage')
        if denied:
            return denied
        branch_raw = request.form.get('branch_id')
        result = scope_service.revoke_scope(
            db(), user_id=int(request.form.get('user_id')),
            scope_role=request.form.get('scope_role'),
            branch_id=int(branch_raw) if branch_raw else None)
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('branches_page', saved=1))

    # ------------------------------------------------------------------ ventas
    @app.route('/sales')
    @login_required
    def sales_page():
        denied = None if g.scope.can_any('sales.view') else require('sales.view')
        if denied:
            return denied
        # E01-R/A2: sólo sedes autorizadas para sales.view (no cualquier
        # membresía): gerente A / almacén B no ve ventas de B.
        branches = branches_for('sales.view')
        sales = commerce.list_sales(db(), limit=50, branch_ids=branches)
        for sale in sales:
            sale['can_reverse'] = g.scope.can('sales.reverse', sale['branch_id'])
        products = commerce.list_products(db(), branch_ids=branches)
        branch_objs = [b for b in scope_service.list_branches(db())
                       if branches is None or b['id'] in branches]
        return render_template('sales.html', sales=sales, products=products,
                               branches=branches, branch_objs=branch_objs,
                               is_director=g.scope.is_director)

    @app.route('/api/sales', methods=['POST'])
    @login_required
    def api_create_sale():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        data = request.get_json(silent=True) or {}
        branch_id = data.get('branch_id')
        if branch_id is not None:
            try:
                branch_id = int(branch_id)
            except (TypeError, ValueError):
                return jsonify(ok=False, code='invalid_branch',
                               message='Sede no válida'), 400
        else:
            sellable = branches_for('sales.create')
            branch_id = sellable[0] if sellable and len(sellable) == 1 else None
        if not g.scope.allowed(branch_id):
            return jsonify(ok=False, code='forbidden',
                           message='Sede fuera de su ámbito'), 403
        denied = require('sales.create', branch_id)
        if denied:
            return denied
        result = commerce.create_sale(
            db(), lines=data.get('lines') or [],
            payment_method=data.get('payment_method') or 'efectivo',
            contact_id=data.get('contact_id'), actor=g.user['id'],
            note=data.get('note'), branch_id=branch_id)
        if not result['ok']:
            return _api_error(result)
        return jsonify(result), 201

    @app.route('/api/sales/<int:sale_id>/reverse', methods=['POST'])
    @login_required
    def api_reverse_sale(sale_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        # E01-R/A1/A2: identidad mínima de la venta y guardia por sede.
        branch = _sale_branch(sale_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Venta no encontrada'), 404
        denied = require('sales.reverse', branch)
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        result = commerce.reverse_sale(
            db(), sale_id=sale_id, reason=data.get('reason'),
            actor=g.user['id'],
            role=_matrix_role('sales.reverse', branch))
        if not result['ok']:
            return _api_error(result)
        return jsonify(result)

    # ---------------------------------------------------------------- inventario
    @app.route('/inventory')
    @login_required
    def inventory_page():
        denied = None if g.scope.can_any('inventory.view') else require('inventory.view')
        if denied:
            return denied
        # E01-R/A2/A4: sedes de inventory.view; capacidades por producto
        # según la matriz en LA SEDE del producto (no rol de cuenta global).
        branches = branches_for('inventory.view')
        products = commerce.list_products(db(), include_inactive=True,
                                          branch_ids=branches)
        for product in products:
            product['can_price'] = g.scope.can('inventory.price',
                                               product['branch_id'])
            product['can_manage'] = g.scope.can('inventory.manage',
                                                product['branch_id'])
        return render_template('inventory.html', products=products,
                               saved=request.args.get('saved') == '1',
                               is_admin=g.scope.is_director,
                               can_manage=g.scope.is_director or any(
                                   p['can_manage'] for p in products),
                               branches=branches,
                               branch_objs=[b for b in
                                            scope_service.list_branches(db())
                                            if branches is None
                                            or b['id'] in branches])

    @app.route('/inventory/products', methods=['POST'])
    @login_required
    def inventory_create():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        branch_raw = request.form.get('branch_id')
        try:
            branch_id = int(branch_raw) if branch_raw else None
        except (TypeError, ValueError):
            return jsonify(ok=False, code='invalid_branch',
                           message='Sede no válida'), 400
        if branch_id is None:
            manageable = branches_for('inventory.manage')
            branch_id = manageable[0] if manageable and len(manageable) == 1 else 1
        # E01-R/A4: alta de producto en una sede concreta del ámbito.
        denied = require('inventory.manage', branch_id)
        if denied:
            return denied
        result = commerce.create_product(
            db(), sku=request.form.get('sku'), name=request.form.get('name'),
            kind=request.form.get('kind', 'servicio'),
            category=request.form.get('category'),
            price=request.form.get('price'), cost=request.form.get('cost'),
            stock=request.form.get('stock', 0),
            min_stock=request.form.get('min_stock', 0), actor=g.user['id'],
            branch_id=branch_id)
        if not result['ok']:
            products = commerce.list_products(
                db(), include_inactive=True, branch_ids=branches_for(
                    'inventory.view'))
            return render_template('inventory.html', products=products,
                                   error=result['message']), 400
        return redirect(url_for('inventory_page', saved=1))

    @app.route('/inventory/products/<int:product_id>/price', methods=['POST'])
    @login_required
    def inventory_price(product_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        branch = _product_branch(product_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Producto no encontrado'), 404
        # E01-R/A4: precio es acción de director en la sede del producto.
        denied = require('inventory.price', branch)
        if denied:
            return denied
        result = commerce.change_price(
            db(), product_id=product_id, new_price=request.form.get('price'),
            reason=request.form.get('reason'), actor=g.user['id'],
            role=_matrix_role('inventory.price', branch))
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('inventory_page', saved=1))

    @app.route('/inventory/products/<int:product_id>/stock', methods=['POST'])
    @login_required
    def inventory_stock(product_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        branch = _product_branch(product_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Producto no encontrado'), 404
        # E01-R/A4: el almacén ajusta cantidad sólo de SU sede (el producto
        # de otra sede no pasa la guardia); precio/costo no se tocan aquí.
        denied = require('inventory.manage', branch)
        if denied:
            return denied
        result = commerce.adjust_stock(
            db(), product_id=product_id, delta=request.form.get('delta'),
            note=request.form.get('note'), actor=g.user['id'],
            role=_matrix_role('inventory.manage', branch))
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('inventory_page', saved=1))

    @app.route('/inventory/products/<int:product_id>/toggle', methods=['POST'])
    @login_required
    def inventory_toggle(product_id):
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        branch = _product_branch(product_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Producto no encontrado'), 404
        denied = require('inventory.manage', branch)
        if denied:
            return denied
        products = commerce.list_products(
            db(), include_inactive=True, branch_ids=branches_for('inventory.view'))
        current = next((p for p in products if p['id'] == product_id), None)
        if not current:
            return _api_error({'code': 'not_found', 'message': 'Producto no encontrado'})
        result = commerce.update_product(
            db(), product_id=product_id, is_active=not current['is_active'])
        if not result['ok']:
            return _api_error(result)
        return redirect(url_for('inventory_page', saved=1))

    @app.route('/inventory/products/<int:product_id>/history')
    @login_required
    def inventory_history(product_id):
        # E01-R/A2: endpoint JSON (lo consume inventory.js); la denegación
        # es 403 JSON consistente, no redirect de formulario.
        branch = _product_branch(product_id)
        if branch == 'missing':
            return jsonify(ok=False, code='not_found',
                           message='Producto no encontrado'), 404
        if not g.scope.can('inventory.view', branch):
            return jsonify(ok=False, code='forbidden',
                           message='Sin permiso para el historial de este '
                                   'producto en su sede'), 403
        return jsonify(ok=True,
                       prices=commerce.price_history(db(), product_id),
                       stock=commerce.stock_history(db(), product_id))

    # ---------------------------------------------------------------- analítica
    @app.route('/analytics')
    @login_required
    def analytics_page():
        denied = None if g.scope.can_any('analytics.view') else require('analytics.view')
        if denied:
            return denied
        profile = _load_profile(db())
        include_demo = request.args.get('demo') == '1'
        data = analytics.overview(db(), profile['zone'],
                                  days=int(request.args.get('days', 30) or 30),
                                  include_demo=include_demo,
                                  branch_ids=branches_for('analytics.view'))
        return render_template('analytics.html', data=data,
                               currency=profile['currency'],
                               rebuilt=request.args.get('rebuilt') == '1')

    @app.route('/api/analytics/overview')
    @login_required
    def api_analytics_overview():
        # E01-R/A2: guardia explícita y ámbito por acción en la API BI
        # (antes devolvía el agregado global a cualquier usuario autenticado).
        denied = None if g.scope.can_any('analytics.view') else require('analytics.view')
        if denied:
            return denied
        profile = _load_profile(db())
        days = int(request.args.get('days', 30) or 30)
        days = max(7, min(days, 90))
        return jsonify(ok=True,
                       data=analytics.overview(db(), profile['zone'], days=days,
                                               branch_ids=branches_for(
                                                   'analytics.view')))

    @app.route('/analytics/rebuild', methods=['POST'])
    @admin_required
    def analytics_rebuild():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        profile = _load_profile(db())
        analytics.rebuild_bi(db(), profile['zone'])
        return redirect(url_for('analytics_page', rebuilt=1))

    # ---------------------------------------------------------------- asistente
    @app.route('/assistant')
    @login_required
    def assistant_page():
        # CORR01/R04: cada usuario ve su propio historial por defecto; la
        # vista global (?scope=global) es explícita y exclusiva de admin.
        scope_global = (request.args.get('scope') == 'global'
                        and g.user['role'] == 'admin')
        history_user = None if scope_global else g.user['id']
        return render_template('assistant.html',
                               recent=assistant.history(db(), user_id=history_user,
                                                        limit=10),
                               scope_global=scope_global,
                               is_admin=g.user['role'] == 'admin')

    @app.route('/assistant/ask', methods=['POST'])
    @login_required
    def assistant_ask():
        if not _csrf_ok():
            return jsonify(ok=False, code='csrf', message='Token CSRF no válido'), 403
        denied = None if g.scope.can_any('assistant.ask') else require('assistant.ask')
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        profile = _load_profile(db())
        include_demo = data.get('include_demo') is True and \
            g.user['role'] == 'admin'
        # E01-R/A2: cada herramienta consulta con el ámbito de SU acción;
        # nunca con el filtro genérico de membresías.
        result = assistant.ask(db(), question=data.get('question'),
                               user_id=g.user['id'], zone=profile['zone'],
                               include_demo=include_demo,
                               branches={
                                   'sales': branches_for('sales.view'),
                                   'agenda': branches_for('agenda.view'),
                                   'inventory': branches_for('inventory.view'),
                               })
        if not result['ok']:
            return _api_error({**result, 'code': result.get('code', 'invalid')})
        return jsonify(result)

    return app
