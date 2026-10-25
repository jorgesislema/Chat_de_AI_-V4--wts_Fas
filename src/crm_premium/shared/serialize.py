"""Serialización común de filas PostgreSQL a diccionarios JSON-safe."""
from datetime import datetime, timezone
from decimal import Decimal


def iso(dt):
    """Datetime (naive o consciente) → ISO 8601 en UTC."""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    return dt


def row(mapping):
    """Copia serializable de una fila dict (datetime → ISO, Decimal → float)."""
    if mapping is None:
        return None
    return {key: _value(value) for key, value in mapping.items()}


def _value(value):
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, Decimal):
        return float(value)
    return value
