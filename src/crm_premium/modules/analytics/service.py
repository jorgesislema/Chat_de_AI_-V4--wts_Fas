"""Analítica: modelo estrella (esquema bi) y consultas del panel.

ETL idempotente que reconstruye dimensiones y hechos en la zona del negocio
(fechas/horas locales). La operación nunca escribe en ``bi``; se reconstruye
bajo demanda (CLI o botón de administración). Consultas del panel leen bi y
devuelven series listas para los gráficos.
"""
from datetime import datetime, timedelta, timezone

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row
from ...shared.timeutil import resolve_zone

STATUS_KEYS = {'pending': 1, 'confirmed': 2, 'attended': 3, 'no_show': 4,
               'cancelled': 5}
STATUS_LABELS = {'pending': 'Pendiente', 'confirmed': 'Confirmada',
                 'attended': 'Atendida', 'no_show': 'No asistió',
                 'cancelled': 'Cancelada'}


def rebuild_bi(url, zone):
    """Reconstruye el esquema bi completo. Devuelve conteos del lote."""
    tz = resolve_zone(zone)
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('TRUNCATE bi.fact_venta_linea, bi.fact_cita, '
                        'bi.dim_contacto, bi.dim_producto, bi.dim_recurso, '
                        'bi.dim_estado, bi.dim_hora, bi.dim_fecha, bi.dim_sede '
                        'RESTART IDENTITY CASCADE')
            cur.execute(
                """SELECT LEAST(
                       COALESCE((SELECT min(start_utc) FROM appointments), now()),
                       COALESCE((SELECT min(created_at) FROM sales), now())) AS lo,
                       GREATEST(
                       COALESCE((SELECT max(start_utc) FROM appointments), now()),
                       COALESCE((SELECT max(created_at) FROM sales), now()),
                       now()) AS hi""")
            bounds = cur.fetchone()

            lo_local = bounds['lo'].astimezone(tz).date()
            hi_local = bounds['hi'].astimezone(tz).date()
            cur.execute(
                """INSERT INTO bi.dim_fecha
                   SELECT d::date,
                          extract(year FROM d)::int, extract(month FROM d)::int,
                          extract(day FROM d)::int,
                          (extract(isodow FROM d)::int - 1),
                          extract(week FROM d)::int,
                          to_char(d, 'TMMon')
                   FROM generate_series(%s::date, %s::date, interval '1 day') d""",
                (lo_local, hi_local))
            cur.execute(
                """INSERT INTO bi.dim_hora
                   SELECT h,
                          CASE WHEN h BETWEEN 6 AND 11 THEN 'mañana'
                               WHEN h BETWEEN 12 AND 17 THEN 'tarde'
                               WHEN h BETWEEN 18 AND 23 THEN 'noche'
                               ELSE 'madrugada' END
                   FROM generate_series(0, 23) h""")
            for code, key in STATUS_KEYS.items():
                cur.execute(
                    'INSERT INTO bi.dim_estado (estado_key, codigo, etiqueta) '
                    'VALUES (%s, %s, %s)', (key, code, STATUS_LABELS[code]))
            cur.execute(
                """INSERT INTO bi.dim_recurso (resource_id, nombre)
                   SELECT id, name FROM resources""")
            cur.execute(
                """INSERT INTO bi.dim_sede (branch_id, nombre)
                   SELECT id, name FROM branches""")
            cur.execute(
                """INSERT INTO bi.dim_producto (product_id, nombre, tipo, categoria, precio_actual)
                   SELECT id, name, kind, category, price FROM products""")
            cur.execute(
                """INSERT INTO bi.dim_contacto (contact_id, seudonimo)
                   SELECT id, 'contacto_' || id FROM contacts""")

            cur.execute(
                """INSERT INTO bi.fact_cita
                       (cita_id, fecha_key, hora_key, recurso_key, estado_key,
                        contacto_key, duracion_min, es_demo, sede_key)
                   SELECT a.id,
                          (a.start_utc AT TIME ZONE %s)::date,
                          extract(hour FROM (a.start_utc AT TIME ZONE %s))::int,
                          r.resource_key, e.estado_key, c.contact_key,
                          greatest(0, extract(epoch FROM (a.end_utc - a.start_utc)) / 60)::int,
                          (a.origin = 'demo'),
                          sd.branch_key
                   FROM appointments a
                   JOIN bi.dim_recurso r ON r.resource_id = a.resource_id
                   JOIN bi.dim_estado e ON e.codigo = a.operational_status
                   LEFT JOIN bi.dim_contacto c ON c.contact_id = a.contact_id
                   LEFT JOIN bi.dim_sede sd ON sd.branch_id = a.branch_id""",
                (zone, zone))
            # CORR01/R02: la venta revertida conserva su fila POSITIVA en su
            # fecha de creación y añade una fila COMPENSATORIA negativa en la
            # fecha de la reversión. El neto acumulado es 0, pero cada período
            # muestra lo que ocurrió en su momento, sin reescribir historia.
            # CORR01/R08: el costo es el snapshot de la línea (unit_cost),
            # NULL si era desconocido; nunca el costo actual del producto.
            cur.execute(
                """INSERT INTO bi.fact_venta_linea
                       (fecha_key, hora_key, product_key, contacto_key, unidades,
                        neto, costo_conocido, es_demo, es_reversa, sale_id,
                        sede_key)
                   SELECT (s.created_at AT TIME ZONE %s)::date,
                          extract(hour FROM (s.created_at AT TIME ZONE %s))::int,
                          p.product_key, c.contact_key, l.qty, l.line_total,
                          l.unit_cost * l.qty, s.is_demo, false, s.id,
                          sd.branch_key
                   FROM sale_lines l
                   JOIN sales s ON s.id = l.sale_id
                   JOIN bi.dim_producto p ON p.product_id = l.product_id
                   LEFT JOIN bi.dim_contacto c ON c.contact_id = s.contact_id
                   LEFT JOIN bi.dim_sede sd ON sd.branch_id = s.branch_id
                   UNION ALL
                   SELECT (coalesce(s.reversed_at, s.created_at) AT TIME ZONE %s)::date,
                          extract(hour FROM (coalesce(s.reversed_at, s.created_at)
                                             AT TIME ZONE %s))::int,
                          p.product_key, c.contact_key, -l.qty, -l.line_total,
                          -(l.unit_cost * l.qty), s.is_demo, true, s.id,
                          sd.branch_key
                   FROM sale_lines l
                   JOIN sales s ON s.id = l.sale_id
                   JOIN bi.dim_producto p ON p.product_id = l.product_id
                   LEFT JOIN bi.dim_contacto c ON c.contact_id = s.contact_id
                   LEFT JOIN bi.dim_sede sd ON sd.branch_id = s.branch_id
                   WHERE s.status = 'reversed'""",
                (zone, zone, zone, zone))
            cur.execute(
                """INSERT INTO bi.meta (key, value)
                   VALUES ('last_rebuild', now()::text)
                   ON CONFLICT (key) DO UPDATE
                   SET value = excluded.value, updated_at = now()""")
            cur.execute('SELECT count(*) AS n FROM bi.fact_cita')
            citas = cur.fetchone()['n']
            cur.execute('SELECT count(*) AS n FROM bi.fact_venta_linea')
            lineas = cur.fetchone()['n']
    return {'citas': citas, 'lineas_venta': lineas, 'zona': zone}


def last_rebuild(url):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value, updated_at FROM bi.meta WHERE key='last_rebuild'")
            found = cur.fetchone()
    if not found:
        return None
    return row(found)['updated_at']


def _days_bounds(url, zone, days):
    tz = resolve_zone(zone)
    now = datetime.now(timezone.utc).astimezone(tz)
    hi = now.date()
    lo = hi - timedelta(days=days - 1)
    return lo, hi


def overview(url, zone, days=30, include_demo=False, branch_ids=None):
    """Series y KPI del panel de analítica (leen el esquema bi).

    CORR01/R08: ``include_demo=False`` por defecto excluye las filas marcadas
    de demo; el modo demo es una opción visible de la interfaz.
    """
    lo, hi = _days_bounds(url, zone, days)
    demo_clause = '' if include_demo else ' AND NOT l.es_demo'
    sede_clause = ''
    sede_params = []
    if branch_ids is not None:
        if not branch_ids:
            branch_ids = [-1]
        marks = ', '.join(['%s'] * len(branch_ids))
        sede_clause = (' AND l.sede_key IN (SELECT branch_key FROM bi.dim_sede '
                       f'WHERE branch_id IN ({marks}))')
        sede_params.extend(sorted(set(int(b) for b in branch_ids)))
    sede_c = sede_clause.replace('l.sede_key', 'c.sede_key')
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT coalesce(sum(l.neto),0) AS neto,
                          coalesce(sum(l.unidades),0) AS unidades,
                          count(DISTINCT l.sale_id) FILTER (WHERE NOT l.es_reversa)
                              AS ventas
                   FROM bi.fact_venta_linea l
                   WHERE l.fecha_key BETWEEN %s AND %s{demo_clause}{sede_clause}""",
                (lo, hi, *sede_params))
            totals = cur.fetchone()

            # Tops separados por tipo (R08): una categoría ya no desaparece
            # porque la otra llene el límite global.
            tops = {}
            for kind in ('servicio', 'producto'):
                cur.execute(
                    f"""SELECT p.nombre, sum(l.unidades) AS unidades,
                               sum(l.neto) AS neto
                        FROM bi.fact_venta_linea l
                        JOIN bi.dim_producto p USING (product_key)
                        WHERE l.fecha_key BETWEEN %s AND %s AND p.tipo = %s
                              {demo_clause}{sede_clause}
                        GROUP BY p.nombre
                        ORDER BY neto DESC NULLS LAST LIMIT 8""",
                    (lo, hi, kind, *sede_params))
                tops[kind] = [row(r) for r in cur.fetchall()]

            cur.execute(
                f"""SELECT p.categoria, sum(l.neto) AS neto
                    FROM bi.fact_venta_linea l
                    JOIN bi.dim_producto p USING (product_key)
                    WHERE l.fecha_key BETWEEN %s AND %s
                          AND p.categoria IS NOT NULL{demo_clause}{sede_clause}
                    GROUP BY p.categoria ORDER BY neto DESC LIMIT 6""",
                (lo, hi, *sede_params))
            categories = [row(r) for r in cur.fetchall()]

            cur.execute(
                f"""SELECT l.fecha_key AS dia, sum(l.neto) AS neto,
                           sum(l.unidades) AS unidades
                    FROM bi.fact_venta_linea l
                    WHERE l.fecha_key BETWEEN %s AND %s{demo_clause}{sede_clause}
                    GROUP BY l.fecha_key ORDER BY l.fecha_key""",
                (lo, hi, *sede_params))
            per_day_raw = {r['dia']: (float(r['neto']), r['unidades'])
                           for r in cur.fetchall()}

            cur.execute(
                f"""SELECT c.hora_key AS hora, count(*) AS citas
                   FROM bi.fact_cita c
                   WHERE c.fecha_key BETWEEN %s AND %s
                     AND (%s OR NOT c.es_demo){sede_c}
                   GROUP BY c.hora_key ORDER BY c.hora_key""",
                (lo, hi, include_demo, *sede_params))
            hours_raw = {r['hora']: r['citas'] for r in cur.fetchall()}

            cur.execute(
                f"""SELECT l.hora_key AS hora, coalesce(sum(l.neto),0) AS neto
                    FROM bi.fact_venta_linea l
                    WHERE l.fecha_key BETWEEN %s AND %s{demo_clause}{sede_clause}
                    GROUP BY l.hora_key ORDER BY l.hora_key""",
                (lo, hi, *sede_params))
            sales_hours_raw = {r['hora']: float(r['neto']) for r in cur.fetchall()}

            cur.execute(
                f"""SELECT e.codigo, count(*) AS n
                   FROM bi.fact_cita c
                   JOIN bi.dim_estado e USING (estado_key)
                   WHERE c.fecha_key BETWEEN %s AND %s
                     AND (%s OR NOT c.es_demo){sede_c}
                   GROUP BY e.codigo""",
                (lo, hi, include_demo, *sede_params))
            status_counts = {r['codigo']: r['n'] for r in cur.fetchall()}

    # Serie diaria completa llenada en Python (R09/estabilidad): no depende
    # de que dim_fecha cubra la ventana.
    per_day = []
    cursor_day = lo
    while cursor_day <= hi:
        neto, unidades = per_day_raw.get(cursor_day, (0.0, 0))
        per_day.append({'dia': cursor_day.isoformat(), 'neto': neto,
                        'unidades': unidades})
        cursor_day += timedelta(days=1)

    neto = float(totals['neto'])
    ventas = totals['ventas']
    attended = status_counts.get('attended', 0)
    no_show = status_counts.get('no_show', 0)
    closed = attended + no_show
    return {
        'desde': lo.isoformat(), 'hasta': hi.isoformat(), 'dias': days,
        'zona': zone, 'incluye_demo': bool(include_demo),
        'sedes': branch_ids,
        'ultima_reconstruccion': last_rebuild(url),
        'kpis': {
            'ventas_netas': neto,
            'unidades': totals['unidades'],
            'num_ventas': ventas,
            'ticket_medio': round(neto / ventas, 2) if ventas else None,
            'asistencia_rate': round(attended / closed, 4) if closed else None,
        },
        'top_servicios': [
            {'label': item['nombre'], 'value': float(item['neto']),
             'unidades': item['unidades']} for item in tops['servicio']],
        'top_productos': [
            {'label': item['nombre'], 'value': float(item['neto']),
             'unidades': item['unidades']} for item in tops['producto']],
        'categorias': [
            {'label': item['categoria'] or 'Sin categoría',
             'value': float(item['neto'])} for item in categories],
        'ventas_por_dia': per_day,
        'horas_pico_citas': [
            {'hora': hour, 'citas': hours_raw.get(hour, 0)} for hour in range(24)],
        'horas_ventas': [
            {'hora': hour, 'neto': sales_hours_raw.get(hour, 0.0)}
            for hour in range(24)],
        'estados': [{'codigo': code, 'label': STATUS_LABELS[code],
                     'value': status_counts.get(code, 0)} for code in STATUS_LABELS],
    }
