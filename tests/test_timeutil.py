"""Tiempo compartido: zonas, DST y rangos de agenda."""
import pytest

from crm_premium.shared.timeutil import (AmbiguousLocalTime, NonexistentLocalTime,
                                          InvalidZone, local_parts, period_label,
                                          to_utc, view_range)


def test_to_utc_sin_offset_interpreta_zona():
    value = to_utc('2026-11-05T09:00', 'America/Guayaquil')
    assert value.isoformat() == '2026-11-05T14:00:00+00:00'


def test_to_utc_con_offset_se_respeta():
    value = to_utc('2026-11-05T09:00-05:00', 'UTC')
    assert value.hour == 14


def test_hora_inexistente_dst_madrid():
    # Madrid salta de 02:00 a 03:00 el 29-03-2026: las 02:30 no existen.
    with pytest.raises(NonexistentLocalTime):
        to_utc('2026-03-29T02:30', 'Europe/Madrid')


def test_hora_ambigua_dst_madrid():
    # Madrid vuelve de 03:00 a 02:00 el 25-10-2026: las 02:30 ocurren dos veces.
    with pytest.raises(AmbiguousLocalTime):
        to_utc('2026-10-25T02:30', 'Europe/Madrid')


def test_zona_invalida():
    with pytest.raises(InvalidZone):
        to_utc('2026-01-01T10:00', 'Marte/Olympus')


def test_rango_semana_lunes_a_domingo():
    rng = view_range('week', '2026-11-04', 'UTC')
    assert rng['start_date'] == '2026-11-02'
    assert rng['end_date'] == '2026-11-08'
    assert len(rng['days']) == 7


def test_rango_mes_rejilla_estable_42_dias():
    rng = view_range('month', '2026-02-10', 'UTC')
    assert len(rng['days']) == 42


def test_rango_mes_enero_tambien_42():
    rng = view_range('month', '2026-01-31', 'UTC')
    assert len(rng['days']) == 42


def test_vista_invalida():
    with pytest.raises(ValueError):
        view_range('year', '2026-01-01', 'UTC')


def test_local_parts_y_period_label():
    parts = local_parts('2026-11-05T14:00:00+00:00', 'America/Guayaquil')
    assert parts['time'] == '09:00'
    parts_madrid = local_parts('2026-07-05T14:00:00+00:00', 'Europe/Madrid')
    assert parts_madrid['time'] == '16:00'
    rng = view_range('month', '2026-11-05', 'UTC')
    assert period_label(rng) == 'nov 2026'
    rng_week = view_range('week', '2026-11-04', 'UTC')
    assert 'nov' in period_label(rng_week)
