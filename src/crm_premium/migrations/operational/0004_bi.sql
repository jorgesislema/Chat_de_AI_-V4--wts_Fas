-- Modelo estrella analítico (esquema bi), separado del operacional.
-- Se reconstruye por ETL idempotente; nunca se escribe desde la operación.
-- PII fuera: contacto seudonimizado, sin teléfonos ni notas en bi.

CREATE SCHEMA IF NOT EXISTS bi;

CREATE TABLE bi.meta (
    key        text PRIMARY KEY,
    value      text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE bi.dim_fecha (
    date_key   date PRIMARY KEY,
    anio       integer NOT NULL,
    mes        integer NOT NULL,
    dia        integer NOT NULL,
    dia_semana integer NOT NULL,   -- 0=lunes
    semana_iso integer NOT NULL,
    mes_nombre text    NOT NULL
);

CREATE TABLE bi.dim_hora (
    hora_key smallint PRIMARY KEY CHECK (hora_key BETWEEN 0 AND 23),
    franja   text NOT NULL         -- mañana / tarde / noche / madrugada
);

CREATE TABLE bi.dim_producto (
    product_key    serial PRIMARY KEY,
    product_id     bigint UNIQUE NOT NULL,
    nombre         text NOT NULL,
    tipo           text NOT NULL,
    categoria      text,
    precio_actual  numeric(12,2)
);

CREATE TABLE bi.dim_contacto (
    contact_key serial PRIMARY KEY,
    contact_id  bigint UNIQUE NOT NULL,
    seudonimo   text NOT NULL       -- 'contacto_<id>'; sin nombre real
);

CREATE TABLE bi.dim_recurso (
    resource_key serial PRIMARY KEY,
    resource_id  bigint UNIQUE NOT NULL,
    nombre       text NOT NULL
);

CREATE TABLE bi.dim_estado (
    estado_key smallint PRIMARY KEY,
    codigo     text UNIQUE NOT NULL,
    etiqueta   text NOT NULL
);

CREATE TABLE bi.fact_cita (
    cita_id      bigint PRIMARY KEY,
    fecha_key    date NOT NULL REFERENCES bi.dim_fecha(date_key),
    hora_key     smallint NOT NULL REFERENCES bi.dim_hora(hora_key),
    recurso_key  integer NOT NULL REFERENCES bi.dim_recurso(resource_key),
    estado_key   smallint NOT NULL REFERENCES bi.dim_estado(estado_key),
    contacto_key integer REFERENCES bi.dim_contacto(contact_key),
    duracion_min integer NOT NULL,
    es_demo      boolean NOT NULL
);

CREATE TABLE bi.fact_venta_linea (
    line_key       bigserial PRIMARY KEY,
    fecha_key      date NOT NULL REFERENCES bi.dim_fecha(date_key),
    hora_key       smallint NOT NULL REFERENCES bi.dim_hora(hora_key),
    product_key    integer NOT NULL REFERENCES bi.dim_producto(product_key),
    contacto_key   integer REFERENCES bi.dim_contacto(contact_key),
    unidades       integer NOT NULL,          -- negativas en reversas
    neto           numeric(12,2) NOT NULL,
    costo_conocido numeric(12,2),
    es_demo        boolean NOT NULL,
    es_reversa     boolean NOT NULL,
    sale_id        bigint NOT NULL
);

CREATE INDEX idx_fvl_fecha ON bi.fact_venta_linea(fecha_key);
CREATE INDEX idx_fc_fecha ON bi.fact_cita(fecha_key);

CREATE VIEW bi.v_top_productos AS
SELECT p.product_key, p.nombre, p.tipo, p.categoria,
       sum(l.unidades) AS unidades, sum(l.neto) AS neto
FROM bi.fact_venta_linea l
JOIN bi.dim_producto p USING (product_key)
GROUP BY p.product_key, p.nombre, p.tipo, p.categoria;

CREATE VIEW bi.v_ventas_dia AS
SELECT fecha_key, sum(neto) AS neto, sum(unidades) AS unidades
FROM bi.fact_venta_linea
GROUP BY fecha_key;

CREATE VIEW bi.v_horas_citas AS
SELECT hora_key, count(*) AS citas
FROM bi.fact_cita
GROUP BY hora_key;
