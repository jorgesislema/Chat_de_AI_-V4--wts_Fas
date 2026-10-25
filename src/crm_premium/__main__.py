"""CLI del CRM Premium: migrar, crear-admin, seed-demo y arrancar.

Uso (desde la raíz del proyecto, con el entorno virtual activado):
    python -m crm_premium migrate
    python -m crm_premium create-admin <usuario>
    python -m crm_premium seed-demo
    python -m crm_premium run [--host 127.0.0.1] [--port 8055]
"""
import argparse
import getpass
import json
import os
import random
import sys
import uuid
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_env():
    load_dotenv(REPO_ROOT / '.env')


def _db_url():
    url = os.environ.get('DATABASE_URL')
    if not url:
        sys.exit('DATABASE_URL no configurada: copie .env.example a .env y ajústelo.')
    return url


def cmd_migrate(args):
    from .infrastructure.persistence.migrations import apply_all
    applied = apply_all(_db_url())
    print('Migraciones aplicadas:', ', '.join(applied) if applied else '(nada pendiente)')


def cmd_create_admin(args):
    from .modules.identity import service as identity
    username = args.username or input('Usuario administrador: ').strip()
    password = getpass.getpass('Contraseña (mínimo 12 caracteres): ')
    confirm = getpass.getpass('Repita la contraseña: ')
    if password != confirm:
        sys.exit('Las contraseñas no coinciden.')
    result = identity.create_user(_db_url(), username=username, password=password,
                                  full_name=args.full_name or 'Administración',
                                  role='admin')
    if not result['ok']:
        sys.exit(f"Error: {result['message']}")
    user = result['user']
    print(f"Administrador creado: {user['username']} (id={user['id']})")


DEMO_RESOURCES = [
    ('Dra. Ana Torres', 'Odontología general'),
    ('Dr. Luis Peña', 'Ortodoncia'),
    ('Dra. Marta Salas', 'Endodoncia'),
]
DEMO_CONTACT_NAMES = [
    'María González', 'Carlos Pérez', 'Lucía Fernández', 'Juan Rodríguez',
    'Sofía Martínez', 'Diego López', 'Valentina Ramírez', 'Andrés Silva',
    'Camila Rojas', 'Mateo Vargas', 'Isabella Castillo', 'Sebastián Mora',
    'Renata Cruz', 'Nicolás Ibarra', 'Emilia Ríos', 'Samuel Navas',
    'Catalina Vera', 'Gabriel Suárez', 'Helena Pardo', 'Tomás Aguirre',
    'Daniela Cuesta', 'Bruno Salazar', 'Paula Miranda', 'Adrián Fuentes',
    'Noelia Campos', 'Iván Ortega', 'Alba Delgado', 'Rubén Cabrera',
    'Sara Herrera', 'Hugo Montes', 'Elena Bravo', 'Marcos Cano',
    'Ariadna Ponce', 'Óscar León', 'Nuria Blanco', 'Álvaro Rey',
    'Rocío Vidal', 'Sergio Pascual', 'Laura Serrano', 'Pablo Gil',
]
DEMO_TITLES = ['Limpieza dental', 'Valoración inicial', 'Consulta de control',
               'Ortodoncia — ajuste', 'Endodoncia — sesión', 'Urgencia dental',
               'Blanqueamiento', 'Presupuesto implantología']


DEMO_CATALOG = [
    # (sku, nombre, tipo, categoria, precio, costo, stock, min)
    ('SRV-VALOR', 'Valoración inicial', 'servicio', 'Consulta', 25.00, 0, 0, 0),
    ('SRV-LIMPIEZA', 'Limpieza dental', 'servicio', 'Higiene', 40.00, 10.00, 0, 0),
    ('SRV-CONTROL', 'Consulta de control', 'servicio', 'Consulta', 20.00, 0, 0, 0),
    ('SRV-ORTO', 'Ortodoncia — ajuste mensual', 'servicio', 'Ortodoncia', 35.00, 5.00, 0, 0),
    ('SRV-ENDO', 'Endodoncia — sesión', 'servicio', 'Endodoncia', 90.00, 25.00, 0, 0),
    ('SRV-BLANQ', 'Blanqueamiento', 'servicio', 'Estética', 120.00, 40.00, 0, 0),
    ('SRV-URGEN', 'Urgencia dental', 'servicio', 'Urgencias', 30.00, 0, 0, 0),
    ('SRV-IMPLA', 'Presupuesto implantología', 'servicio', 'Implantes', 50.00, 0, 0, 0),
    ('SRV-EXTRA', 'Extracción simple', 'servicio', 'Cirugía', 60.00, 15.00, 0, 0),
    ('SRV-FLUOR', 'Aplicación de flúor', 'servicio', 'Higiene', 18.00, 4.00, 0, 0),
    ('PRD-PASTA', 'Pasta dental sensibilidad 75ml', 'producto', 'Higiene oral', 8.50, 3.20, 60, 10),
    ('PRD-CEPILLO', 'Cepillo eléctrico recarga', 'producto', 'Higiene oral', 45.00, 22.00, 25, 5),
    ('PRD-HILOS', 'Caja de hilo dental 50m', 'producto', 'Higiene oral', 6.00, 2.10, 80, 15),
    ('PRD-COLUTORIO', 'Colutorio clorhexidina 500ml', 'producto', 'Higiene oral', 12.00, 5.50, 40, 8),
    ('PRD-GUANTES', 'Guantes de nitrilo (caja 100)', 'producto', 'Insumos', 15.00, 8.00, 30, 6),
    ('PRD-MASCARILLAS', 'Mascarillas (caja 50)', 'producto', 'Insumos', 9.00, 4.00, 8, 10),
    ('PRD-PROTECTOR', 'Protector bucal deportivo', 'producto', 'Ortodoncia', 35.00, 14.00, 12, 4),
    ('PRD-MANTENIMIENTO', 'Kit post-bleanqueamiento', 'producto', 'Estética', 28.00, 11.00, 18, 5),
]

DEMO_KNOWLEDGE = [
    ('Políticas de la clínica (demo)',
     'Las citas deben confirmarse con 24 horas de anticipación. Las cancelaciones '
     'con menos de 4 horas de aviso pueden tener cargo del 30%. Los tratamientos '
     'de ortodoncia incluyen ajustes mensuales por 12 meses.'),
    ('Horario de atención (demo)',
     'Atención de lunes a viernes de 08:00 a 17:00 y sábados de 08:00 a 13:00. '
     'Las urgencias se atienden por orden de llegada con previa llamada.'),
    ('Garantía de tratamientos (demo)',
     'Los empastes tienen garantía de 6 meses; endodoncias, 12 meses, sujeto a '
     'asistencia a los controles indicados por el profesional.'),
]


def seed_commerce(url, tz, days=60):
    """Catálogo, ventas históricas sintéticas y base de conocimiento demo."""
    from .infrastructure.persistence.db import transaction
    from .modules.commerce import service as commerce
    products = []
    for sku, name, kind, category, price, cost, stock, minimum in DEMO_CATALOG:
        result = commerce.create_product(
            url, sku=sku, name=name, kind=kind, category=category,
            price=price, cost=cost if cost else None, stock=stock,
            min_stock=minimum, actor='seed-demo')
        assert result['ok'], result
        products.append(result['product'])
    sales_made = 0
    contact_ids = []
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contacts ORDER BY id LIMIT 40")
            contact_ids = [r['id'] for r in cur.fetchall()]
    today_local = datetime.now(timezone.utc).astimezone(tz).date()
    services = [p for p in products if p['kind'] == 'servicio']
    goods = [p for p in products if p['kind'] == 'producto']
    for offset in range(-days, 1):
        day = today_local + timedelta(days=offset)
        for _ in range(random.randint(1, 4)):
            lines = []
            for _ in range(random.randint(1, 3)):
                product = random.choices(services + goods,
                                         weights=[6] * len(services) + [2] * len(goods))[0]
                lines.append({'product_id': product['id'],
                              'qty': random.randint(1, 2)})
            commerce.create_sale(
                url, lines=lines,
                payment_method=random.choice(['efectivo', 'tarjeta', 'transferencia']),
                contact_id=random.choice(contact_ids) if contact_ids else None,
                actor='seed-demo', is_demo=True,
                note='Venta DEMO sintética')
            sales_made += 1
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM knowledge_docs WHERE title LIKE '%demo%'")
            if not cur.fetchone()['n']:
                for title, content in DEMO_KNOWLEDGE:
                    cur.execute('INSERT INTO knowledge_docs (title, content) VALUES (%s,%s)',
                                (title, content))
    return len(products), sales_made


def cmd_seed_demo(args):
    """Carga datos 100% sintéticos marcados origin='demo' para explorar el sistema."""
    from .infrastructure.persistence.db import transaction
    from .modules.organization import service as organization
    from .modules.scheduling import service as scheduling
    url = _db_url()
    if not args.yes and input(
            '¿Cargar datos DEMO sintéticos en la base configurada? (s/N): '
    ).strip().lower() not in ('s', 'si', 'sí'):
        sys.exit('Cancelado.')
    random.seed(args.seed)
    zone = os.environ.get('CRM_ZONE', 'America/Guayaquil')
    tz = ZoneInfo(zone)
    organization.ensure(url, name='Clínica Dental Sonrisa (demo)', zone=zone)

    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM contacts WHERE notes LIKE '%DEMO%'")
            agenda_seeded = cur.fetchone()['n'] > 0
    resources = []
    if not agenda_seeded:
        for name, specialty in DEMO_RESOURCES:
            result = scheduling.create_resource(url, name=name, specialty=specialty)
            resources.append(result['resource'])
    else:
        print('Agenda demo ya cargada; se omite (no se duplica).')

    now_local = datetime.now(timezone.utc).astimezone(tz)
    today_local = now_local.date()
    created = 0
    contact_ids = []
    if agenda_seeded:
        with transaction(url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM contacts WHERE notes LIKE '%DEMO%' ORDER BY id")
                contact_ids = [r['id'] for r in cur.fetchall()]
    else:
        with transaction(url) as conn:
            with conn.cursor() as cur:
                for index, name in enumerate(DEMO_CONTACT_NAMES):
                    cur.execute(
                        """INSERT INTO contacts (full_name, phone, notes, channel)
                           VALUES (%s, %s, %s, 'web') RETURNING id""",
                        (name, f'+5939{200000 + index * 137 % 8000000:07d}',
                         'Contacto DEMO sintético'))
                    contact_ids.append(cur.fetchone()['id'])

                for offset_days in range(-21, 22):
                    day = today_local + timedelta(days=offset_days)
                    base_local = datetime.combine(day, time(0, 0))
                    for resource in resources:
                        taken = set()
                        for _ in range(random.randint(4, 7)):
                            hour = random.randint(8, 16)
                            if hour in taken:
                                continue
                            taken.add(hour)
                            # Horas 8-16: fuera de los saltos DST habituales (01-03).
                            start_utc = base_local.replace(
                                hour=hour, tzinfo=tz, fold=0).astimezone(timezone.utc)
                            duration = random.choice([30, 45, 60])
                            end_utc = start_utc + timedelta(minutes=duration)
                            if offset_days < 0:
                                status = random.choices(
                                    ['attended', 'no_show', 'cancelled'],
                                    weights=[75, 15, 10])[0]
                            elif offset_days == 0:
                                status = random.choice(['pending', 'confirmed'])
                            else:
                                status = random.choices(
                                    ['pending', 'confirmed', 'cancelled'],
                                    weights=[45, 45, 10])[0]
                            cur.execute(
                                """INSERT INTO appointments
                                   (resource_id, contact_id, title, start_utc, end_utc,
                                    event_id, origin, channel, operational_status)
                                   VALUES (%s,%s,%s,%s,%s,%s,'demo','web',%s)
                                   RETURNING id""",
                                (resource['id'], random.choice(contact_ids),
                                 random.choice(DEMO_TITLES), start_utc, end_utc,
                                 uuid.uuid4().hex, status))
                            appt_id = cur.fetchone()['id']
                            cur.execute(
                                """INSERT INTO appointment_history
                                   (appointment_id, action, actor_label, detail)
                                   VALUES (%s,'creacion','seed-demo',%s::jsonb)""",
                                (appt_id, json.dumps(
                                    {'start': start_utc.isoformat(),
                                     'end': end_utc.isoformat(),
                                     'status': status})))
                            if status != 'cancelled' and random.random() < 0.12:
                                cur.execute(
                                    """INSERT INTO appointment_notes
                                       (appointment_id, author_user_id, body)
                                       VALUES (%s, NULL, %s)""",
                                    (appt_id,
                                     'Nota DEMO: paciente prefiere turno por la mañana.'))
                            created += 1

    # Sección comercio: catálogo, ventas sintéticas y conocimiento (idempotente).
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM products WHERE sku LIKE 'SRV-%' "
                        "OR sku LIKE 'PRD-%'")
            commerce_seeded = cur.fetchone()['n'] > 0
    if commerce_seeded:
        print('Comercio demo ya cargado; se omite (no se duplica).')
    else:
        products_n, sales_n = seed_commerce(url, tz)
        print(f'Comercio demo: {products_n} artículos, {sales_n} ventas sintéticas.')
    print(f'Demo cargado: {len(resources)} recursos nuevos, {len(contact_ids)} '
          f'contactos demo, {created} citas sintéticas nuevas.')


def cmd_rotate_password(args):
    """CORR01B/R01: rotación interactiva segura. La contraseña NUNCA va en
    argumentos ni historial: se lee con getpass y se confirma dos veces."""
    from .modules.identity import service as identity
    url = _db_url()
    username = args.username or input('Usuario a rotar: ').strip()
    password = getpass.getpass('Nueva contraseña (mínimo 12 caracteres): ')
    confirm = getpass.getpass('Repita la nueva contraseña: ')
    if password != confirm:
        sys.exit('Las contraseñas no coinciden; no se cambió nada.')
    if not password:
        sys.exit('Contraseña vacía; no se cambió nada.')
    result = identity.admin_reset_password(url, username=username,
                                            new_password=password)
    if not result['ok']:
        sys.exit(f'Error: {result["message"]}')
    print(f'Contraseña de {username} rotada; sus sesiones quedaron revocadas. '
          f'No se imprime la contraseña en ningún momento.')


def cmd_rebuild_bi(args):
    from .modules.analytics import service as analytics
    from .modules.organization import service as organization
    url = _db_url()
    profile = organization.get(url)
    if profile is None:
        profile = organization.ensure(url)
    result = analytics.rebuild_bi(url, profile['zone'])
    print(f"Modelo estrella reconstruido: {result['citas']} citas, "
          f"{result['lineas_venta']} líneas de venta (zona {result['zona']}).")


def cmd_run(args):
    from .entrypoints.web.app import create_app
    app = create_app()
    print(f'CRM Premium en http://{args.host}:{args.port} (Ctrl+C para detener)')
    app.run(host=args.host, port=args.port, debug=False)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='crm_premium',
                                     description='CRM Premium — edición 2000+')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('migrate', help='Aplica migraciones pendientes')

    admin = sub.add_parser('create-admin', help='Crea un usuario administrador')
    admin.add_argument('username', nargs='?')
    admin.add_argument('--full-name', default='')

    seed = sub.add_parser('seed-demo', help='Carga datos demo sintéticos')
    seed.add_argument('--seed', type=int, default=42)
    seed.add_argument('--yes', action='store_true')

    run = sub.add_parser('run', help='Arranca el servidor web local')
    run.add_argument('--host', default='127.0.0.1')
    run.add_argument('--port', type=int, default=8055)

    sub.add_parser('rebuild-bi', help='Reconstruye el modelo estrella analítico')

    rotate = sub.add_parser('rotate-password',
                            help='Rota una contraseña de forma interactiva '
                                 '(getpass; nunca en argumentos)')
    rotate.add_argument('username', nargs='?')

    args = parser.parse_args(argv)
    _load_env()
    {'migrate': cmd_migrate, 'create-admin': cmd_create_admin,
     'seed-demo': cmd_seed_demo, 'run': cmd_run,
     'rebuild-bi': cmd_rebuild_bi,
     'rotate-password': cmd_rotate_password}[args.command](args)


if __name__ == '__main__':
    main()
