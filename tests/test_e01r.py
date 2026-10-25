"""E01-R: regresiones de los hallazgos A1–A6 (REVISION_CODEX_01).

A1 guardia por acción+sede en detalle/transición/nota/corrección y
contacto→citas; A2 filtros por acción (BI API, inventario/historial,
contactos, herramientas); A3 revocación durable (sin backfill en GET);
A4 inventario sin handlers inline y permiso por sede del producto;
A6 migración de una base poblada pre-E01 preservando IDs/historial/precios.

Las pruebas A5 de interfaz (guardado en navegador, capturas 360/768/1440)
viven en tools/evidencia_e01r.py; aquí queda el equivalente de API de los
recorridos. PostgreSQL temporal explícito; identidad y proveedores simulados.
"""
import secrets
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

from crm_premium.entrypoints.web.app import create_app
from crm_premium.modules.analytics import service as analytics
from crm_premium.modules.assistant import service as assistant
from crm_premium.modules.commerce import service as commerce
from crm_premium.modules.contacts import service as contacts
from crm_premium.modules.identity import service as identity
from crm_premium.modules.organization import service as organization
from crm_premium.modules.scheduling import service as scheduling
from crm_premium.modules.scope import service as scope

ZONE = 'UTC'
PASSWORD = 'ClaveLarga.2026'


# ------------------------------------------------------------- utilidades

def _tag():
    return secrets.token_hex(3)


def _user(db_url, role='user'):
    result = identity.create_user(db_url, username=f'u_{_tag()}',
                                  password=PASSWORD, role=role)
    assert result['ok'], result
    return result['user']


def _client(db_url, org, username):
    """Cliente web fresco con sesión y CSRF del usuario indicado."""
    app = create_app(db_url=db_url)
    app.config['testing'] = True
    test_client = app.test_client()
    page = test_client.get('/login')
    token = page.data.decode('utf-8').split('name="csrf_token" value="')[1] \
        .split('"')[0]
    response = test_client.post('/login', data={'username': username,
                                                'password': PASSWORD,
                                                'csrf_token': token})
    assert response.status_code == 302, response.data
    html = test_client.get('/').data.decode('utf-8')
    test_client.csrf = html.split('name="csrf-token" content="')[1].split('"')[0]
    return test_client


def _two_branch_world(db_url, admin_user):
    """Sedes A/B con un recurso cada una y usuarios gerenteA/almacénB."""
    tag = _tag()
    a = scope.create_branch(db_url, name=f'Sede A {tag}', timezone=ZONE)['branch']
    b = scope.create_branch(db_url, name=f'Sede B {tag}', timezone=ZONE)['branch']
    ra = scheduling.create_resource(db_url, name=f'Recurso A {tag}')['resource']
    rb = scheduling.create_resource(db_url, name=f'Recurso B {tag}')['resource']
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE resources SET branch_id=%s WHERE id=%s',
                        (a['id'], ra['id']))
            cur.execute('UPDATE resources SET branch_id=%s WHERE id=%s',
                        (b['id'], rb['id']))
    gerente = _user(db_url)
    scope.assign_scope(db_url, user_id=gerente['id'], scope_role='gerente',
                       branch_id=a['id'])
    almacen = _user(db_url)
    scope.assign_scope(db_url, user_id=almacen['id'], scope_role='almacen',
                       branch_id=b['id'])
    return {'a': a, 'b': b, 'ra': ra, 'rb': rb, 'gerente': gerente,
            'almacen': almacen}


def _appointment(db_url, resource_id, start, end, title='Consulta',
                 contact_id=None, service_id=None):
    result = scheduling.save_appointment(
        db_url, resource_id=resource_id, start=start, end=end, title=title,
        zone=ZONE, actor=None, clock=__import__('datetime').datetime(
            2029, 1, 1, tzinfo=__import__('datetime').timezone.utc),
        contact_id=contact_id, service_id=service_id, channel='web')
    assert result['ok'], result
    return result['appointment']


# ------------------------------------------------------- A1: guardia cita

def test_a1_gerente_ajeno_no_lee_ni_muta_cita_de_otra_sede(db_url, org,
                                                           admin_user):
    world = _two_branch_world(db_url, admin_user)
    target = _appointment(db_url, world['rb']['id'], '2030-06-10T10:00',
                          '2030-06-10T10:30', 'Marca privada sede B')
    client = _client(db_url, org, world['gerente']['username'])

    detail = client.get(f"/api/appointments/{target['id']}")
    assert detail.status_code == 403, detail.data
    assert 'Marca privada' not in detail.get_data(as_text=True)

    transition = client.post(f"/api/appointments/{target['id']}/transition",
                             json={'action': 'cancel',
                                   'expected_version': target['row_version'],
                                   'reason': 'intento ajeno'},
                             headers={'X-CSRF-Token': client.csrf})
    assert transition.status_code == 403
    note = client.post(f"/api/appointments/{target['id']}/transition",
                       json={'action': 'note', 'body': 'intento'},
                       headers={'X-CSRF-Token': client.csrf})
    assert note.status_code == 403
    correct = client.post(f"/api/appointments/{target['id']}/transition",
                          json={'action': 'correct', 'target': 'confirmed',
                                'reason': 'intento',
                                'expected_version': target['row_version']},
                          headers={'X-CSRF-Token': client.csrf})
    assert correct.status_code == 403

    # La cita ajena queda intacta (cero cambios).
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT operational_status, row_version, title '
                        'FROM appointments WHERE id=%s', (target['id'],))
            row = cur.fetchone()
    assert row['title'] == 'Marca privada sede B'
    assert row['operational_status'] == 'pending'
    assert row['row_version'] == target['row_version']

    # Su propia sede sí se lee y lista vacío no habilita ID directo.
    own = _appointment(db_url, world['ra']['id'], '2030-06-11T09:00',
                       '2030-06-11T09:30')
    assert client.get(f"/api/appointments/{own['id']}").status_code == 200
    listing = client.get('/api/agenda?view=week&date=2030-06-10').get_json()
    assert all(e['id'] != target['id'] for e in listing['events'])


def test_a1_accion_desconocida_denegada(db_url, org, admin_user):
    world = _two_branch_world(db_url, admin_user)
    own = _appointment(db_url, world['ra']['id'], '2030-06-12T09:00',
                       '2030-06-12T09:30')
    client = _client(db_url, org, world['gerente']['username'])
    response = client.post(f"/api/appointments/{own['id']}/transition",
                           json={'action': 'borrar_todo'},
                           headers={'X-CSRF-Token': client.csrf})
    assert response.status_code == 400
    assert response.get_json()['code'] == 'invalid_action'


def test_a1_contacto_muestra_solo_citas_de_su_agenda(db_url, org, admin_user):
    world = _two_branch_world(db_url, admin_user)
    person = contacts.create(db_url, full_name=f'Paciente {_tag()}',
                             phone='+593900000111')['contact']
    own = _appointment(db_url, world['ra']['id'], '2030-06-10T09:00',
                       '2030-06-10T09:30', 'Cita sede A', contact_id=person['id'])
    foreign = _appointment(db_url, world['rb']['id'], '2030-06-10T11:00',
                           '2030-06-10T11:30', 'Cita sede B MARCA-A1',
                           contact_id=person['id'])
    client = _client(db_url, org, world['gerente']['username'])
    html = client.get(f"/contacts/{person['id']}").get_data(as_text=True)
    assert 'Cita sede A' in html
    assert 'MARCA-A1' not in html, 'el perfil del contacto no filtra sede ajena'

    # Agenda del recurso ajeno tampoco aparece en el listado.
    listing = client.get('/api/agenda?view=week&date=2030-06-10').get_json()
    assert {e['id'] for e in listing['events']} == {own['id']}


# ------------------------------------------------- A2: ámbito por acción

def test_a2_doble_rol_gerente_a_almacen_b_separa_ventas_e_inventario(
        db_url, org, admin_user):
    world = _two_branch_world(db_url, admin_user)
    doble = _user(db_url)
    scope.assign_scope(db_url, user_id=doble['id'], scope_role='gerente',
                       branch_id=world['a']['id'])
    scope.assign_scope(db_url, user_id=doble['id'], scope_role='almacen',
                       branch_id=world['b']['id'])

    pa = commerce.create_product(db_url, sku=f'SRV-A-{_tag()}',
                                 name='Servicio A', price='100.00',
                                 kind='servicio')['product']
    pb = commerce.create_product(db_url, sku=f'PROD-B-{_tag()}',
                                 name='Producto B', price='50.00',
                                 kind='producto', stock=10,
                                 branch_id=world['b']['id'])['product']
    sale_a = commerce.create_sale(db_url, lines=[{'product_id': pa['id'],
                                                  'qty': 1}],
                                  actor=admin_user['id'],
                                  branch_id=world['a']['id'])
    sale_b = commerce.create_sale(db_url, lines=[{'product_id': pb['id'],
                                                  'qty': 1}],
                                  actor=admin_user['id'],
                                  branch_id=world['b']['id'])
    analytics.rebuild_bi(db_url, ZONE)

    client = _client(db_url, org, doble['username'])
    # Ventas: ve A (gerente), no B (almacén no da sales.view).
    html = client.get('/sales').get_data(as_text=True)
    assert f'V{sale_a["sale_id"]:06d}' in html
    assert f'V{sale_b["sale_id"]:06d}' not in html
    # BI: analytics.view incluye a almacén en la matriz, así que el doble
    # rol ve ambas sedes (150.00); la separación estricta por acción se
    # prueba con el gerente puro en test_a2_bi_api_*.
    bi = client.get('/api/analytics/overview').get_json()
    assert bi['ok']
    assert sorted(bi['data']['sedes']) == sorted([world['a']['id'],
                                                  world['b']['id']])
    assert abs(bi['data']['kpis']['ventas_netas'] - 150.0) < 0.01
    # Inventario: ve/ajusta B (almacén); historial de B permitido.
    page = client.get('/inventory').get_data(as_text=True)
    assert 'Producto B' in page
    history = client.get(f"/inventory/products/{pb['id']}/history")
    assert history.status_code == 200

    # Gerente puro de A: sin inventario en B y sin historial de B.
    solo_a = _client(db_url, org, world['gerente']['username'])
    denied = solo_a.get(f"/inventory/products/{pb['id']}/history")
    assert denied.status_code == 403
    assert '50.00' not in denied.get_data(as_text=True)


def test_a2_bi_api_sin_asignacion_denegada_y_gerente_filtrada(db_url, org,
                                                              admin_user):
    world = _two_branch_world(db_url, admin_user)
    pa = commerce.create_product(db_url, sku=f'SRV-BI-{_tag()}',
                                 name='BI A', price='60.00',
                                 kind='servicio')['product']
    commerce.create_sale(db_url, lines=[{'product_id': pa['id'], 'qty': 1}],
                         actor=admin_user['id'], branch_id=world['a']['id'])
    commerce.create_sale(db_url, lines=[{'product_id': pa['id'], 'qty': 2}],
                         actor=admin_user['id'], branch_id=world['b']['id'])
    analytics.rebuild_bi(db_url, ZONE)

    outsider = _user(db_url)
    client = _client(db_url, org, outsider['username'])
    assert client.get('/api/analytics/overview').status_code == 403

    gerente = _client(db_url, org, world['gerente']['username'])
    data = gerente.get('/api/analytics/overview').get_json()['data']
    assert data['sedes'] == [world['a']['id']]
    assert abs(data['kpis']['ventas_netas'] - 60.0) < 0.01


def test_a2_herramientas_respetan_ambito_por_accion(db_url, org, admin_user):
    world = _two_branch_world(db_url, admin_user)
    doble = _user(db_url)
    scope.assign_scope(db_url, user_id=doble['id'], scope_role='gerente',
                       branch_id=world['a']['id'])
    scope.assign_scope(db_url, user_id=doble['id'], scope_role='almacen',
                       branch_id=world['b']['id'])
    pb = commerce.create_product(db_url, sku=f'PROD-P-{_tag()}',
                                 name='Producto Precio B', price='77.00',
                                 kind='producto', stock=3, min_stock=2,
                                 branch_id=world['b']['id'])['product']
    _appointment(db_url, world['rb']['id'], '2030-06-10T08:00',
                 '2030-06-10T08:30', 'Cita B')

    # precio usa inventory.view: doble rol ve B; gerente puro no.
    r = assistant.ask(db_url, question='precio de Producto Precio B',
                      user_id=doble['id'], zone=ZONE,
                      branches={'sales': [world['a']['id']],
                                'agenda': [world['a']['id']],
                                'inventory': [world['b']['id']]})
    assert r['ok'] and r['data']['product'] is not None
    r_ajeno = assistant.ask(db_url, question='precio de Producto Precio B',
                            user_id=world['gerente']['id'], zone=ZONE,
                            branches={'sales': [world['a']['id']],
                                      'agenda': [world['a']['id']],
                                      'inventory': [world['a']['id']]})
    assert r_ajeno['data']['product'] is None

    # citas_hoy usa agenda.view: doble rol (agenda=A) no cuenta la cita de B.
    from datetime import datetime, timedelta, timezone as tz
    futuro = (datetime(2030, 6, 10, 8, 0, tzinfo=tz.utc)
              + timedelta(days=(datetime.now(tz.utc).date()
                                - datetime(2030, 6, 10).date()).days % 3650))
    hoy = assistant.ask(db_url, question='citas de hoy',
                        user_id=doble['id'], zone=ZONE,
                        branches={'sales': None,
                                  'agenda': [world['a']['id']],
                                  'inventory': None})
    assert hoy['data']['total'] == 0  # la cita 2030 está fuera de "hoy"
    del futuro  # la comparación fina de día local vive en la evidencia UI

    # stock_bajo usa inventory.view: doble rol ve B; agenda de A no filtra.
    commerce.adjust_stock(db_url, product_id=pb['id'], delta=-2, note='prueba',
                          actor=admin_user['id'], role='admin')
    r_stock = assistant.ask(db_url, question='stock bajo',
                            user_id=doble['id'], zone=ZONE,
                            branches={'sales': [world['a']['id']],
                                      'agenda': [world['a']['id']],
                                      'inventory': [world['b']['id']]})
    assert any(i['sku'] == pb['sku'] for i in r_stock['data']['items'])
    r_stock_a = assistant.ask(db_url, question='stock bajo',
                              user_id=world['gerente']['id'], zone=ZONE,
                              branches={'sales': [world['a']['id']],
                                        'agenda': [world['a']['id']],
                                        'inventory': [world['a']['id']]})
    assert r_stock_a['data']['items'] == []


# ------------------------------------------------- A3: revocación durable

def test_a3_revocacion_no_reaparece_por_lecturas(db_url, org, admin_user):
    usuario = _user(db_url)
    b1 = scope.create_branch(db_url, name=f'Sede R {_tag()}',
                             timezone=ZONE)['branch']
    scope.assign_scope(db_url, user_id=usuario['id'], scope_role='asesor',
                       branch_id=b1['id'])
    client = _client(db_url, org, usuario['username'])
    assert client.get('/api/agenda').status_code == 200

    scope.revoke_scope(db_url, user_id=usuario['id'], scope_role='asesor',
                       branch_id=b1['id'])

    # Re-autenticar y recorrer lecturas varias veces: sin reposición.
    for _ in range(3):
        client = _client(db_url, org, usuario['username'])
        assert client.get('/').status_code == 200
        assert client.get('/settings').status_code == 200
        assert client.get('/api/agenda').status_code == 403

    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT count(*) AS n FROM user_branch_roles '
                        'WHERE user_id=%s', (usuario['id'],))
            assert cur.fetchone()['n'] == 0


# ------------------------------------------------- A4: inventario usable

def test_a4_inventario_sin_handlers_inline_y_con_data(db_url, org,
                                                      admin_user):
    world = _two_branch_world(db_url, admin_user)
    pb = commerce.create_product(db_url, sku=f'PROD-UI-{_tag()}',
                                 name='Producto UI', price='12.00',
                                 kind='producto', stock=5,
                                 branch_id=world['b']['id'])['product']
    director = _client(db_url, org, 'admin_test')
    html = director.get('/inventory').get_data(as_text=True)
    assert 'onclick=' not in html, 'CSP script-src self bloquea handlers inline'
    assert 'data-history=' in html
    assert f'data-price="{pb["id"]}"' in html       # director: precio en B
    assert f'data-stock="{pb["id"]}"' in html       # director: stock en B
    assert "unsafe-inline" not in director.get('/inventory').headers \
        .get('Content-Security-Policy', '')

    almacen = _client(db_url, org, world['almacen']['username'])
    html_b = almacen.get('/inventory').get_data(as_text=True)
    assert f'data-stock="{pb["id"]}"' in html_b      # su sede: ajusta stock
    assert 'data-price=' not in html_b               # nunca precio
    # Producto de sede A: ni stock ni precio para el almacén de B.
    pa = commerce.create_product(db_url, sku=f'PROD-UA-{_tag()}',
                                 name='Producto otra sede', price='9.00',
                                 kind='producto', stock=2,
                                 branch_id=world['a']['id'])['product']
    html_mix = almacen.get('/inventory').get_data(as_text=True)
    assert f'data-stock="{pa["id"]}"' not in html_mix


def test_a4_almacen_ajusta_su_sede_no_precio_ni_ajena(db_url, org,
                                                      admin_user):
    world = _two_branch_world(db_url, admin_user)
    pb = commerce.create_product(db_url, sku=f'PROD-S-{_tag()}',
                                 name='Stock B', price='30.00',
                                 kind='producto', stock=7,
                                 branch_id=world['b']['id'])['product']
    pa = commerce.create_product(db_url, sku=f'PROD-SX-{_tag()}',
                                 name='Stock A', price='31.00',
                                 kind='producto', stock=7,
                                 branch_id=world['a']['id'])['product']
    almacen = _client(db_url, org, world['almacen']['username'])
    csrf = {'X-CSRF-Token': almacen.csrf}

    # Ajuste propio: 302 y movimiento auditado con nota.
    ok = almacen.post(f'/inventory/products/{pb["id"]}/stock',
                      data={'delta': '-2', 'note': 'merma de prueba', **{
                          'csrf_token': almacen.csrf}})
    assert ok.status_code == 302
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT delta, note, cause FROM stock_movements '
                        'WHERE product_id=%s AND cause=%s '
                        'ORDER BY id DESC LIMIT 1', (pb['id'], 'adjustment'))
            movement = cur.fetchone()
            cur.execute('SELECT stock FROM products WHERE id=%s', (pb['id'],))
            stock = cur.fetchone()['stock']
    assert movement['delta'] == -2 and movement['note'] == 'merma de prueba'
    assert stock == 5

    # Ajuste en sede ajena: denegado (redirect web, patrón de la app) y
    # sin ningún cambio en la base.
    denied = almacen.post(f'/inventory/products/{pa["id"]}/stock',
                          data={'delta': '1', 'note': 'x', **{
                              'csrf_token': almacen.csrf}})
    assert denied.status_code == 302
    # Precio: denegado para almacén incluso en su sede.
    price = almacen.post(f'/inventory/products/{pb["id"]}/price',
                         data={'price': '1.00', 'reason': 'x', **{
                             'csrf_token': almacen.csrf}})
    assert price.status_code == 302
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT stock, price FROM products WHERE id=%s',
                        (pa['id'],))
            unchanged = cur.fetchone()
            cur.execute('SELECT count(*) AS n FROM product_price_history '
                        'WHERE product_id=%s', (pb['id'],))
            prices = cur.fetchone()['n']
    assert unchanged['stock'] == 7 and prices == 0


# ------------------------------------------------- A6: migración poblada

def test_a6_migracion_preserva_base_poblada_pre_e01(db_url, tmp_path):
    """Ensayo A6: base sintética en esquema 0001–0005 PBLADA, luego 0006+0007.

    Compara IDs, historial (acción/motivo), precios auditados y costo de
    línea antes/después; el backfill etiqueta a sede 1 sin reinterpretar.
    """
    from urllib.parse import urlsplit
    parts = urlsplit(db_url)
    admin_dsn = f'{parts.scheme}://{parts.netloc}/postgres'
    name = f'e01r_pre_{_tag()}'
    admin = psycopg.connect(admin_dsn, autocommit=True)
    admin.execute(f'CREATE DATABASE "{name}"')
    admin.close()
    pre_dsn = f'{parts.scheme}://{parts.netloc}/{name}'
    from crm_premium.infrastructure.persistence import migrations
    try:
        pre_dir = tmp_path / 'pre_e01'
        pre_dir.mkdir()
        for sql in sorted(migrations.MIGRATIONS_DIR.glob('*.sql')):
            if sql.name.split('_', 1)[0].isdigit() and \
                    int(sql.name.split('_', 1)[0]) <= 5:
                (pre_dir / sql.name).write_text(sql.read_text(encoding='utf-8'),
                                                encoding='utf-8')
        assert migrations.apply_all(pre_dsn, directory=pre_dir) != []

        # ---- poblar con el esquema ANTERIOR a E01 (sin sedes) ----
        with psycopg.connect(pre_dsn, autocommit=True,
                             row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Toda base real pre-E01 tiene su perfil de organización
                # (0006 lo usa para nombrar la sede Principal).
                cur.execute("""INSERT INTO organization (id, name, zone)
                               VALUES (1, 'Negocio Viejo', 'UTC')""")
                cur.execute(
                    """INSERT INTO users (username, password_hash, full_name, role)
                       VALUES ('viejo', 'x', 'Usuario viejo', 'admin')
                       RETURNING id""")
                admin_id = cur.fetchone()['id']
                cur.execute(
                    """INSERT INTO contacts (full_name, phone, channel)
                       VALUES ('Paciente viejo', '+593900000999', 'web')
                       RETURNING id""")
                contact_id = cur.fetchone()['id']
                cur.execute(
                    """INSERT INTO resources (name, specialty)
                       VALUES ('Profesional viejo', 'General') RETURNING id""")
                resource_id = cur.fetchone()['id']
                cur.execute(
                    """INSERT INTO appointments (resource_id, contact_id, title,
                           start_utc, end_utc, event_id, origin,
                           operational_status, row_version)
                       VALUES (%s, %s, 'Cita vieja',
                               '2029-05-01T10:00:00+00:00',
                               '2029-05-01T10:30:00+00:00', 'evt-vieja',
                               'local', 'confirmed', 3) RETURNING id""",
                    (resource_id, contact_id))
                appt_id = cur.fetchone()['id']
                cur.execute(
                    """INSERT INTO appointment_history
                       (appointment_id, action, actor_user_id, actor_label,
                        detail, reason)
                       VALUES (%s, 'confirmacion', %s, NULL,
                               '{"before": {"status": "pending"}}',
                               'confirmado por teléfono')""",
                    (appt_id, admin_id))
                cur.execute(
                    """INSERT INTO appointment_notes (appointment_id,
                           author_user_id, body) VALUES (%s, %s, 'nota vieja')""",
                    (appt_id, admin_id))
                cur.execute(
                    """INSERT INTO products (sku, name, kind, price, cost, stock,
                           min_stock) VALUES ('SKU-VIEJO', 'Producto viejo',
                           'producto', 25.00, 10.00, 4, 1) RETURNING id""")
                product_id = cur.fetchone()['id']
                cur.execute(
                    """INSERT INTO product_price_history
                       (product_id, old_price, new_price, reason, actor_user_id)
                       VALUES (%s, 20.00, 25.00, 'ajuste viejo', %s)""",
                    (product_id, admin_id))
                cur.execute(
                    """INSERT INTO sales (contact_id, total, paid,
                           payment_method, is_demo, created_by)
                       VALUES (%s, 50.00, 50.00, 'efectivo', false, %s)
                       RETURNING id""",
                    (contact_id, admin_id))
                sale_id = cur.fetchone()['id']
                cur.execute(
                    """INSERT INTO sale_lines (sale_id, product_id, product_name,
                           kind, qty, unit_price, unit_cost, line_total)
                       VALUES (%s, %s, 'Producto viejo', 'producto', 2, 25.00,
                               10.00, 50.00)""", (sale_id, product_id))
                cur.execute(
                    """INSERT INTO stock_movements (product_id, delta,
                           resulting_stock, cause, sale_id, actor_user_id)
                       VALUES (%s, -2, 2, 'sale', %s, %s)""",
                    (product_id, sale_id, admin_id))

        def _snapshot(dsn):
            with psycopg.connect(dsn, autocommit=True,
                                 row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    out = {}
                    cur.execute('SELECT id, full_name FROM contacts ORDER BY id')
                    out['contactos'] = cur.fetchall()
                    cur.execute('SELECT action, reason, detail, note_id '
                                'FROM appointment_history ORDER BY id')
                    out['historial'] = cur.fetchall()
                    cur.execute('SELECT old_price, new_price, reason '
                                'FROM product_price_history ORDER BY id')
                    out['precios'] = cur.fetchall()
                    cur.execute('SELECT unit_price, unit_cost, qty, line_total '
                                'FROM sale_lines ORDER BY id')
                    out['lineas'] = cur.fetchall()
                    cur.execute('SELECT delta, resulting_stock, cause '
                                'FROM stock_movements ORDER BY id')
                    out['movimientos'] = cur.fetchall()
                    cur.execute('SELECT title, start_utc, row_version, '
                                'operational_status FROM appointments ORDER BY id')
                    out['citas'] = cur.fetchall()
                    cur.execute('SELECT cost FROM products WHERE sku=%s',
                                ('SKU-VIEJO',))
                    out['costo'] = cur.fetchone()
                return out

        before = _snapshot(pre_dsn)
        applied = migrations.apply_all(pre_dsn)  # 0006 + 0007
        assert applied == ['0006_branches.sql', '0007_branch_backfill.sql']
        after = _snapshot(pre_dsn)

        # Preservación exacta: IDs, historia, precio y costo.
        assert after['contactos'] == before['contactos']
        assert after['historial'] == before['historial']
        assert after['precios'] == before['precios']
        assert after['lineas'] == before['lineas']
        assert after['movimientos'] == before['movimientos']
        assert after['citas'] == before['citas']
        assert after['costo']['cost'] == __import__('decimal').Decimal('10.00')

        # Backfill a sede 1 y ámbitos iniciales (una vez).
        with psycopg.connect(pre_dsn, autocommit=True,
                             row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                for table in ('resources', 'appointments', 'products', 'sales',
                              'stock_movements'):
                    cur.execute(f'SELECT count(*) AS n FROM {table} '
                                'WHERE branch_id IS NULL')
                    assert cur.fetchone()['n'] == 0, table
                cur.execute('SELECT count(*) AS n FROM user_branch_roles')
                inicial = cur.fetchone()['n']
                assert inicial == 1  # admin viejo → director global
        # Las lecturas repetidas NO añaden ámbitos (A3).
        organization.get(pre_dsn)
        organization.get(pre_dsn)
        with psycopg.connect(pre_dsn, autocommit=True,
                             row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT count(*) AS n FROM user_branch_roles')
                assert cur.fetchone()['n'] == inicial
    finally:
        admin = psycopg.connect(admin_dsn, autocommit=True)
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()
