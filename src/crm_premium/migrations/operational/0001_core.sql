-- Núcleo del CRM Premium: identidad, organización, contactos y agenda.
-- Esquema inicial de la edición 2000+ (V4). PostgreSQL 14+.

CREATE TABLE users (
    id              bigserial PRIMARY KEY,
    username        text        NOT NULL UNIQUE,
    password_hash   text        NOT NULL,
    full_name       text        NOT NULL DEFAULT '',
    role            text        NOT NULL DEFAULT 'user'
                    CHECK (role IN ('admin', 'user')),
    is_active       boolean     NOT NULL DEFAULT true,
    failed_attempts integer     NOT NULL DEFAULT 0,
    locked_until    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sessions (
    id          bigserial PRIMARY KEY,
    token_hash  text        NOT NULL UNIQUE,
    user_id     bigint      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token  text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    expires_at  timestamptz NOT NULL,
    revoked_at  timestamptz
);

CREATE INDEX idx_sessions_user ON sessions(user_id) WHERE revoked_at IS NULL;

-- Una organización por instalación (fila única id=1).
CREATE TABLE organization (
    id           integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    name         text        NOT NULL,
    zone         text        NOT NULL DEFAULT 'UTC',
    currency     text        NOT NULL DEFAULT 'USD',
    opening_json jsonb       NOT NULL DEFAULT '{}'::jsonb,
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE contacts (
    id         bigserial PRIMARY KEY,
    full_name  text        NOT NULL,
    phone      text,
    email      text,
    notes      text,
    channel    text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_contacts_name ON contacts (lower(full_name));

-- Recursos con agenda (profesionales, sillones, salas...). Capacidad 1.
CREATE TABLE resources (
    id          bigserial PRIMARY KEY,
    name        text        NOT NULL,
    specialty   text,
    is_active   boolean     NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE appointments (
    id                 bigserial PRIMARY KEY,
    resource_id        bigint      NOT NULL REFERENCES resources(id),
    contact_id         bigint      REFERENCES contacts(id),
    title              text        NOT NULL,
    start_utc          timestamptz NOT NULL,
    end_utc            timestamptz NOT NULL,
    operational_status text        NOT NULL DEFAULT 'pending'
                       CHECK (operational_status IN
                              ('pending', 'confirmed', 'attended', 'no_show', 'cancelled')),
    origin             text        NOT NULL DEFAULT 'local',
    channel            text        CHECK (channel IN ('web', 'bot', 'google')
                              OR channel IS NULL),
    event_id           text        NOT NULL UNIQUE,
    row_version        integer     NOT NULL DEFAULT 1,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT appt_positive_range CHECK (end_utc > start_utc)
);

CREATE INDEX idx_appt_conflict
    ON appointments (resource_id, start_utc, end_utc)
    WHERE operational_status <> 'cancelled';

CREATE TABLE appointment_notes (
    id              bigserial PRIMARY KEY,
    appointment_id  bigint      NOT NULL
                    REFERENCES appointments(id) ON DELETE CASCADE,
    author_user_id  bigint      REFERENCES users(id),
    body            text        NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE appointment_history (
    id             bigserial PRIMARY KEY,
    appointment_id bigint      NOT NULL
                   REFERENCES appointments(id) ON DELETE CASCADE,
    action         text        NOT NULL,
    actor_user_id  bigint      REFERENCES users(id),
    actor_label    text,
    reason         text,
    detail         jsonb,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
    id            bigserial PRIMARY KEY,
    actor_user_id bigint REFERENCES users(id),
    actor_label   text,
    action        text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);
