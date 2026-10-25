"""Flujo web completo: panel, agenda API, contactos y ajustes."""
from crm_premium.modules.organization import service as organization


def test_dashboard_renderiza_kpis(client):
    page = client.get('/')
    html = page.data.decode('utf-8')
    assert 'Citas de hoy' in html
    assert 'csrf-token' in html


def test_flago_agenda_crear_cita(client, resource, contact):
    listing = client.get('/api/agenda?view=day&date=2027-03-10')
    assert listing.status_code == 200
    assert listing.get_json()['ok']

    created = client.post('/api/appointments', json={
        'resource_id': resource['id'], 'contact_id': contact['id'],
        'title': 'Cita web', 'start': '2027-03-10T10:00',
        'end': '2027-03-10T11:00'}, headers={'X-CSRF-Token': client.csrf})
    assert created.status_code == 201, created.get_json()
    appt = created.get_json()['appointment']

    events = client.get('/api/agenda?view=day&date=2027-03-10').get_json()['events']
    assert any(e['id'] == appt['id'] for e in events)

    detail = client.get(f'/api/appointments/{appt["id"]}')
    assert detail.status_code == 200
    assert detail.get_json()['appointment']['start_local']['time'] == '10:00'

    transition = client.post(f'/api/appointments/{appt["id"]}/transition', json={
        'action': 'confirm', 'expected_version': appt['row_version']},
        headers={'X-CSRF-Token': client.csrf})
    assert transition.status_code == 200

    note = client.post(f'/api/appointments/{appt["id"]}/transition', json={
        'action': 'note', 'body': 'Cliente confirmó por teléfono'},
        headers={'X-CSRF-Token': client.csrf})
    assert note.status_code == 200


def test_solape_en_api_devuelve_409(client, resource):
    first = client.post('/api/appointments', json={
        'resource_id': resource['id'], 'title': 'A',
        'start': '2027-04-01T09:00', 'end': '2027-04-01T10:00'},
        headers={'X-CSRF-Token': client.csrf})
    assert first.status_code == 201
    second = client.post('/api/appointments', json={
        'resource_id': resource['id'], 'title': 'B',
        'start': '2027-04-01T09:30', 'end': '2027-04-01T10:30'},
        headers={'X-CSRF-Token': client.csrf})
    assert second.status_code == 409
    assert second.get_json()['code'] == 'overlap'


def test_contactos_ciclo_completo(client):
    page = client.get('/contacts')
    assert page.status_code == 200
    created = client.post('/contacts', data={
        'csrf_token': client.csrf, 'full_name': 'María Prueba Web',
        'phone': '+593987654321', 'email': 'maria@example.test'})
    assert created.status_code == 302
    listing = client.get('/contacts?q=maría')
    assert 'María Prueba Web' in listing.data.decode('utf-8')
    empty = client.post('/contacts', data={
        'csrf_token': client.csrf, 'full_name': '   '})
    assert empty.status_code == 400


def test_ajustes_actualizan_zona(client):
    response = client.post('/settings', data={
        'csrf_token': client.csrf, 'name': 'Clínica Modelo',
        'zone': 'America/Guayaquil', 'currency': 'USD',
        'days': ['0', '1', '2', '3', '4'],
        'open_start': '08:00', 'open_end': '17:00'})
    assert response.status_code == 302
    profile = organization.get(client.application.config['DATABASE_URL'])
    assert profile['name'] == 'Clínica Modelo'
    assert profile['zone'] == 'America/Guayaquil'
    bad_zone = client.post('/settings', data={
        'csrf_token': client.csrf, 'name': 'X', 'zone': 'Marte/Olympus',
        'currency': 'USD'})
    assert bad_zone.status_code == 400


def test_gestion_usuarios_por_admin(client):
    created = client.post('/users', data={
        'csrf_token': client.csrf, 'username': 'nuevo.asesor',
        'full_name': 'Asesor Nuevo', 'role': 'user',
        'password': 'ClaveAsesor.2026'})
    assert created.status_code == 302
    weak = client.post('/users', data={
        'csrf_token': client.csrf, 'username': 'debil',
        'full_name': 'X', 'role': 'user', 'password': 'corta'})
    assert weak.status_code == 400
    page = client.get('/users')
    assert 'nuevo.asesor' in page.data.decode('utf-8')


def test_comercio_web_completo(client):
    from crm_premium.modules.commerce import service as commerce
    url = client.application.config['DATABASE_URL']
    service = commerce.create_product(url, sku='SRV-WEB',
                                      name='Limpieza web', price='30.00')['product']
    product = commerce.create_product(url, sku='PRD-WEB', kind='producto',
                                      name='Pasta web', price='5.00',
                                      stock=10)['product']
    page = client.get('/inventory')
    assert page.status_code == 200 and 'PRD-WEB' in page.data.decode('utf-8')

    created = client.post('/api/sales', json={
        'lines': [{'product_id': service['id'], 'qty': 1},
                  {'product_id': product['id'], 'qty': 2}],
        'payment_method': 'tarjeta'}, headers={'X-CSRF-Token': client.csrf})
    assert created.status_code == 201, created.get_json()
    sale_id = created.get_json()['sale_id']

    listed = client.get('/sales')
    assert f'V{sale_id:06d}' in listed.data.decode('utf-8')

    no_csrf = client.post('/api/sales', json={'lines': []})
    assert no_csrf.status_code == 403


def test_analitica_web(client):
    from crm_premium.modules.analytics import service as analytics
    url = client.application.config['DATABASE_URL']
    analytics.rebuild_bi(url, 'UTC')
    page = client.get('/analytics')
    assert page.status_code == 200
    assert 'Ventas netas' in page.data.decode('utf-8')
    api = client.get('/api/analytics/overview?days=7')
    assert api.status_code == 200 and api.get_json()['ok']


def test_asistente_web(client):
    ask = client.post('/assistant/ask', json={'question': 'ventas de hoy'},
                      headers={'X-CSRF-Token': client.csrf})
    assert ask.status_code == 200
    body = ask.get_json()
    assert body['ok'] and body['tool'] == 'ventas'
    page = client.get('/assistant')
    assert page.status_code == 200
    assert 'Auditoría reciente' in page.data.decode('utf-8')
