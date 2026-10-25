"""Agenda: reglas de citas portadas de V3 sobre PostgreSQL."""
from datetime import datetime, timedelta, timezone

import pytest

from crm_premium.modules.scheduling import service as scheduling

ZONE = 'UTC'
FUTURE = '2027-03-10'


def _future_day(base='09'):
    return f'{FUTURE}T{base}:00'


def _future_iso(base='09'):
    return f'{FUTURE}T{base}:00:00+00:00'


def test_crear_y_detalle(db_url, org, resource, contact):
    result = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='Valoración', zone=ZONE,
        contact_id=contact['id'], actor='seed')
    assert result['ok'], result
    detail = scheduling.appointment_detail(db_url, appointment_id=result['appointment']['id'])
    assert detail['ok']
    assert detail['appointment']['contact_name'] == 'Cliente Prueba'
    actions = [h['action'] for h in detail['history']]
    assert 'creacion' in actions


def test_solape_detectado(db_url, org, resource):
    first = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='A', zone=ZONE)
    assert first['ok']
    second = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10:30'),
        end=_future_day('11:30'), title='B', zone=ZONE)
    assert not second['ok'] and second['code'] == 'overlap'
    # Toque en el borde (11:00–12:00 tras 10:00–11:00) es válido.
    third = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('11'),
        end=_future_day('12'), title='C', zone=ZONE)
    assert third['ok']


def test_concurrencia_mismo_hueco(db_url, org, resource):
    """Dos reservas simultáneas: exactamente una gana (bloqueo consultivo)."""
    import threading

    results = []
    barrier = threading.Barrier(2)

    def worker(tag):
        barrier.wait()
        results.append(scheduling.save_appointment(
            db_url, resource_id=resource['id'], start=_future_day('15'),
            end=_future_day('16'), title=f'Cita {tag}', zone=ZONE))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    won = [r for r in results if r['ok']]
    lost = [r for r in results if not r['ok']]
    assert len(won) == 1 and len(lost) == 1
    assert lost[0]['code'] == 'overlap'


def test_pasado_rango_y_titulo(db_url, org, resource):
    past = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start='2020-01-01T10:00',
        end='2020-01-01T11:00', title='X', zone=ZONE)
    assert not past['ok'] and past['code'] == 'past_datetime'
    inverted = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('12'),
        end=_future_day('11'), title='X', zone=ZONE)
    assert not inverted['ok'] and inverted['code'] == 'invalid_range'
    empty = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('12'),
        end=_future_day('13'), title='   ', zone=ZONE)
    assert not empty['ok'] and empty['code'] == 'invalid_title'


def test_recurso_inexistente_e_inactivo(db_url, org, resource):
    missing = scheduling.save_appointment(
        db_url, resource_id=99999, start=_future_day('10'),
        end=_future_day('11'), title='X', zone=ZONE)
    assert not missing['ok'] and missing['code'] == 'missing_resource'
    scheduling.create_resource(db_url, name='Inactivo', is_active=False)
    listing = scheduling.list_resources(db_url)
    inactive = [r for r in listing if r['name'] == 'Inactivo']
    # list_resources(only_active=True) no lo devuelve.
    assert inactive == []


def test_reprogramacion_version_y_conflicto(db_url, org, resource):
    created = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='Original', zone=ZONE)
    appt_id = created['appointment']['id']
    version = created['appointment']['row_version']

    stale = scheduling.reprogram_appointment(
        db_url, appointment_id=appt_id, start=_future_day('14'),
        end=_future_day('15'), title='Reprog', zone=ZONE, expected_version=version - 1)
    assert not stale['ok'] and stale['code'] == 'version_conflict'

    missing_version = scheduling.reprogram_appointment(
        db_url, appointment_id=appt_id, start=_future_day('14'),
        end=_future_day('15'), title='Reprog', zone=ZONE, expected_version=None)
    assert not missing_version['ok'] and missing_version['code'] == 'version_conflict'

    ok = scheduling.reprogram_appointment(
        db_url, appointment_id=appt_id, start=_future_day('14'),
        end=_future_day('15'), title='Reprog', zone=ZONE,
        expected_version=version)
    assert ok['ok'] and ok['appointment']['event_id'] == created['appointment']['event_id']
    assert ok['appointment']['operational_status'] == 'pending'


def test_confirmar_cancelar_asistencia(db_url, org, resource):
    created = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='Ciclo', zone=ZONE)
    appt_id = created['appointment']['id']
    version = created['appointment']['row_version']

    confirmed = scheduling.confirm_appointment(db_url, appointment_id=appt_id,
                                               expected_version=version)
    assert confirmed['ok']
    again = scheduling.confirm_appointment(db_url, appointment_id=appt_id,
                                           expected_version=version + 1)
    assert again['ok'] and again['idempotent']

    early = scheduling.mark_attendance(db_url, appointment_id=appt_id,
                                       outcome='attended', expected_version=version + 1)
    assert not early['ok'] and early['code'] == 'too_early'

    # Cancelar una confirmada antes del inicio es válido.
    cancelled = scheduling.cancel_appointment(db_url, appointment_id=appt_id,
                                              expected_version=version + 1,
                                              reason='Cliente no podrá')
    assert cancelled['ok'] and cancelled['appointment']['operational_status'] == 'cancelled'

    after_cancel = scheduling.confirm_appointment(
        db_url, appointment_id=appt_id, expected_version=version + 2)
    assert not after_cancel['ok'] and after_cancel['code'] == 'invalid_transition'
    attend_cancelled = scheduling.mark_attendance(
        db_url, appointment_id=appt_id, outcome='attended',
        expected_version=version + 2)
    assert not attend_cancelled['ok'] and attend_cancelled['code'] == 'invalid_transition'

    # Cita aparte: asistencia tras el fin y bloqueo de cancelación ya cerrada.
    second = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('12'),
        end=_future_day('13'), title='Cierre', zone=ZONE)
    after = datetime.fromisoformat(f'{FUTURE}T13:00:00+00:00') + timedelta(minutes=1)
    closed = scheduling.mark_attendance(db_url, appointment_id=second['appointment']['id'],
                                        outcome='attended',
                                        expected_version=second['appointment']['row_version'],
                                        clock=after)
    assert closed['ok'] and closed['appointment']['operational_status'] == 'attended'
    reclose = scheduling.cancel_appointment(
        db_url, appointment_id=second['appointment']['id'],
        expected_version=second['appointment']['row_version'] + 1)
    assert not reclose['ok'] and reclose['code'] == 'already_closed'


def test_cancelacion_idempotente_y_no_resurreccion(db_url, org, resource):
    created = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='Anula', zone=ZONE)
    appt_id = created['appointment']['id']
    version = created['appointment']['row_version']
    first = scheduling.cancel_appointment(db_url, appointment_id=appt_id,
                                          expected_version=version)
    assert first['ok'] and not first['idempotent']
    second = scheduling.cancel_appointment(db_url, appointment_id=appt_id,
                                           expected_version=version + 1)
    assert second['ok'] and second['idempotent']
    revived = scheduling.admin_correct_status(
        db_url, appointment_id=appt_id, target='pending', reason='intento',
        expected_version=version + 1, role='admin')
    assert not revived['ok'] and revived['code'] == 'no_resurrection'


def test_correccion_admin_permisos_y_motivo(db_url, org, resource):
    created = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='Corr', zone=ZONE)
    appt_id = created['appointment']['id']
    no_role = scheduling.admin_correct_status(
        db_url, appointment_id=appt_id, target='confirmed', reason='x',
        expected_version=created['appointment']['row_version'], role='user')
    assert not no_role['ok'] and no_role['code'] == 'forbidden'
    no_reason = scheduling.admin_correct_status(
        db_url, appointment_id=appt_id, target='confirmed', reason=' ',
        expected_version=created['appointment']['row_version'], role='admin')
    assert not no_reason['ok'] and no_reason['code'] == 'reason_required'
    ok = scheduling.admin_correct_status(
        db_url, appointment_id=appt_id, target='confirmed', reason='Llamó para confirmar',
        expected_version=created['appointment']['row_version'], role='admin')
    assert ok['ok']


def test_notas_internas(db_url, org, admin_user, resource):
    created = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=_future_day('10'),
        end=_future_day('11'), title='Notas', zone=ZONE)
    appt_id = created['appointment']['id']
    empty = scheduling.add_note(db_url, appointment_id=appt_id, body='   ', author=admin_user["id"])
    assert not empty['ok'] and empty['code'] == 'note_required'
    anon = scheduling.add_note(db_url, appointment_id=appt_id, body='hola',
                               author='bot')
    assert not anon['ok'] and anon['code'] == 'forbidden'
    ok = scheduling.add_note(db_url, appointment_id=appt_id, body='Prefiere mañana',
                             author=admin_user["id"])
    assert ok['ok']
    detail = scheduling.appointment_detail(db_url, appointment_id=appt_id)
    assert detail['notes'][0]['body'] == 'Prefiere mañana'
    assert any(h['action'] == 'nota' for h in detail['history'])


def test_ventana_horario_aplica_y_excepcion_admin(db_url, org, resource):
    from crm_premium.modules.organization import service as organization
    organization.update(db_url, opening={'days': list(range(7)),
                                         'start': '08:00', 'end': '17:00'})
    profile = organization.get(db_url)
    policy = organization.build_window_policy(profile)
    outside = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=f'{FUTURE}T20:00',
        end=f'{FUTURE}T21:00', title='Tarde', zone=ZONE, window_policy=policy)
    assert not outside['ok'] and outside['code'] == 'outside_business_hours'
    user_with_reason = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=f'{FUTURE}T20:00',
        end=f'{FUTURE}T21:00', title='Tarde', zone=ZONE, window_policy=policy,
        reason='urgencia')
    assert not user_with_reason['ok']
    admin_ok = scheduling.save_appointment(
        db_url, resource_id=resource['id'], start=f'{FUTURE}T20:00',
        end=f'{FUTURE}T21:00', title='Tarde', zone=ZONE, window_policy=policy,
        role='admin', reason='autorizada por dirección')
    assert admin_ok['ok']


def test_listado_por_rango(db_url, org, resource):
    day = '2027-05-20'  # fecha aislada de otras pruebas
    scheduling.save_appointment(db_url, resource_id=resource['id'],
                                start=f'{day}T10:00', end=f'{day}T11:00',
                                title='L1', zone=ZONE)
    scheduling.save_appointment(db_url, resource_id=resource['id'],
                                start=f'{day}T12:00', end=f'{day}T13:00',
                                title='L2', zone=ZONE, channel='web')
    events = scheduling.list_appointments(
        db_url, start_utc=f'{day}T00:00:00+00:00',
        end_utc=f'{day}T23:59:00+00:00')
    assert [e['title'] for e in events] == ['L1', 'L2']
    with pytest.raises(ValueError):
        scheduling.list_appointments(db_url, start_utc=f'{day}T12:00:00+00:00',
                                     end_utc=f'{day}T10:00:00+00:00')
