"""Comercio: catálogo, precios auditados, stock por movimientos y ventas."""
import threading

from crm_premium.modules.commerce import service as commerce


def _mk(url, admin_user, sku='SRV-TEST', kind='servicio', price='50.00', stock=0):
    return commerce.create_product(
        url, sku=sku, name=f'Artículo {sku}', kind=kind, category='Pruebas',
        price=price, stock=stock, min_stock=2, actor=admin_user['id'])


def test_crear_producto_y_duplicado(db_url, admin_user):
    first = _mk(db_url, admin_user)
    assert first['ok']
    dup = _mk(db_url, admin_user)
    assert not dup['ok'] and dup['code'] == 'sku_taken'
    bad_price = commerce.create_product(db_url, sku='SRV-BAD', name='X',
                                        price='-3')
    assert not bad_price['ok'] and bad_price['code'] == 'invalid_price'


def test_cambio_de_precio_audita(db_url, admin_user):
    product = _mk(db_url, admin_user, 'SRV-PRECIO-AUD', price='50.00')['product']
    denied = commerce.change_price(db_url, product_id=product['id'],
                                   new_price='60.00', reason='x', actor=admin_user["id"],
                                   role='user')
    assert not denied['ok'] and denied['code'] == 'forbidden'
    no_reason = commerce.change_price(db_url, product_id=product['id'],
                                      new_price='60.00', reason=' ', actor=admin_user["id"],
                                      role='admin')
    assert not no_reason['ok'] and no_reason['code'] == 'reason_required'
    ok = commerce.change_price(db_url, product_id=product['id'],
                               new_price='60.00', reason='actualización de lista',
                               actor=admin_user["id"], role='admin')
    assert ok['ok'] and float(ok['product']['price']) == 60.00
    history = commerce.price_history(db_url, product['id'])
    assert len(history) == 1
    assert float(history[0]['old_price']) == 50.00
    assert float(history[0]['new_price']) == 60.00
    assert history[0]['reason'] == 'actualización de lista'


def test_ajuste_stock_auditado(db_url, admin_user):
    product = _mk(db_url, admin_user, 'PRD-TEST', kind='producto', stock=10)['product']
    entry = commerce.adjust_stock(db_url, product_id=product['id'], delta=5,
                                  note='compra', actor=admin_user["id"], role='admin')
    assert entry['ok'] and entry['product']['stock'] == 15
    too_low = commerce.adjust_stock(db_url, product_id=product['id'], delta=-99,
                                    note='merma', actor=admin_user["id"], role='admin')
    assert not too_low['ok'] and too_low['code'] == 'negative_stock'
    movements = commerce.stock_history(db_url, product['id'])
    assert [m['delta'] for m in movements] == [5, 10]  # más nuevo primero


def test_venta_descuenta_stock_y_registra_pago(db_url, admin_user):
    product = _mk(db_url, admin_user, 'PRD-VENTA', kind='producto', stock=5)['product']
    service = _mk(db_url, admin_user, 'SRV-VENTA', price='25.00')['product']
    result = commerce.create_sale(db_url, lines=[
        {'product_id': product['id'], 'qty': 2},
        {'product_id': service['id'], 'qty': 1}],
        payment_method='efectivo', actor=admin_user["id"])
    assert result['ok'], result
    detail = commerce.sale_detail(db_url, result['sale_id'])
    assert len(detail['lines']) == 2
    assert float(detail['sale']['total']) == 125.00  # 2×50 + 25
    assert float(detail['sale']['paid']) == 125.00
    listed = commerce.list_products(db_url, q='PRD-VENTA')
    assert listed[0]['stock'] == 3


def test_venta_sin_stock_rechazada(db_url, admin_user):
    product = _mk(db_url, admin_user, 'PRD-BAJO', kind='producto', stock=1)['product']
    result = commerce.create_sale(db_url, lines=[
        {'product_id': product['id'], 'qty': 2}], actor=admin_user["id"])
    assert not result['ok'] and result['code'] == 'insufficient_stock'
    assert result['message'].find('PRD-BAJO') >= 0


def test_venta_vacia_o_linea_mala(db_url, admin_user):
    assert commerce.create_sale(db_url, lines=[])[
        'code'] == 'empty_sale'
    product = _mk(db_url, admin_user, 'SRV-MAL', price='10')['product']
    bad = commerce.create_sale(db_url, lines=[{'product_id': product['id'],
                                               'qty': 0}])
    assert bad['code'] == 'invalid_line'


def test_reversion_compensatoria(db_url, admin_user):
    product = _mk(db_url, admin_user, 'PRD-REV', kind='producto', stock=10)['product']
    sale = commerce.create_sale(db_url, lines=[
        {'product_id': product['id'], 'qty': 4}], actor=admin_user["id"])
    assert sale['ok']
    denied = commerce.reverse_sale(db_url, sale_id=sale['sale_id'],
                                   reason='x', actor=admin_user["id"], role='user')
    assert not denied['ok'] and denied['code'] == 'forbidden'
    no_reason = commerce.reverse_sale(db_url, sale_id=sale['sale_id'],
                                      reason=' ', actor=admin_user["id"], role='admin')
    assert not no_reason['ok'] and no_reason['code'] == 'reason_required'
    ok = commerce.reverse_sale(db_url, sale_id=sale['sale_id'],
                               reason='devolución del cliente', actor=admin_user["id"],
                               role='admin')
    assert ok['ok']
    listed = commerce.list_products(db_url, q='PRD-REV')
    assert listed[0]['stock'] == 10
    again = commerce.reverse_sale(db_url, sale_id=sale['sale_id'],
                                  reason='otra vez', actor=admin_user["id"], role='admin')
    assert not again['ok'] and again['code'] == 'already_reversed'
    movements = commerce.stock_history(db_url, product['id'])
    causes = [m['cause'] for m in movements]
    assert 'sale' in causes and 'reversal' in causes


def test_concurrencia_ultima_unidad(db_url, admin_user):
    """Dos ventas simultáneas de la última unidad: exactamente una gana."""
    product = _mk(db_url, admin_user, 'PRD-UNO', kind='producto', stock=1)['product']
    results = []
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()
        results.append(commerce.create_sale(db_url, lines=[
            {'product_id': product['id'], 'qty': 1}], actor=admin_user["id"]))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    won = [r for r in results if r['ok']]
    lost = [r for r in results if not r['ok']]
    assert len(won) == 1 and len(lost) == 1
    assert lost[0]['code'] == 'insufficient_stock'
    listed = commerce.list_products(db_url, q='PRD-UNO')
    assert listed[0]['stock'] == 0


def test_stock_bajo_detectado(db_url, admin_user):
    _mk(db_url, admin_user, 'PRD-MIN', kind='producto', stock=1)  # min_stock=2
    low = commerce.low_stock_products(db_url)
    assert any(item['sku'] == 'PRD-MIN' for item in low)
