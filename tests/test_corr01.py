"""CORR01: reproducciones de los hallazgos R02–R10 de la auditoría.

Cada prueba se escribió contra el código auditado (antes de la corrección)
para reproducir el defecto; tras CORR01 deben pasar. Evidencia de la corrida
roja previa en pruebas/ejecuciones/<UTC-ID>/.
"""
import threading
from datetime import datetime, timedelta, timezone

from crm_premium.entrypoints.web.app import create_app
from crm_premium.modules.analytics import service as analytics
from crm_premium.modules.assistant import service as assistant
from crm_premium.modules.commerce import service as commerce
from crm_premium.modules.identity import service as identity
from crm_premium.modules.organization import service as organization

from conftest import login_as


# --------------------------------------------------------------------- R02

def _sale_100(db_url, admin_user, sku='SRV-R02'):
    product = commerce.create_product(db_url, sku=sku, name='Servicio R02',
                                      price='100.00')['product']
    return commerce.create_sale(db_url, lines=[{'product_id': product['id'],
                                                'qty': 1}],
                                actor=admin_user['id'])


def test_r02_reversion_total_neto_cero_y_fechas_propias(db_url, org, admin_user):
    """Venta 100 → anulación → neto acumulado 0; la compensación vive en su
    propia fecha y la venta histórica conserva su positivo."""
    sale = _sale_100(db_url, admin_user)
    assert sale['ok']
    # La venta ocurre hoy; movemos created_at 8 días atrás para simular
    # período anterior (la reversión queda HOY, en su propia fecha).
    from crm_premium.infrastructure.persistence.db import transaction
    past = datetime.now(timezone.utc) - timedelta(days=8)
    with transaction(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE sales SET created_at=%s WHERE id=%s',
                        (past, sale['sale_id']))
    reversal = commerce.reverse_sale(db_url, sale_id=sale['sale_id'],
                                     reason='anulación total R02',
                                     actor=admin_user['id'], role='admin')
    assert reversal['ok']
    analytics.rebuild_bi(db_url, 'UTC')
    data = analytics.overview(db_url, 'UTC', days=30)
    assert abs(data['kpis']['ventas_netas']) < 0.01  # neto acumulado 0
    per_day = {d['dia']: d['neto'] for d in data['ventas_por_dia']}
    assert abs(per_day.get(past.date().isoformat(), 0) - 100.0) < 0.01  # positivo histórico
    today = datetime.now(timezone.utc).date().isoformat()
    assert abs(per_day.get(today, 0) + 100.0) < 0.01  # compensación en su fecha


def test_r02_asistente_cuenta_reversion_en_su_momento(db_url, org, admin_user):
    sale = _sale_100(db_url, admin_user, 'SRV-R02B')
    # La venta ocurre hace 8 días; la reversión HOY debe ser el único
    # movimiento visible de hoy: -100 (compensación en su momento).
    from crm_premium.infrastructure.persistence.db import transaction
    past = datetime.now(timezone.utc) - timedelta(days=8)
    with transaction(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE sales SET created_at=%s WHERE id=%s',
                        (past, sale['sale_id']))
    commerce.reverse_sale(db_url, sale_id=sale['sale_id'], reason='x',
                          actor=admin_user['id'], role='admin')
    result = assistant.ask(db_url, question='ventas de hoy',
                           user_id=admin_user['id'], zone='UTC')
    assert result['tool'] == 'ventas'
    # Hoy: la compensación -100; ninguna venta confirmada nueva ⇒ neto -100.
    assert abs(result['data']['neto'] + 100.0) < 0.01


# --------------------------------------------------------------------- R03

def _policy_weekdays_9_17(url):
    organization.update(url, opening={'days': [0, 1, 2, 3, 4],
                                      'start': '09:00', 'end': '17:00'})
    return organization.build_window_policy(organization.get(url))


def test_r03_rechaza_intervalo_que_atraviesa_noche_cerrada(db_url, org):
    policy = _policy_weekdays_9_17(db_url)
    start = datetime(2026, 10, 26, 10, 0, tzinfo=timezone.utc)  # lunes
    end = datetime(2026, 10, 27, 11, 0, tzinfo=timezone.utc)    # martes
    assert policy(start, end) is not None, 'debe rechazar cruce de noche cerrada'


def test_r03_rechaza_fin_unos_segundos_despues_del_cierre(db_url, org):
    policy = _policy_weekdays_9_17(db_url)
    start = datetime(2026, 10, 26, 16, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 26, 17, 0, 30, tzinfo=timezone.utc)
    assert policy(start, end) is not None


def test_r03_permite_terminar_exactamente_al_cierre(db_url, org):
    policy = _policy_weekdays_9_17(db_url)
    start = datetime(2026, 10, 26, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 26, 17, 0, 0, tzinfo=timezone.utc)
    assert policy(start, end) is None


def test_r03_rechaza_fin_de_semana(db_url, org):
    policy = _policy_weekdays_9_17(db_url)
    start = datetime(2026, 10, 31, 10, 0, tzinfo=timezone.utc)  # sábado
    end = datetime(2026, 10, 31, 11, 0, tzinfo=timezone.utc)
    assert policy(start, end) is not None


def test_r03_jornada_completa_hasta_el_segundo_exacto(db_url, org):
    organization.update(db_url, opening={'days': list(range(7)),
                                         'start': '00:00', 'end': '23:59'})
    policy = organization.build_window_policy(organization.get(db_url))
    start = datetime(2026, 10, 26, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 26, 23, 59, 0, tzinfo=timezone.utc)
    assert policy(start, end) is None  # termina exactamente al cierre: permitido
    beyond = datetime(2026, 10, 26, 23, 59, 30, tzinfo=timezone.utc)
    assert policy(start, beyond) is not None  # un segundo más: rechazado


def test_r03_perfil_24x7_permite_49_horas(db_url, org):
    organization.update(db_url, opening={})  # sin horario = 24×7
    assert organization.build_window_policy(organization.get(db_url)) is None


# ------------------------------------------------------------------ R04/R05

def _fresh_client(db_url, org):
    app = create_app(db_url=db_url)
    app.config['testing'] = True
    return app.test_client()


def test_r04_usuario_no_ve_preguntas_ajenas(db_url, org, admin_user, plain_user):
    assistant.ask(db_url, question='ventas de hoy MARCA-UNICA-R04', user_id=admin_user['id'],
                  zone='UTC')
    other = login_as(db_url, _fresh_client(db_url, org), plain_user['username'])
    page = other.get('/assistant')
    html = page.data.decode('utf-8')
    assert 'MARCA-UNICA-R04' not in html, 'usuario ordinario no debe ver Q&A ajenos'


def test_r04_admin_ve_global_con_permiso(db_url, org, admin_user, plain_user):
    assistant.ask(db_url, question='stock bajo MARCA-UNICA-GLOBAL',
                  user_id=plain_user['id'], zone='UTC')
    admin = login_as(db_url, _fresh_client(db_url, org), 'admin_test')
    html = admin.get('/assistant?scope=global').data.decode('utf-8')
    assert 'MARCA-UNICA-GLOBAL' in html  # la vista global es explícita y sólo admin  # la vista global es explícita y sólo admin


def test_r05_usuario_ordinario_no_cambia_ajustes_globales(db_url, org,
                                                          plain_user):
    other = login_as(db_url, _fresh_client(db_url, org), plain_user['username'])
    response = other.post('/settings', data={
        'csrf_token': other.csrf, 'name': 'Negocio hackeado',
        'zone': 'UTC', 'currency': 'EUR'})
    assert response.status_code == 302
    assert organization.get(db_url)['name'] != 'Negocio hackeado'


# ------------------------------------------------------------------ R06/R07

def test_r06_cambio_de_rol_revoca_sesiones(db_url, org, admin_user, plain_user):
    auth = identity.authenticate(db_url, username=plain_user['username'],
                                 password='ClaveLarga.2026')
    assert auth['ok']
    result = identity.set_user_role(db_url, user_id=plain_user['id'],
                                    role='admin')
    assert result['ok']
    user, _ = identity.user_for_session(db_url, token=auth['token'])
    assert user is None, 'el token debe morir al cambiar el rol'


def test_r07_login_fallido_y_luego_correcto_sin_recarga(db_url, org, admin_user):
    app = create_app(db_url=db_url)
    app.config['testing'] = True
    with app.test_client() as client:
        first = client.get('/login')
        token1 = first.data.decode('utf-8').split(
            'name="csrf_token" value="')[1].split('"')[0]
        failed = client.post('/login', data={
            'username': 'admin_test', 'password': 'Incorrecta.2026',
            'csrf_token': token1})
        assert failed.status_code == 401
        token2 = failed.data.decode('utf-8').split(
            'name="csrf_token" value="')[1].split('"')[0]
        assert token2 and token2 != token1
        retry = client.post('/login', data={
            'username': 'admin_test', 'password': 'ClaveLarga.2026',
            'csrf_token': token2})
        assert retry.status_code == 302, ('el reintento con el par regenerado '
                                          'debe autenticar sin recargar')


def test_r07_token_csrf_ajeno_rechazado(db_url, org, admin_user):
    app = create_app(db_url=db_url)
    app.config['testing'] = True
    with app.test_client() as client:
        client.get('/login')
        response = client.post('/login', data={
            'username': 'admin_test', 'password': 'ClaveLarga.2026',
            'csrf_token': 'token-ajeno-123'})
        assert response.status_code == 400


# --------------------------------------------------------------------- R08

def test_r08_bi_excluye_demo_por_defecto(db_url, org, admin_user):
    product = commerce.create_product(db_url, sku='SRV-DEMO', name='Demo',
                                      price='50.00')['product']
    real = commerce.create_product(db_url, sku='SRV-REAL', name='Real',
                                   price='10.00')['product']
    commerce.create_sale(db_url, lines=[{'product_id': product['id'], 'qty': 1}],
                         actor=admin_user['id'], is_demo=True)
    commerce.create_sale(db_url, lines=[{'product_id': real['id'], 'qty': 2}],
                         actor=admin_user['id'])
    analytics.rebuild_bi(db_url, 'UTC')
    default = analytics.overview(db_url, 'UTC', days=30)
    assert abs(default['kpis']['ventas_netas'] - 20.0) < 0.01
    with_demo = analytics.overview(db_url, 'UTC', days=30, include_demo=True)
    assert abs(with_demo['kpis']['ventas_netas'] - 70.0) < 0.01


def test_r08_costo_historico_no_se_recalcula(db_url, org, admin_user):
    product = commerce.create_product(db_url, sku='PRD-COSTO', kind='producto',
                                      name='Costoso', price='30.00',
                                      cost='10.00', stock=10)['product']
    commerce.create_sale(db_url, lines=[{'product_id': product['id'], 'qty': 2}],
                         actor=admin_user['id'])
    # El costo del producto cambia DESPUÉS de la venta.
    commerce.change_price(db_url, product_id=product['id'], new_price='31.00',
                          reason='lista nueva', actor=admin_user['id'],
                          role='admin')
    from crm_premium.infrastructure.persistence.db import transaction
    with transaction(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE products SET cost=99.00 WHERE id=%s',
                        (product['id'],))
    analytics.rebuild_bi(db_url, 'UTC')
    from crm_premium.infrastructure.persistence.db import connect
    with connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT costo_conocido FROM bi.fact_venta_linea '
                        'WHERE sale_id = (SELECT max(id) FROM sales)')
            costo = cur.fetchone()['costo_conocido']
    assert costo is not None and abs(float(costo) - 20.0) < 0.01  # 2 × 10.00 snapshot


def test_r08_costo_desconocido_permanece_null(db_url, org, admin_user):
    product = commerce.create_product(db_url, sku='SRV-SINCOSTO',
                                      name='Sin costo', price='15.00')['product']
    sale = commerce.create_sale(db_url, lines=[{'product_id': product['id'],
                                                'qty': 1}],
                                actor=admin_user['id'])
    assert sale['ok']
    analytics.rebuild_bi(db_url, 'UTC')
    from crm_premium.infrastructure.persistence.db import connect
    with connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT costo_conocido FROM bi.fact_venta_linea '
                        'WHERE sale_id = %s', (sale['sale_id'],))
            assert cur.fetchone()['costo_conocido'] is None


def test_r08_cobros_no_disponibles_no_es_precio(db_url, org, admin_user):
    result = assistant.ask(db_url, question='cobros de hoy',
                           user_id=admin_user['id'], zone='UTC')
    assert result['tool'] == 'no_disponible'
    assert 'no disponible' in result['answer'].lower()


def test_r08_top_separado_por_tipo(db_url, org, admin_user):
    """Con 9 servicios y 1 producto vendidos, el top de productos debe
    mostrar al producto aunque el top global mezclado lo descartara."""
    for index in range(9):
        service = commerce.create_product(db_url, sku=f"SRV-M{index}",
                                          name=f"Servicio masa {index}",
                                          price='5.00')['product']
        commerce.create_sale(db_url, lines=[{'product_id': service['id'],
                                             'qty': 1}],
                             actor=admin_user['id'])
    good = commerce.create_product(db_url, sku='PRD-UNO', kind='producto',
                                    name='Producto único', price='7.00',
                                    stock=5)['product']
    commerce.create_sale(db_url, lines=[{'product_id': good['id'], 'qty': 1}],
                         actor=admin_user['id'])
    analytics.rebuild_bi(db_url, 'UTC')
    data = analytics.overview(db_url, 'UTC', days=30)
    assert any(item['label'] == 'Producto único'
               for item in data['top_productos'])
    assert all(item['label'] != 'Producto único'
               for item in data['top_servicios'])


# --------------------------------------------------------------------- R10

def test_r10_locks_orden_inverso_sin_deadlock(db_url, org, admin_user):
    """Dos ventas concurrentes con líneas A,B y B,A: el orden determinista
    de locks debe permitir ambas sin interbloqueo."""
    a = commerce.create_product(db_url, sku='PRD-LA', kind='producto',
                                name='Lock A', price='1.00', stock=50)['product']
    b = commerce.create_product(db_url, sku='PRD-LB', kind='producto',
                                name='Lock B', price='1.00', stock=50)['product']
    results = []
    barrier = threading.Barrier(2)

    def worker(lines):
        barrier.wait()
        results.append(commerce.create_sale(db_url, lines=lines,
                                            actor=admin_user['id']))

    threads = [
        threading.Thread(target=worker, args=([
            {'product_id': a['id'], 'qty': 1}, {'product_id': b['id'], 'qty': 1}],)),
        threading.Thread(target=worker, args=([
            {'product_id': b['id'], 'qty': 1}, {'product_id': a['id'], 'qty': 1}],)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(r['ok'] for r in results), results
    listed_a = commerce.list_products(db_url, q='Lock A')[0]
    listed_b = commerce.list_products(db_url, q='Lock B')[0]
    assert listed_a['stock'] == 48 and listed_b['stock'] == 48
