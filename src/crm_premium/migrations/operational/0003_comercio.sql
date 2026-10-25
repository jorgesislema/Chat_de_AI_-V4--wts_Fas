-- Comercio: catálogo con precios auditados, stock por movimientos, ventas
-- con pago registrado y reversión compensatoria. Más base de conocimiento
-- y registro de auditoría del asistente interno.

CREATE TABLE products (
    id          bigserial PRIMARY KEY,
    sku         text        NOT NULL UNIQUE,
    name        text        NOT NULL,
    kind        text        NOT NULL DEFAULT 'servicio'
                CHECK (kind IN ('producto', 'servicio')),
    category    text,
    price       numeric(12,2) NOT NULL CHECK (price >= 0),
    cost        numeric(12,2) CHECK (cost IS NULL OR cost >= 0),
    stock       integer     NOT NULL DEFAULT 0 CHECK (stock >= 0),
    min_stock   integer     NOT NULL DEFAULT 0,
    is_active   boolean     NOT NULL DEFAULT true,
    row_version integer     NOT NULL DEFAULT 1,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_products_name ON products (lower(name));

-- Cada cambio de precio queda auditado; nunca se edita el historial.
CREATE TABLE product_price_history (
    id            bigserial PRIMARY KEY,
    product_id    bigint      NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    old_price     numeric(12,2),
    new_price     numeric(12,2) NOT NULL,
    reason        text,
    actor_user_id bigint      REFERENCES users(id),
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sales (
    id             bigserial PRIMARY KEY,
    contact_id     bigint      REFERENCES contacts(id),
    total          numeric(12,2) NOT NULL,
    paid           numeric(12,2) NOT NULL DEFAULT 0,
    payment_method text,
    status         text        NOT NULL DEFAULT 'confirmed'
                   CHECK (status IN ('confirmed', 'reversed')),
    is_demo        boolean     NOT NULL DEFAULT false,
    note           text,
    created_by     bigint      REFERENCES users(id),
    created_at     timestamptz NOT NULL DEFAULT now(),
    reversed_at    timestamptz,
    reverse_reason text
);

CREATE TABLE sale_lines (
    id           bigserial PRIMARY KEY,
    sale_id      bigint      NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id   bigint      NOT NULL REFERENCES products(id),
    product_name text        NOT NULL,
    kind         text        NOT NULL,
    qty          integer     NOT NULL CHECK (qty > 0),
    unit_price   numeric(12,2) NOT NULL,
    line_total   numeric(12,2) NOT NULL
);

CREATE INDEX idx_sale_lines_sale ON sale_lines(sale_id);

-- Stock sólo se mueve por movimientos firmados con causa y saldo resultante.
CREATE TABLE stock_movements (
    id              bigserial PRIMARY KEY,
    product_id      bigint      NOT NULL REFERENCES products(id),
    delta           integer     NOT NULL,
    resulting_stock integer     NOT NULL CHECK (resulting_stock >= 0),
    cause           text        NOT NULL
                    CHECK (cause IN ('initial', 'sale', 'reversal', 'adjustment')),
    sale_id         bigint      REFERENCES sales(id),
    note            text,
    actor_user_id   bigint      REFERENCES users(id),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_stock_product ON stock_movements(product_id, id);

-- Base de conocimiento interna (RAG básico por palabras clave en esta fase).
CREATE TABLE knowledge_docs (
    id         bigserial PRIMARY KEY,
    title      text        NOT NULL,
    content    text        NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Auditoría del asistente: cada pregunta/respuesta con herramienta usada.
CREATE TABLE assistant_log (
    id         bigserial PRIMARY KEY,
    user_id    bigint      REFERENCES users(id),
    question   text        NOT NULL,
    intent     text,
    tool       text,
    answer     text        NOT NULL,
    data       jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
