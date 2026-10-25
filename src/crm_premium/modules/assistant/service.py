"""Asistente interno: preguntas sobre la base del negocio con auditoría.

Diseño honesto de esta fase (F15 núcleo): asistente determinista por
herramientas — detecta la intención, ejecuta una consulta parametrizada y
responde con el dato y su origen. NO hay modelo de lenguaje externo todavía
(llegará con la fase de proveedores IA / failover F22 y sus evals F24), pero
la arquitectura de herramientas + registro ya es la definitiva:

- Cada pregunta/respuesta queda en ``assistant_log`` (usuario, intención,
  herramienta, respuesta y datos): audita qué se preguntó y con qué se
  respondió.
- Sin SQL arbitrario ni escrituras: sólo SELECT acotados por herramienta.
- RAG básico por palabras clave sobre ``knowledge_docs`` (los embeddings
  llegan con la fase de conocimiento F12/F15 completa).
"""
import re
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Json

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row
from ...shared.timeutil import resolve_zone

TOOLS = ('ventas', 'top_productos', 'citas_hoy', 'proximas_citas', 'stock_bajo',
         'precio', 'asistencia', 'conocimiento', 'no_disponible', 'ayuda')


def _local_now(zone):
    tz = resolve_zone(zone)
    return datetime.now(timezone.utc).astimezone(tz)


def _money(value):
    return f'{float(value):,.2f}'


# ------------------------------------------------------------- herramientas

def _tool_resumen_ventas(url, zone, periodo, include_demo=False,
                         branch_ids=None):
    """CORR01/R02: la reversión cuenta en su propio momento, no reescribe la
    venta. CORR01/R08: datos demo excluidos salvo opt-in explícito."""
    now_local = _local_now(zone)
    if periodo == 'hoy':
        lo = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        label = 'hoy'
    elif periodo == 'semana':
        lo = (now_local - timedelta(days=now_local.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
        label = 'esta semana'
    else:
        lo = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = 'este mes'
    demo = '' if include_demo else ' AND NOT es_demo'
    sede = ''
    sede_params = []
    if branch_ids is not None:
        if not branch_ids:
            return ('No tiene sedes asignadas: no hay datos dentro de su '
                    'ámbito. Origen: límite de alcance por sede.'), \
                {'neto': 0, 'ventas': 0, 'periodo': periodo}
        marks = ', '.join(['%s'] * len(branch_ids))
        sede = f' AND branch_id IN ({marks})'
        sede_params.extend(sorted(set(int(b) for b in branch_ids)))
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT coalesce(sum(importe),0) AS neto,
                           count(*) FILTER (WHERE es_confirmada) AS ventas
                    FROM (
                        SELECT total AS importe, created_at AS momento,
                               (status = 'confirmed') AS es_confirmada,
                               is_demo AS es_demo
                        FROM sales WHERE 1=1{sede}
                        UNION ALL
                        SELECT -total AS importe,
                               coalesce(reversed_at, created_at) AS momento,
                               false, is_demo
                        FROM sales WHERE status = 'reversed'{sede}
                    ) movimientos
                    WHERE momento >= %s{demo}""",
                (*sede_params, *sede_params, lo.astimezone(timezone.utc)))
            found = cur.fetchone()
    neto = float(found['neto'])
    demo_note = '' if include_demo else ' (datos demo excluidos)'
    answer = (f'Ventas netas {label}: {_money(neto)} en {found["ventas"]} venta(s) '
              f'confirmada(s); las anulaciones restan en su fecha propia'
              f'{demo_note}. Origen: tabla sales, desde {lo:%Y-%m-%d %H:%M} ({zone}).')
    return answer, {'neto': neto, 'ventas': found['ventas'], 'periodo': periodo}


def _tool_top(url, zone, kind, include_demo=False, branch_ids=None):
    demo = '' if include_demo else ' AND NOT s.is_demo'
    sede = ''
    sede_params = [kind]
    if branch_ids is not None:
        if not branch_ids:
            return ('No tiene sedes asignadas: sin datos en su ámbito.',
                    {'items': []})
        marks = ', '.join(['%s'] * len(branch_ids))
        sede = f' AND s.branch_id IN ({marks})'
        sede_params.extend(sorted(set(int(b) for b in branch_ids)))
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT l.product_name, sum(l.qty) AS unidades,
                           sum(l.line_total) AS neto
                    FROM sale_lines l JOIN sales s ON s.id = l.sale_id
                    JOIN products p ON p.id = l.product_id
                    WHERE p.kind = %s AND s.created_at >= now() - interval '30 days'
                      AND s.status = 'confirmed'{demo}{sede}
                    GROUP BY l.product_name
                    ORDER BY neto DESC NULLS LAST LIMIT 5""", sede_params)
            rows = [row(r) for r in cur.fetchall()]
    if not rows:
        return ('Aún no hay ventas registradas en los últimos 30 días para ese '
                'tipo de artículo. Origen: sale_lines + sales + products.'), {'items': []}
    noun = 'tratamientos/servicios' if kind == 'servicio' else 'productos'
    lines = [f"{i + 1}. {r['product_name']} — {r['unidades']} u · "
             f"{_money(r['neto'])}" for i, r in enumerate(rows)]
    answer = (f'Top {noun} por ingresos (30 días, ventas confirmadas):\n'
              + '\n'.join(lines)
              + '\nOrigen: sale_lines de los últimos 30 días.')
    return answer, {'items': rows}


def _tool_citas_hoy(url, zone, include_demo=False):
    now_local = _local_now(zone)
    lo = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    hi = lo + timedelta(days=1)
    demo = '' if include_demo else " AND origin <> 'demo'"
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT operational_status, count(*) AS n FROM appointments
                    WHERE start_utc >= %s AND start_utc < %s{demo}
                    GROUP BY operational_status""",
                (lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)))
            counts = {r['operational_status']: r['n'] for r in cur.fetchall()}
    total = sum(counts.values())
    detail = ', '.join(f"{v} {k}" for k, v in sorted(counts.items())) or 'ninguna'
    answer = (f'Hoy hay {total} cita(s) en la agenda ({detail}). '
              f'Origen: appointments por día local {lo:%Y-%m-%d} en zona {zone}.')
    return answer, {'total': total, 'por_estado': counts}


def _tool_proximas(url, zone, limit=5, include_demo=False):
    demo = '' if include_demo else " AND a.origin <> 'demo'"
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT a.title, r.name AS resource, a.start_utc
                    FROM appointments a JOIN resources r ON r.id = a.resource_id
                    WHERE a.start_utc >= now()
                      AND a.operational_status IN ('pending','confirmed'){demo}
                    ORDER BY a.start_utc LIMIT %s""", (limit,))
            rows = cur.fetchall()
    if not rows:
        return 'No hay próximas citas programadas. Origen: appointments.', {'items': []}
    tz = resolve_zone(zone)
    lines = [f"· {r['start_utc'].astimezone(tz):%d %b %H:%M} — {r['title']} ({r['resource']})"
             for r in rows]
    return ('Próximas citas:\n' + '\n'.join(lines)
            + f'\nOrigen: appointments futuras, zona {zone}.'), \
        {'items': [{'titulo': r['title'], 'recurso': r['resource'],
                    'inicio': row(r)['start_utc']} for r in rows]}


def _tool_stock_bajo(url, zone, branch_ids=None):
    from ..commerce import service as commerce
    items = [i for i in commerce.low_stock_products(url)
             if branch_ids is None or i.get('branch_id') is None
             or i['branch_id'] in branch_ids]
    if not items:
        return ('Ningún producto está en o bajo su mínimo. '
                'Origen: products con stock <= min_stock.'), {'items': []}
    lines = [f"· {i['name']} ({i['sku']}): stock {i['stock']} / mínimo {i['min_stock']}"
             for i in items]
    return ('Productos en o bajo el mínimo:\n' + '\n'.join(lines)
            + '\nOrigen: products (stock <= min_stock).'), {'items': items}


def _tool_precio(url, zone, text):
    from ..commerce import service as commerce
    product = commerce.find_product_by_text(url, text)
    if not product:
        return (f'No encontré un artículo activo que coincida con «{text}». '
                'Pruebe con el nombre o el SKU. Origen: products.'), {'product': None}
    noun = 'Tratamiento' if product['kind'] == 'servicio' else 'Producto'
    answer = (f"{noun} {product['name']} ({product['sku']}): precio actual "
              f"{_money(product['price'])}"
              + (f", stock {product['stock']}" if product['kind'] == 'producto' else '')
              + '. Origen: products.')
    return answer, {'product': product}


def _tool_asistencia(url, zone):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT count(*) FILTER (WHERE operational_status='attended') AS attended,
                          count(*) FILTER (WHERE operational_status='no_show') AS no_show
                   FROM appointments
                   WHERE start_utc >= now() - interval '30 days'""")
            found = cur.fetchone()
    closed = found['attended'] + found['no_show']
    rate = round(found['attended'] / closed * 100, 1) if closed else None
    answer = ('Sin citas cerradas en 30 días para calcular asistencia.'
              if rate is None else
              f'Asistencia de 30 días: {rate}% ({found["attended"]} atendidas, '
              f'{found["no_show"]} no asistieron). '
              'Origen: appointments cerradas en 30 días.')
    return answer, {'rate': rate, 'attended': found['attended'],
                    'no_show': found['no_show']}


def _tool_no_disponible(url, zone, question):
    """CORR01/R08: consultas financieras sin soporte real se declaran no
    disponibles; nunca se disfrazan de ventas ni se inventan cobros."""
    return ('Esa consulta es sobre cobros/pagos: función no disponible en esta '
            'fase. El sistema registra ventas con pago al momento, pero no '
            'lleva movimientos de cobro independientes, abonos ni cartera; '
            'ventas y cobros son conceptos distintos y no voy a responder '
            'una con datos de la otra. Pregunte por «ventas de '
            'hoy/semana/mes» o solicite la fase de cobros (F11 completa). '
            'Origen: límite declarado del núcleo.'), \
        {'limite': 'cobros_no_disponibles'}


def _tool_conocimiento(url, zone, question):
    """RAG básico por palabras clave (CORR01: cada palabra se busca en
    contenido O título; antes sólo la primera palabra cruzaba al título)."""
    stop = {'cuál', 'como', 'para', 'donde', 'cuando', 'sobre', 'que'}
    words = [w for w in re.findall(r'[a-záéíóúñ]{4,}', question.lower())
             if w not in stop]
    with transaction(url) as conn:
        with conn.cursor() as cur:
            if words:
                per_word = '(lower(content) LIKE %s OR lower(title) LIKE %s)'
                clause = ' OR '.join([per_word] * len(words))
                params = []
                for word in words:
                    params.extend([f'%{word}%', f'%{word}%'])
                cur.execute(
                    f'SELECT id, title, content FROM knowledge_docs '
                    f'WHERE {clause} ORDER BY id LIMIT 2', params)
            else:
                cur.execute('SELECT id, title, content FROM knowledge_docs '
                            'ORDER BY id LIMIT 2')
            docs = cur.fetchall()
    if not docs:
        return ('No encontré documentos internos sobre eso. '
                'Origen: knowledge_docs.'), {'docs': []}
    lines = [f'【{d["title"]}】 {d["content"][:280]}' for d in docs]
    return ('De la base de conocimiento interna:\n' + '\n—\n'.join(lines)
            + '\nOrigen: knowledge_docs (búsqueda por palabras clave).'), \
        {'docs': [{'titulo': d['title']} for d in docs]}


def _tool_ayuda():
    return ('Puedo responder con datos reales del negocio:\n'
            '· «ventas de hoy / de la semana / del mes»\n'
            '· «tratamientos más vendidos» · «productos más vendidos»\n'
            '· «citas de hoy» · «próximas citas»\n'
            '· «stock bajo» · «precio de limpieza dental»\n'
            '· «asistencia» · «políticas / horario de atención»\n'
            'Cada respuesta indica su origen y queda registrada en la auditoría.'), \
        {'capabilities': TOOLS[:-1]}


# ------------------------------------------------------------- intención

def _detect(question):
    q = question.lower()
    # CORR01/R08: cobros/abonos/pagos/recaudación son consultas de COBRO, no
    # de venta; se declaran no disponibles en lugar de disfrazarse.
    if re.search(r'cobros?|cobranza|abonos?|pagos?|recaudaci[oó]n', q):
        return 'no_disponible', None
    if re.search(r'tratamiento|servicio', q) and re.search(r'vend|top|más|mas', q):
        return 'top_productos', 'servicio'
    if re.search(r'producto', q) and re.search(r'vend|top|más|mas|rotan', q):
        return 'top_productos', 'producto'
    if re.search(r'venta|ingreso|factur|dinero', q):
        if re.search(r'semana', q):
            return 'ventas', 'semana'
        if re.search(r'mes', q):
            return 'ventas', 'mes'
        return 'ventas', 'hoy'
    if re.search(r'citas?', q) and re.search(r'hoy', q):
        return 'citas_hoy', None
    if re.search(r'pr[oó]xim|siguientes|viene', q) and re.search(r'cita|agenda', q):
        return 'proximas_citas', None
    if re.search(r'stock|inventario|existencia', q) and re.search(
            r'bajo|baja|falt|agot|m[ií]nim', q):
        return 'stock_bajo', None
    if re.search(r'precio|cuesta|vale', q):
        match = re.search(r'(?:precio de|precio|cuesta|vale)\s+(.+)$', q)
        text = (match.group(1) if match else q).strip('¿? .,')
        return 'precio', (text or q)
    if re.search(r'asistencia|no asist|inasistencia', q):
        return 'asistencia', None
    if re.search(r'pol[ií]tica|documento|horario|conoc|regla', q):
        return 'conocimiento', question
    return 'ayuda', None


def ask(url, *, question, user_id, zone='UTC', include_demo=False,
        branch_ids=None):
    """Responde una pregunta con una herramienta y registra la auditoría.

    CORR01/R04: ``user_id`` es identificación de auditoría; las herramientas
    sólo leen datos operativos con permisos implícitos de usuario autenticado
    (agregados). La vista global del historial exige rol admin en la ruta.
    """
    question = (question or '').strip()[:500]
    if not question:
        return {'ok': False, 'code': 'empty', 'message': 'Escriba una pregunta'}
    intent, arg = _detect(question)
    if intent == 'ventas':
        answer, data = _tool_resumen_ventas(url, zone, arg, include_demo,
                                            branch_ids=branch_ids)
    elif intent == 'top_productos':
        answer, data = _tool_top(url, zone, arg, include_demo,
                                 branch_ids=branch_ids)
    elif intent == 'citas_hoy':
        answer, data = _tool_citas_hoy(url, zone, include_demo)
    elif intent == 'proximas_citas':
        answer, data = _tool_proximas(url, zone, include_demo=include_demo)
    elif intent == 'stock_bajo':
        answer, data = _tool_stock_bajo(url, zone, branch_ids=branch_ids)
    elif intent == 'precio':
        answer, data = _tool_precio(url, zone, arg)
    elif intent == 'asistencia':
        answer, data = _tool_asistencia(url, zone)
    elif intent == 'conocimiento':
        answer, data = _tool_conocimiento(url, zone, arg)
    elif intent == 'no_disponible':
        answer, data = _tool_no_disponible(url, zone, question)
    else:
        answer, data = _tool_ayuda()
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO assistant_log
                   (user_id, question, intent, tool, answer, data)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING id, created_at""",
                (user_id, question, intent, intent, answer, Json(data)))
            saved = cur.fetchone()
    return {'ok': True, 'intent': intent, 'tool': intent, 'answer': answer,
            'data': data, 'logged_id': saved['id'],
            'at': row(saved)['created_at']}


def history(url, user_id=None, limit=50):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT l.*, u.username FROM assistant_log l
                   LEFT JOIN users u ON u.id = l.user_id
                   WHERE (%s::bigint IS NULL OR l.user_id = %s)
                   ORDER BY l.id DESC LIMIT %s""",
                (user_id, user_id, limit))
            return [row(r) for r in cur.fetchall()]
