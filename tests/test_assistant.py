"""Asistente interno: herramientas, intención y auditoría de cada respuesta."""
from crm_premium.modules.assistant import service as assistant
from crm_premium.modules.commerce import service as commerce

ZONE = 'UTC'


def _mk_product(db_url, sku, kind='servicio', price='42.00', stock=0, min_stock=0):
    return commerce.create_product(db_url, sku=sku, name=f'Artículo {sku}',
                                   kind=kind, price=price, stock=stock,
                                   min_stock=min_stock)['product']


def test_pregunta_ventas_registra_auditoria(db_url, org, admin_user):
    result = assistant.ask(db_url, question='¿cuáles fueron las ventas de hoy?',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['ok'] and result['tool'] == 'ventas'
    assert 'Ventas netas' in result['answer'] or 'ventas netas' in result['answer']
    assert result['logged_id'] > 0
    logged = assistant.history(db_url)
    assert any(item['question'].startswith('¿cuáles') for item in logged)
    assert logged[0]['username'] == 'admin_test'


def test_top_tratamientos(db_url, org, admin_user):
    best = _mk_product(db_url, 'SRV-TOP1', price='100.00')
    other = _mk_product(db_url, 'SRV-TOP2', price='10.00')
    from crm_premium.modules.commerce import service as commerce
    commerce.create_sale(db_url, lines=[{'product_id': best['id'], 'qty': 3}],
                         actor=admin_user["id"])
    commerce.create_sale(db_url, lines=[{'product_id': other['id'], 'qty': 1}],
                         actor=admin_user["id"])
    result = assistant.ask(db_url, question='tratamientos más vendidos',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['tool'] == 'top_productos'
    assert result['data']['items'][0]['product_name'] == 'Artículo SRV-TOP1'


def test_precio_por_nombre(db_url, org, admin_user):
    _mk_product(db_url, 'SRV-PRECIO', price='66.50')
    result = assistant.ask(db_url, question='¿cuál es el precio de artículo SRV-PRECIO?',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['tool'] == 'precio'
    assert '66.50' in result['answer']


def test_stock_bajo(db_url, org, admin_user):
    _mk_product(db_url, 'PRD-STOCK', kind='producto', stock=1, min_stock=3)
    result = assistant.ask(db_url, question='qué producto está con stock bajo',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['tool'] == 'stock_bajo'
    assert any(item['sku'] == 'PRD-STOCK' for item in result['data']['items'])


def test_citas_hoy(db_url, org, admin_user, resource):
    from crm_premium.modules.scheduling import service as scheduling
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Cita futura cercana dentro de hoy (para no chocar con el pasado).
    result = assistant.ask(db_url, question='citas de hoy',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['tool'] == 'citas_hoy'
    assert 'cita' in result['answer']


def test_conocimiento_rag_basico(db_url, org, admin_user):
    from crm_premium.infrastructure.persistence.db import transaction
    with transaction(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO knowledge_docs (title, content) '
                        'VALUES (%s, %s)',
                        ('Política de cancelación (prueba)',
                         'Las cancelaciones con menos de 4 horas generan cargo.'))
    result = assistant.ask(db_url, question='cuál es la política de cancelación',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['tool'] == 'conocimiento'
    assert 'cancelaci' in result['answer'].lower()


def test_desconocido_devuelve_ayuda(db_url, org, admin_user):
    result = assistant.ask(db_url, question='hola qué tal el clima',
                           user_id=admin_user['id'], zone=ZONE)
    assert result['tool'] == 'ayuda'
    assert 'Puedo responder' in result['answer']


def test_pregunta_vacia(db_url, org, admin_user):
    result = assistant.ask(db_url, question='   ', user_id=admin_user['id'])
    assert not result['ok']
