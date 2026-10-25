"""Analítica: reconstrucción del modelo estrella y consultas del panel."""
from crm_premium.modules.analytics import service as analytics
from crm_premium.modules.commerce import service as commerce
from crm_premium.modules.scheduling import service as scheduling

ZONE = 'UTC'


def _seed_data(db_url, org, admin_user, resource, contact):
    service = commerce.create_product(db_url, sku='SRV-ANA', name='Limpieza analítica',
                                      kind='servicio', price='100.00')
    product = commerce.create_product(db_url, sku='PRD-ANA', name='Kit analítico',
                                      kind='producto', price='10.00', stock=50)
    sale = commerce.create_sale(db_url, lines=[
        {'product_id': service['product']['id'], 'qty': 3},
        {'product_id': product['product']['id'], 'qty': 5}],
        actor=admin_user['id'])
    # Cita AYER a las 10:00 UTC con reloj inyectado (la ventana del panel
    # mira hacia atrás; una cita futura quedaría fuera del período).
    from datetime import datetime, timedelta, timezone as _tz
    yesterday = datetime.now(_tz.utc) - timedelta(days=1)
    before = datetime.now(_tz.utc) - timedelta(days=2)
    scheduling.save_appointment(
        db_url, resource_id=resource['id'],
        start=yesterday.strftime('%Y-%m-%dT10:00'),
        end=yesterday.strftime('%Y-%m-%dT11:00'),
        title='Cita BI', zone=ZONE, clock=before)
    return service['product'], product['product'], sale


def test_rebuild_idempotente_y_cuadre(db_url, org, admin_user, resource, contact):
    service, product, sale = _seed_data(db_url, org, admin_user, resource, contact)
    first = analytics.rebuild_bi(db_url, ZONE)
    assert first['citas'] >= 1 and first['lineas_venta'] >= 2
    second = analytics.rebuild_bi(db_url, ZONE)
    assert second['citas'] == first['citas']  # idempotente
    assert analytics.last_rebuild(db_url) is not None

    data = analytics.overview(db_url, ZONE, days=3650)
    total_sales = float(service['price']) * 3 + float(product['price']) * 5
    assert abs(data['kpis']['ventas_netas'] - total_sales) < 0.01
    assert data['kpis']['unidades'] == 8
    assert any(item['label'] == 'Limpieza analítica'
               for item in data['top_servicios'])
    assert any(item['label'] == 'Kit analítico'
               for item in data['top_productos'])
    # La cita sembrada cae en la franja horaria 10.
    assert any(slot['hora'] == 10 and slot['citas'] >= 1
               for slot in data['horas_pico_citas'])


def test_reversion_conserva_positivo_y_compensa(db_url, org, admin_user, resource,
                                                contact):
    """CORR01/R02: la reversión no reescribe la venta histórica; el neto
    acumulado baja exactamente el importe revertido."""
    service, product, sale = _seed_data(db_url, org, admin_user, resource, contact)
    analytics.rebuild_bi(db_url, ZONE)
    before = analytics.overview(db_url, ZONE, days=3650)['kpis']['ventas_netas']
    assert abs(before - 350.00) < 0.01
    commerce.reverse_sale(db_url, sale_id=sale['sale_id'],
                          reason='prueba de neteo', actor=admin_user['id'],
                          role='admin')
    analytics.rebuild_bi(db_url, ZONE)
    after = analytics.overview(db_url, ZONE, days=3650)['kpis']['ventas_netas']
    assert abs(after) < 0.01  # neto acumulado 0: positivo + compensación


def test_vista_por_dias_acotada(db_url, org):
    analytics.rebuild_bi(db_url, ZONE)
    data = analytics.overview(db_url, ZONE, days=7)
    assert data['dias'] == 7
    assert len(data['ventas_por_dia']) == 7
    assert len(data['horas_pico_citas']) == 24
    assert len(data['estados']) == 5
