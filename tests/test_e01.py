"""E01: sedes, ámbitos, backfill, BI/IA por sede y buscador de contactos."""
import psycopg
from psycopg.rows import dict_row

from crm_premium.entrypoints.web.app import create_app
from crm_premium.modules.analytics import service as analytics
from crm_premium.modules.assistant import service as assistant
from crm_premium.modules.commerce import service as commerce
from crm_premium.modules.contacts import service as contacts
from crm_premium.modules.identity import service as identity
from crm_premium.modules.scope import service as scope
from crm_premium.modules.scheduling import service as scheduling

ZONE = 'UTC'


# ------------------------------------------------ backfill a sede Principal

def test_e01m_backfill_preserva_ids_y_etiqueta(db_url, org, admin_user,
                                               resource, contact):
    """E00B precisión 3: consolidación PostgreSQL → sede Principal sin
    pérdidas; no infiere pagos/estados (sólo etiqueta)."""
    sale = commerce.create_sale(db_url, lines=[
        {'product_id': commerce.create_product(
            db_url, sku='SRV-BF', name='Backfill', price='5.00')['product']['id'],
         'qty': 1}], actor=admin_user['id'], branch_id=1)
    result = scope.create_branch(db_url, name='Principal', timezone=ZONE)
    assert result['ok'] and result['branch']['id'] == 1
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for table in ('resources', 'appointments', 'products', 'sales',
                          'stock_movements'):
                cur.execute(f'SELECT count(*) AS n FROM {table} '
                            'WHERE branch_id IS NULL')
                assert cur.fetchone()['n'] == 0, table
            cur.execute('SELECT id, branch_id FROM sales WHERE id=%s',
                        (sale['sale_id'],))
            row = cur.fetchone()
            assert row['branch_id'] == 1 and row['id'] == sale['sale_id']


# ------------------------------------------------------- ámbito y matriz

def _make_two_branches(db_url, admin_user):
    import secrets as _secrets
    tag = _secrets.token_hex(3)
    b1 = scope.create_branch(db_url, name=f'Sede Norte {tag}',
                             timezone=ZONE)['branch']
    b2 = scope.create_branch(db_url, name=f'Sede Sur {tag}',
                             timezone=ZONE)['branch']
    gerente = identity.create_user(db_url, username=f'gerente_{tag}',
                                   password='ClaveLarga.2026')
    assert gerente['ok'], gerente
    scope.assign_scope(db_url, user_id=gerente['user']['id'],
                       scope_role='gerente', branch_id=b1['id'])
    return b1, b2, gerente['user']


def test_e01_denegacion_por_defecto_sin_asignacion(db_url, org):
    outsider = identity.create_user(db_url, username='sin_ambito',
                                    password='ClaveLarga.2026')
    assert outsider['ok'], outsider
    ctx = scope.load_scope(db_url, outsider['user']['id'])
    assert not ctx.authenticated
    assert ctx.can('sales.view') is False
    assert ctx.branch_filter() == []


def test_e01_gerente_ve_solo_su_sede(db_url, org, admin_user, contact):
    b1, b2, gerente = _make_two_branches(db_url, admin_user)
    r1 = scheduling.create_resource(db_url, name='Profesional Norte')['resource']
    r2 = scheduling.create_resource(db_url, name='Profesional Sur')['resource']
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE resources SET branch_id=%s WHERE id=%s',
                        (b1['id'], r1['id']))
            cur.execute('UPDATE resources SET branch_id=%s WHERE id=%s',
                        (b2['id'], r2['id']))
    ok = scheduling.save_appointment(
        db_url, resource_id=r1['id'], start='2027-09-01T10:00',
        end='2027-09-01T11:00', title='Cita norte', zone=ZONE,
        contact_id=contact['id'])
    assert ok['ok'], ok
    events_norte = scheduling.list_appointments(
        db_url, start_utc='2027-09-01T00:00:00+00:00',
        end_utc='2027-09-02T00:00:00+00:00', branch_ids=[b1['id']])
    events_sur = scheduling.list_appointments(
        db_url, start_utc='2027-09-01T00:00:00+00:00',
        end_utc='2027-09-02T00:00:00+00:00', branch_ids=[b2['id']])
    assert [e['title'] for e in events_norte] == ['Cita norte']
    assert events_sur == []


def test_e01_matriz_web_negativa(db_url, org, admin_user, plain_user, contact):
    """Casos negativos de permisos por acción (denegación por defecto)."""
    b1, b2, gerente = _make_two_branches(db_url, admin_user)
    scope.assign_scope(db_url, user_id=plain_user['id'], scope_role='asesor',
                       branch_id=b1['id'])
    almacen = identity.create_user(db_url, username='almacen_u',
                                   password='ClaveLarga.2026')
    assert almacen['ok'], almacen
    scope.assign_scope(db_url, user_id=almacen['user']['id'],
                       scope_role='almacen', branch_id=b1['id'])

    r1 = scheduling.create_resource(db_url, name='Profesional Norte')['resource']
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE resources SET branch_id=%s WHERE id=%s',
                        (b1['id'], r1['id']))
    ok_norte = scheduling.save_appointment(
        db_url, resource_id=r1['id'], start='2027-09-01T10:00',
        end='2027-09-01T11:00', title='Cita norte', zone=ZONE,
        contact_id=contact['id'])
    assert ok_norte['ok'], ok_norte

    app = create_app(db_url=db_url)
    app.config['testing'] = True

    def client_as(username):
        c = app.test_client()
        page = c.get('/login')
        token = page.data.decode('utf-8').split(
            'name="csrf_token" value="')[1].split('"')[0]
        r = c.post('/login', data={'username': username,
                                   'password': 'ClaveLarga.2026',
                                   'csrf_token': token})
        assert r.status_code == 302, (username, r.status_code, r.data[:300])
        html = c.get('/').data.decode('utf-8')
        c.csrf = html.split('name="csrf-token" content="')[1].split('"')[0]
        return c

    asesor = client_as(plain_user['username'])
    # Asesor SÍ registra venta en su sede.
    product = commerce.create_product(db_url, sku='SRV-VNEG', name='V neg',
                                      price='10.00')['product']
    ok = asesor.post('/api/sales', json={
        'lines': [{'product_id': product['id'], 'qty': 1}]},
        headers={'X-CSRF-Token': asesor.csrf})
    assert ok.status_code == 201, ok.get_json()
    # Asesor NO cambia precio ni gestiona stock (matriz).
    resp = asesor.post('/inventory/products/%s/price' % product['id'],
                       data={'csrf_token': asesor.csrf, 'price': '99',
                             'reason': 'x'})
    assert resp.status_code in (302, 403)
    assert asesor.get('/branches').status_code == 302

    almacen_c = client_as('almacen_u')
    assert almacen_c.get('/sales').status_code == 302      # matriz: sin ventas
    assert almacen_c.get('/inventory').status_code == 200  # matriz: sí stock

    gerente_c = client_as(gerente['username'])
    listing = gerente_c.get('/api/agenda?view=day&date=2027-09-01')
    assert listing.status_code == 200
    events = listing.get_json()['events']
    titles = [e['title'] for e in events]
    assert 'Cita norte' in titles      # su sede
    assert all(e['resource_name'] != 'Profesional Sur' for e in events)


def test_e01_revocar_ambito_revoqa_sesiones(db_url, org, plain_user):
    auth = identity.authenticate(db_url, username=plain_user['username'],
                                 password='ClaveLarga.2026')
    assert auth['ok']
    scope.assign_scope(db_url, user_id=plain_user['id'], scope_role='asesor',
                       branch_id=1)
    scope.revoke_scope(db_url, user_id=plain_user['id'], scope_role='asesor',
                       branch_id=1)
    user, _ = identity.user_for_session(db_url, token=auth['token'])
    assert user is None, 'quitar ámbito debe revocar sesiones'


# ----------------------------------------------------------- BI por sede

def test_e01_bi_por_sede(db_url, org, admin_user):
    b1 = scope.create_branch(db_url, name='Sede BI 1', timezone=ZONE)['branch']
    b2 = scope.create_branch(db_url, name='Sede BI 2', timezone=ZONE)['branch']
    p1 = commerce.create_product(db_url, sku='SRV-B1', name='Servicio B1',
                                 price='100.00')['product']
    p2 = commerce.create_product(db_url, sku='SRV-B2', name='Servicio B2',
                                 price='50.00')['product']
    commerce.create_sale(db_url, lines=[{'product_id': p1['id'], 'qty': 1}],
                         actor=admin_user['id'], branch_id=b1['id'])
    commerce.create_sale(db_url, lines=[{'product_id': p2['id'], 'qty': 1}],
                         actor=admin_user['id'], branch_id=b2['id'])
    analytics.rebuild_bi(db_url, ZONE)
    all_data = analytics.overview(db_url, ZONE, days=3650)
    assert abs(all_data['kpis']['ventas_netas'] - 150.0) < 0.01
    north = analytics.overview(db_url, ZONE, days=3650, branch_ids=[b1['id']])
    assert abs(north['kpis']['ventas_netas'] - 100.0) < 0.01
    south = analytics.overview(db_url, ZONE, days=3650, branch_ids=[b2['id']])
    assert abs(south['kpis']['ventas_netas'] - 50.0) < 0.01
    none_scope = analytics.overview(db_url, ZONE, days=3650, branch_ids=[])
    assert none_scope['kpis']['ventas_netas'] == 0


# ------------------------------------------------- asistente por ámbito

def test_e01_asistente_respeta_sede(db_url, org, admin_user, plain_user):
    b1 = scope.create_branch(db_url, name='Sede IA 1', timezone=ZONE)['branch']
    b2 = scope.create_branch(db_url, name='Sede IA 2', timezone=ZONE)['branch']
    p1 = commerce.create_product(db_url, sku='SRV-IA1', name='Servicio IA1',
                                 price='40.00')['product']
    commerce.create_sale(db_url, lines=[{'product_id': p1['id'], 'qty': 1}],
                         actor=admin_user['id'], branch_id=b1['id'],
                         payment_method='efectivo')
    # E01-R/A2: ask() recibe el mapa de ámbitos por acción; ventas usa el
    # de sales.view.
    result = assistant.ask(db_url, question='ventas de hoy MARCA-E01',
                           user_id=plain_user['id'], zone=ZONE,
                           branches={'sales': [b2['id']], 'agenda': [b2['id']],
                                     'inventory': [b2['id']]})
    assert abs(result['data']['neto']) < 0.01  # su sede no tiene ventas
    result_all = assistant.ask(db_url, question='ventas de hoy MARCA-E01B',
                               user_id=admin_user['id'], zone=ZONE,
                               branches={'sales': None, 'agenda': None,
                                         'inventory': None})
    assert abs(result_all['data']['neto'] - 40.0) < 0.01
    result_none = assistant.ask(db_url, question='ventas de hoy',
                                user_id=plain_user['id'], zone=ZONE,
                                branches={'sales': [], 'agenda': [],
                                          'inventory': []})
    assert result_none['data']['neto'] == 0


# ------------------------------------------- buscador de contactos (sin IDs)

def test_e01_buscador_contactos(db_url, org, admin_user, client):
    contacts.create(db_url, full_name='Zoila Prueba Búsqueda',
                    phone='+593991112223')
    resp = client.get('/api/contacts/search?q=zoila')
    items = resp.get_json()['items']
    assert len(items) == 1 and items[0]['name'] == 'Zoila Prueba Búsqueda'
    assert items[0]['id'] > 0
    empty = client.get('/api/contacts/search?q=')
    assert empty.get_json()['items'] == []


# ------------------------------------- servicio tipado y citas multidiarias

def test_e01_service_tipado_validado(db_url, org, admin_user, resource):
    product = commerce.create_product(db_url, sku='SRV-TIPO',
                                      name='Limpieza tipada',
                                      price='20.00')['product']
    good = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start='2027-10-01T09:00',
        end='2027-10-01T10:00', title='Con servicio', zone=ZONE,
        service_id=product['id'])
    assert good['ok']
    detail = scheduling.appointment_detail(
        db_url, appointment_id=good['appointment']['id'])
    assert detail['appointment']['service_id'] == product['id']
    bad = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start='2027-10-02T09:00',
        end='2027-10-02T10:00', title='Con producto', zone=ZONE,
        service_id=999999)
    assert not bad['ok'] and bad['code'] == 'invalid_title'


def test_e01_cita_multidiaria_atraviesa_dias(db_url, org, resource):
    created = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start='2027-10-05T23:00',
        end='2027-10-06T01:00', title='Cruza medianoche', zone=ZONE)
    assert created['ok']
    day1 = scheduling.list_appointments(
        db_url, start_utc='2027-10-05T00:00:00+00:00',
        end_utc='2027-10-06T00:00:00+00:00')
    day2 = scheduling.list_appointments(
        db_url, start_utc='2027-10-06T00:00:00+00:00',
        end_utc='2027-10-07T00:00:00+00:00')
    assert [e['title'] for e in day1] == ['Cruza medianoche']
    assert [e['title'] for e in day2] == ['Cruza medianoche']
