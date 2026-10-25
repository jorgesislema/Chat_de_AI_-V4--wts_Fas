"""Conexión y transacciones PostgreSQL.

Todas las escrituras de los servicios ocurren dentro de ``transaction``, que
confirma al salir sin error y revierte ante excepción. Los servicios reciben
la URL de la base de forma explícita (inyectable en pruebas).
"""
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


def connect(url):
    """Conexión con filas dict; transacciones explícitas (autocommit off)."""
    return psycopg.connect(url, row_factory=dict_row, autocommit=False)


@contextmanager
def transaction(url):
    """Transacción única: commit automático al éxito, rollback ante error."""
    conn = connect(url)
    try:
        with conn.transaction():
            yield conn
    finally:
        conn.close()


def ping(url):
    """Devuelve True si la base responde a ``SELECT 1``."""
    try:
        with connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
        return True
    except psycopg.Error:
        return False
