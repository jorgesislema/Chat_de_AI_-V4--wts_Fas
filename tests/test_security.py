"""Seguridad web: CSRF, sesiones, roles, cabeceras y cookies."""
from crm_premium.entrypoints.web.app import create_app
from crm_premium.modules.identity import service as identity


def _plain_client(db_url, org, admin_user):
    app = create_app(db_url=db_url)
    app.config['testing'] = True
    return app.test_client()


def _login(client, username='admin_test', password='ClaveLarga.2026'):
    page = client.get('/login')
    token = page.data.decode('utf-8').split('name="csrf_token" value="')[1].split('"')[0]
    return client.post('/login', data={'username': username,
                                       'password': password,
                                       'csrf_token': token})


def test_rutas_protegidas_redirigen_a_login(db_url, org, admin_user):
    client = _plain_client(db_url, org, admin_user)
    for path in ('/', '/agenda', '/contacts', '/settings', '/users'):
        response = client.get(path)
        assert response.status_code == 302 and '/login' in response.location


def test_api_protegida_401(db_url, org, admin_user):
    client = _plain_client(db_url, org, admin_user)
    response = client.get('/api/agenda?view=day&date=2027-03-10')
    assert response.status_code == 401


def test_cabeceras_de_seguridad(client):
    response = client.get('/')
    assert "default-src 'self'" in response.headers['Content-Security-Policy']
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_cookie_de_sesion_httponly(db_url, org, admin_user):
    client = _plain_client(db_url, org, admin_user)
    response = _login(client)
    cookie_header = response.headers.get('Set-Cookie', '')
    assert 'crm_session=' in cookie_header
    assert 'HttpOnly' in cookie_header and 'SameSite=Lax' in cookie_header


def test_csrf_requerido_en_escrituras(client):
    response = client.post('/api/appointments', json={
        'resource_id': 1, 'title': 'X', 'start': '2027-03-10T10:00',
        'end': '2027-03-10T11:00'})
    assert response.status_code == 403
    assert response.get_json()['code'] == 'csrf'


def test_csrf_de_login_rechaza_forgery(db_url, org, admin_user):
    client = _plain_client(db_url, org, admin_user)
    client.get('/login')
    response = client.post('/login', data={
        'username': 'admin_test', 'password': 'ClaveLarga.2026',
        'csrf_token': 'valor-ajeno'})
    assert response.status_code == 400


def test_credenciales_invalidas_401(db_url, org, admin_user):
    client = _plain_client(db_url, org, admin_user)
    response = _login(client, password='Incorrecta.2026')
    assert response.status_code == 401


def test_usuario_no_admin_no_ve_usuarios(db_url, org, admin_user):
    identity.create_user(db_url, username='emilio', password='ClaveLarga.2026')
    client = _plain_client(db_url, org, admin_user)
    _login(client, username='emilio')
    assert client.get('/users').status_code == 302
    # E01-R/A3: sin asignación de ámbito el usuario NO recibe 'asesor'
    # automático al leer el perfil; la agenda le queda denegada (403).
    assert client.get('/api/agenda').status_code == 403


def test_logout_revoca(client):
    response = client.post('/logout', data={'csrf_token': client.csrf})
    assert response.status_code == 302
    page = client.get('/')
    assert page.status_code == 302 and '/login' in page.location


def test_open_redirect_bloqueado(db_url, org, admin_user):
    client = _plain_client(db_url, org, admin_user)
    page = client.get('/login')
    token = page.data.decode('utf-8').split('name="csrf_token" value="')[1].split('"')[0]
    response = client.post('/login?next=https://ajeno.example',
                           data={'username': 'admin_test',
                                 'password': 'ClaveLarga.2026',
                                 'csrf_token': token})
    # Un next externo nunca se usa: cae en el panel local.
    assert response.headers['Location'].endswith('/') \
        and 'ajeno.example' not in response.headers['Location']
