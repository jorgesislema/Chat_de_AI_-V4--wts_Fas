"""Comercio: catálogo con precios auditados, stock por movimientos y ventas.

Reglas (documento 02 del expediente):
- El precio cambia sólo por ``change_price``: escribe historial con actor y
  motivo; nunca se edita el historial.
- El stock sólo se mueve por movimientos firmados con causa y saldo
  resultante; venta y reversión son compensatorias entre sí.
- Venta: líneas validadas, stock descontado atómicamente bajo bloqueo
  consultivo por producto (dos ventas no consumen la última unidad dos veces),
  pago registrado y auditoría en la misma transacción.
- Reversión: sólo administrador y con motivo; no se puede revertir dos veces.
- Dinero decimal explícito (numeric); moneda la define el perfil.
"""
from datetime import datetime, timezone
from decimal import Decimal

from psycopg.errors import UniqueViolation

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row

ADVISORY_NAMESPACE = 94002

INVALID_SKU = 'invalid_sku'
INVALID_NAME = 'invalid_name'
INVALID_PRICE = 'invalid_price'
INVALID_KIND = 'invalid_kind'
NOT_FOUND = 'not_found'
SKU_TAKEN = 'sku_taken'
PRICE_REQUIRED = 'price_required'
REASON_REQUIRED = 'reason_required'
FORBIDDEN = 'forbidden'
EMPTY_SALE = 'empty_sale'
INVALID_LINE = 'invalid_line'
INACTIVE_PRODUCT = 'inactive_product'
INSUFFICIENT_STOCK = 'insufficient_stock'
NEGATIVE_STOCK = 'negative_stock'
ALREADY_REVERSED = 'already_reversed'

KINDS = ('producto', 'servicio')


def _clock():
    return datetime.now(timezone.utc)


def _audit(cur, actor, action):
    user_id = actor if isinstance(actor, int) and not isinstance(actor, bool) else None
    label = None if user_id is not None else str(actor or 'system')[:40]
    cur.execute(
        'INSERT INTO audit_log (actor_user_id, actor_label, action) VALUES (%s,%s,%s)',
        (user_id, label, action[:500]))


def _money(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
    except Exception:
        return None
    if amount < 0:
        return None
    return amount


# ----------------------------------------------------------------- catálogo

def create_product(url, *, sku, name, kind='servicio', category=None, price,
                   cost=None, stock=0, min_stock=0, actor=None, branch_id=1):
    clean_sku = (sku or '').strip().upper()[:40]
    clean_name = (name or '').strip()[:160]
    if not clean_sku or not clean_sku.replace('-', '').replace('_', '').isalnum():
        return {'ok': False, 'code': INVALID_SKU,
                'message': 'SKU no válido (letras, números, - y _)'}
    if not clean_name:
        return {'ok': False, 'code': INVALID_NAME, 'message': 'El nombre es obligatorio'}
    if kind not in KINDS:
        return {'ok': False, 'code': INVALID_KIND,
                'message': 'El tipo debe ser producto o servicio'}
    amount = _money(price)
    if amount is None:
        return {'ok': False, 'code': INVALID_PRICE,
                'message': 'Precio no válido (mayor o igual a 0)'}
    cost_amount = _money(cost) if cost not in (None, '') else None
    stock = int(stock or 0)
    if stock < 0:
        return {'ok': False, 'code': NEGATIVE_STOCK, 'message': 'Stock inicial no válido'}
    try:
        with transaction(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO products
                       (sku, name, kind, category, price, cost, stock, min_stock,
                        branch_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                    (clean_sku, clean_name, kind,
                     (category or '').strip()[:80] or None,
                     amount, cost_amount, stock, int(min_stock or 0), branch_id))
                product = row(cur.fetchone())
                if stock:
                    cur.execute(
                        """INSERT INTO stock_movements
                           (product_id, delta, resulting_stock, cause, note, actor_user_id)
                           VALUES (%s, %s, %s, 'initial', 'Carga inicial', %s)""",
                        (product['id'], stock, stock,
                         actor if isinstance(actor, int) else None))
                _audit(cur, actor, f'Creación de producto {clean_sku}')
    except UniqueViolation:
        return {'ok': False, 'code': SKU_TAKEN, 'message': 'Ese SKU ya existe'}
    return {'ok': True, 'code': 'created', 'product': product}


def update_product(url, *, product_id, name=None, category=None, min_stock=None,
                   is_active=None):
    """Campos no críticos; precio y stock van por sus flujos auditados."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM products WHERE id=%s', (product_id,))
            current = cur.fetchone()
            if not current:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Producto no encontrado'}
            cur.execute(
                """UPDATE products SET name=%s, category=%s, min_stock=%s,
                   is_active=%s, row_version=row_version+1, updated_at=now()
                   WHERE id=%s RETURNING *""",
                ((name or current['name']).strip()[:160],
                 (category if category is not None else current['category'] or '').strip()[:80] or None,
                 int(min_stock) if min_stock is not None else current['min_stock'],
                 is_active if is_active is not None else current['is_active'],
                 product_id))
            return {'ok': True, 'code': 'updated', 'product': row(cur.fetchone())}


def change_price(url, *, product_id, new_price, reason, actor, role='user'):
    """Cambia el precio escribiendo historial; requiere motivo y rol admin."""
    if role != 'admin':
        return {'ok': False, 'code': FORBIDDEN,
                'message': 'Sólo un administrador puede cambiar precios'}
    if not (reason or '').strip():
        return {'ok': False, 'code': REASON_REQUIRED,
                'message': 'Indique el motivo del cambio de precio'}
    amount = _money(new_price)
    if amount is None:
        return {'ok': False, 'code': INVALID_PRICE, 'message': 'Precio no válido'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM products WHERE id=%s FOR UPDATE', (product_id,))
            current = cur.fetchone()
            if not current:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Producto no encontrado'}
            if current['price'] == amount:
                return {'ok': True, 'code': 'unchanged', 'product': row(current)}
            cur.execute(
                'UPDATE products SET price=%s, row_version=row_version+1, '
                'updated_at=now() WHERE id=%s', (amount, product_id))
            cur.execute(
                """INSERT INTO product_price_history
                   (product_id, old_price, new_price, reason, actor_user_id)
                   VALUES (%s,%s,%s,%s,%s)""",
                (product_id, current['price'], amount, reason.strip()[:300],
                 actor if isinstance(actor, int) else None))
            _audit(cur, actor,
                   f'Cambio de precio de {current["sku"]}: {current["price"]} → {amount}')
            cur.execute('SELECT * FROM products WHERE id=%s', (product_id,))
            return {'ok': True, 'code': 'updated', 'product': row(cur.fetchone())}


def adjust_stock(url, *, product_id, delta, note, actor, role='user'):
    """Ajuste manual de inventario (entrada/merma); movimiento auditado."""
    if role != 'admin':
        return {'ok': False, 'code': FORBIDDEN,
                'message': 'Sólo un administrador puede ajustar stock'}
    try:
        delta = int(delta)
    except (TypeError, ValueError):
        return {'ok': False, 'code': INVALID_LINE, 'message': 'Cantidad no válida'}
    if delta == 0:
        return {'ok': False, 'code': INVALID_LINE, 'message': 'El ajuste no puede ser cero'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s, %s)',
                        (ADVISORY_NAMESPACE, product_id))
            cur.execute('SELECT * FROM products WHERE id=%s FOR UPDATE', (product_id,))
            current = cur.fetchone()
            if not current:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Producto no encontrado'}
            resulting = current['stock'] + delta
            if resulting < 0:
                return {'ok': False, 'code': NEGATIVE_STOCK,
                        'message': f'El ajuste dejaría stock negativo (quedaría {resulting})'}
            cur.execute('UPDATE products SET stock=%s, row_version=row_version+1, '
                        'updated_at=now() WHERE id=%s', (resulting, product_id))
            cur.execute(
                """INSERT INTO stock_movements
                   (product_id, delta, resulting_stock, cause, note, actor_user_id)
                   VALUES (%s,%s,%s,'adjustment',%s,%s)""",
                (product_id, delta, resulting, (note or '').strip()[:300] or None,
                 actor if isinstance(actor, int) else None))
            _audit(cur, actor, f'Ajuste de stock de {current["sku"]}: {delta:+d}')
            cur.execute('SELECT * FROM products WHERE id=%s', (product_id,))
            return {'ok': True, 'code': 'updated', 'product': row(cur.fetchone())}


def list_products(url, *, q='', kind=None, low_only=False, include_inactive=False,
                  branch_ids=None):
    pattern = f'%{(q or "").strip().lower()}%'
    clauses = []
    params = [pattern, pattern]
    if q:
        clauses.append('(lower(p.name) LIKE %s OR lower(p.sku) LIKE %s)')
    else:
        clauses.append('(%s = %s OR lower(p.name) LIKE %s OR lower(p.sku) LIKE %s)')
        params = [pattern, pattern, pattern, pattern]
    if kind in KINDS:
        clauses.append('p.kind = %s')
        params.append(kind)
    if low_only:
        clauses.append("p.kind = 'producto' AND p.stock <= p.min_stock")
    if not include_inactive:
        clauses.append('p.is_active')
    if branch_ids is not None:
        if not branch_ids:
            return []
        marks = ', '.join(['%s'] * len(branch_ids))
        clauses.append(f'p.branch_id IN ({marks})')
        params.extend(sorted(set(int(b) for b in branch_ids)))
    where = ' AND '.join(clauses)
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT p.*,
                    (SELECT count(*) FROM product_price_history h
                     WHERE h.product_id = p.id) AS price_changes
                    FROM products p WHERE {where}
                    ORDER BY p.kind, p.name LIMIT 500""", params)
            items = [row(r) for r in cur.fetchall()]
    return items


def price_history(url, product_id):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT h.*, u.full_name AS actor_name
                   FROM product_price_history h
                   LEFT JOIN users u ON u.id = h.actor_user_id
                   WHERE h.product_id=%s ORDER BY h.id DESC""", (product_id,))
            return [row(r) for r in cur.fetchall()]


def stock_history(url, product_id, limit=50):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.*, s.id AS sale_ref, u.full_name AS actor_name
                   FROM stock_movements m
                   LEFT JOIN sales s ON s.id = m.sale_id
                   LEFT JOIN users u ON u.id = m.actor_user_id
                   WHERE m.product_id=%s ORDER BY m.id DESC LIMIT %s""",
                (product_id, limit))
            return [row(r) for r in cur.fetchall()]


def find_product_by_text(url, text):
    """Búsqueda por nombre/SKU para el asistente (primer resultado)."""
    pattern = f'%{(text or "").strip().lower()}%'
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM products
                   WHERE is_active AND (lower(name) LIKE %s OR lower(sku) LIKE %s)
                   ORDER BY name LIMIT 1""", (pattern, pattern))
            return row(cur.fetchone())


def low_stock_products(url):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sku, name, stock, min_stock, branch_id FROM products
                   WHERE is_active AND kind='producto' AND stock <= min_stock
                   ORDER BY stock LIMIT 20""")
            return [row(r) for r in cur.fetchall()]


# ------------------------------------------------------------------ ventas

def create_sale(url, *, lines, payment_method='efectivo', contact_id=None,
                actor=None, is_demo=False, note=None, branch_id=1):
    """Venta atómica: valida, bloquea productos, descuenta stock y registra pago."""
    if not isinstance(lines, list) or not lines:
        return {'ok': False, 'code': EMPTY_SALE, 'message': 'La venta no tiene líneas'}
    cleaned = []
    for line in lines:
        try:
            product_id = int(line.get('product_id'))
            qty = int(line.get('qty'))
        except (TypeError, ValueError):
            return {'ok': False, 'code': INVALID_LINE,
                    'message': 'Línea de venta no válida'}
        if qty <= 0 or qty > 1000:
            return {'ok': False, 'code': INVALID_LINE,
                    'message': 'La cantidad debe estar entre 1 y 1000'}
        cleaned.append((product_id, qty))
    contact_value = None
    if contact_id not in (None, ''):
        try:
            contact_value = int(contact_id)
        except (TypeError, ValueError):
            return {'ok': False, 'code': INVALID_LINE, 'message': 'Contacto no válido'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            seen = {}
            for product_id, qty in cleaned:
                if product_id in seen:
                    return {'ok': False, 'code': INVALID_LINE,
                            'message': 'Producto repetido en la venta; sume la cantidad'}
                seen[product_id] = qty
            # CORR01/R10: orden determinista de locks (id ascendente) para que
            # ventas concurrentes A,B / B,A nunca se interbloqueen.
            for product_id in sorted(seen):
                cur.execute('SELECT pg_advisory_xact_lock(%s, %s)',
                            (ADVISORY_NAMESPACE, product_id))
                cur.execute('SELECT * FROM products WHERE id=%s', (product_id,))
                product = cur.fetchone()
                if not product:
                    return {'ok': False, 'code': NOT_FOUND,
                            'message': f'Producto {product_id} no encontrado'}
                if not product['is_active']:
                    return {'ok': False, 'code': INACTIVE_PRODUCT,
                            'message': f'{product["name"]} está desactivado'}
                if product['kind'] == 'producto' and product['stock'] < seen[product_id]:
                    return {'ok': False, 'code': INSUFFICIENT_STOCK,
                            'message': f'Stock insuficiente de {product["name"]} '
                                       f'(disponible: {product["stock"]})'}
            total = sum(Decimal(p['price']) * q for p_id, q in seen.items()
                        for p in [_product_cache(cur, p_id)])
            cur.execute(
                """INSERT INTO sales (contact_id, total, paid, payment_method,
                   is_demo, note, created_by, branch_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, created_at""",
                (contact_value, total, total, (payment_method or 'efectivo').strip()[:30],
                 is_demo, (note or '').strip()[:300] or None,
                 actor if isinstance(actor, int) else None,
                 int(branch_id) if branch_id else None))
            sale = cur.fetchone()
            sale_id = sale['id']
            for product_id, qty in seen.items():
                product = _product_cache(cur, product_id)
                line_total = Decimal(product['price']) * qty
                # CORR01/R08: snapshot del costo conocido en la línea; NULL
                # significa desconocido y JAMÁS se recalcula después.
                cur.execute(
                    """INSERT INTO sale_lines
                       (sale_id, product_id, product_name, kind, qty, unit_price,
                        unit_cost, line_total)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (sale_id, product_id, product['name'], product['kind'], qty,
                     product['price'], product['cost'], line_total))
                if product['kind'] == 'producto':
                    resulting = product['stock'] - qty
                    cur.execute('UPDATE products SET stock=%s, row_version=row_version+1, '
                                'updated_at=now() WHERE id=%s', (resulting, product_id))
                    cur.execute(
                        """INSERT INTO stock_movements
                           (product_id, delta, resulting_stock, cause, sale_id, actor_user_id)
                           VALUES (%s, %s, %s, 'sale', %s, %s)""",
                        (product_id, -qty, resulting, sale_id,
                         actor if isinstance(actor, int) else None))
            _audit(cur, actor, f'Venta V{sale_id:06d} por {total}')
    return {'ok': True, 'code': 'created', 'sale_id': sale_id,
            'total': float(total), 'created_at': row(sale)['created_at']}


def _product_cache(cur, product_id):
    cur.execute('SELECT * FROM products WHERE id=%s', (product_id,))
    return cur.fetchone()


def reverse_sale(url, *, sale_id, reason, actor, role='user'):
    """Reversión compensatoria auditada; sólo admin, con motivo, una sola vez."""
    if role != 'admin':
        return {'ok': False, 'code': FORBIDDEN,
                'message': 'Sólo un administrador puede revertir ventas'}
    if not (reason or '').strip():
        return {'ok': False, 'code': REASON_REQUIRED,
                'message': 'Indique el motivo de la reversión'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM sales WHERE id=%s FOR UPDATE', (sale_id,))
            sale = cur.fetchone()
            if not sale:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Venta no encontrada'}
            if sale['status'] == 'reversed':
                return {'ok': False, 'code': ALREADY_REVERSED,
                        'message': 'La venta ya estaba revertida'}
            cur.execute('SELECT * FROM sale_lines WHERE sale_id=%s '
                        'ORDER BY product_id', (sale_id,))
            lines = cur.fetchall()
            for line in lines:
                if line['kind'] == 'producto':
                    # CORR01/R10: locks en orden determinista también aquí.
                    cur.execute('SELECT pg_advisory_xact_lock(%s, %s)',
                                (ADVISORY_NAMESPACE, line['product_id']))
                    cur.execute('SELECT stock FROM products WHERE id=%s',
                                (line['product_id'],))
                    resulting = cur.fetchone()['stock'] + line['qty']
                    cur.execute('UPDATE products SET stock=%s, row_version=row_version+1, '
                                'updated_at=now() WHERE id=%s',
                                (resulting, line['product_id']))
                    cur.execute(
                        """INSERT INTO stock_movements
                           (product_id, delta, resulting_stock, cause, sale_id, actor_user_id)
                           VALUES (%s,%s,%s,'reversal',%s,%s)""",
                        (line['product_id'], line['qty'], resulting, sale_id,
                         actor if isinstance(actor, int) else None))
            cur.execute(
                """UPDATE sales SET status='reversed', reversed_at=now(),
                   reverse_reason=%s WHERE id=%s""",
                (reason.strip()[:300], sale_id))
            _audit(cur, actor, f'Reversión de venta V{sale_id:06d}: {reason.strip()[:120]}')
    return {'ok': True, 'code': 'reversed', 'sale_id': sale_id}


def list_sales(url, *, limit=50, q='', branch_ids=None):
    pattern = f'%{(q or "").strip().lower()}%'
    branch_clause = ''
    params = [pattern, pattern, f'%{(q or "").strip()}%']
    if branch_ids is not None:
        if not branch_ids:
            return []
        marks = ', '.join(['%s'] * len(branch_ids))
        branch_clause = f' AND s.branch_id IN ({marks})'
        params.extend(sorted(set(int(b) for b in branch_ids)))
    with transaction(url) as conn:
        with conn.cursor() as cur:
            # Mejora UI acotada (E05 llegó después): nombres snapshot desde
            # sale_lines; NO introduce estados de entrega/pago de E05.
            cur.execute(
                f"""SELECT s.*, c.full_name AS contact_name,
                          (SELECT count(*) FROM sale_lines l
                           WHERE l.sale_id = s.id) AS lines,
                          (SELECT string_agg(DISTINCT l.product_name, ', ')
                           FROM sale_lines l WHERE l.sale_id = s.id) AS item_names,
                          b.name AS branch_name
                   FROM sales s
                   LEFT JOIN contacts c ON c.id = s.contact_id
                   LEFT JOIN branches b ON b.id = s.branch_id
                   WHERE (%s = '%%' OR lower(coalesce(c.full_name,'')) LIKE %s
                          OR s.id::text LIKE %s){branch_clause}
                   ORDER BY s.id DESC LIMIT %s""",
                params + [max(1, min(int(limit), 200))])
            return [row(r) for r in cur.fetchall()]


def sale_detail(url, sale_id):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT s.*, c.full_name AS contact_name FROM sales s
                   LEFT JOIN contacts c ON c.id = s.contact_id WHERE s.id=%s""",
                (sale_id,))
            sale = cur.fetchone()
            if not sale:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Venta no encontrada'}
            cur.execute('SELECT * FROM sale_lines WHERE sale_id=%s ORDER BY id',
                        (sale_id,))
            lines = [row(r) for r in cur.fetchall()]
    return {'ok': True, 'sale': row(sale), 'lines': lines}
