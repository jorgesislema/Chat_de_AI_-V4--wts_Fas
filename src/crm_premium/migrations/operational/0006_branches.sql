-- E01: sedes, roles de ámbito, horarios de recurso y referencia tipada a
-- servicio. Backfill transaccional a sede «Principal» (id=1) preservando
-- IDs/historial/precios/costos. No infiere pagos, entregas ni estados:
-- los datos históricos se etiquetan, no se reinterpretan.

CREATE TABLE branches (
    id         bigserial PRIMARY KEY,
    name       text        NOT NULL UNIQUE,
    timezone   text        NOT NULL,
    is_active  boolean     NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Rol de ámbito independiente del rol de cuenta (users.role). NULL en
-- branch_id = ámbito global (sólo director). Denegación por defecto:
-- sin fila, sin acceso a sede alguna salvo rol global explícito.
CREATE TABLE user_branch_roles (
    id         bigserial PRIMARY KEY,
    user_id    bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    branch_id  bigint REFERENCES branches(id) ON DELETE CASCADE,
    scope_role text   NOT NULL
               CHECK (scope_role IN ('director', 'gerente', 'asesor',
                                     'almacen', 'finanzas', 'analista')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ubr_unique UNIQUE (user_id, branch_id, scope_role),
    CONSTRAINT ubr_global_only_director
        CHECK (branch_id IS NOT NULL OR scope_role = 'director')
);

CREATE INDEX idx_ubr_user ON user_branch_roles(user_id);

-- Sede de operación (backfill = 1). NULL transitorio no autoriza: el
-- servidor trata NULL como «sin sede» hasta el backfill.
ALTER TABLE resources        ADD COLUMN IF NOT EXISTS branch_id bigint REFERENCES branches(id);
ALTER TABLE appointments     ADD COLUMN IF NOT EXISTS branch_id bigint REFERENCES branches(id);
ALTER TABLE products         ADD COLUMN IF NOT EXISTS branch_id bigint REFERENCES branches(id);
ALTER TABLE sales            ADD COLUMN IF NOT EXISTS branch_id bigint REFERENCES branches(id);
ALTER TABLE stock_movements  ADD COLUMN IF NOT EXISTS branch_id bigint REFERENCES branches(id);

-- Horario semanal por recurso (vacío = hereda el horario del negocio).
CREATE TABLE resource_schedules (
    id          bigserial PRIMARY KEY,
    resource_id bigint NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    weekday     smallint NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time  time     NOT NULL,
    end_time    time     NOT NULL,
    CONSTRAINT rs_valid_range CHECK (end_time > start_time),
    CONSTRAINT rs_unique UNIQUE (resource_id, weekday, start_time)
);

-- Referencia tipada a servicio/tratamiento del catálogo (opcional).
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS service_id bigint REFERENCES products(id);

-- Backfill transaccional: sede Principal desde la zona del negocio.
INSERT INTO branches (id, name, timezone)
SELECT 1, 'Principal', o.zone FROM organization o
ON CONFLICT (id) DO NOTHING;

UPDATE resources       SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE appointments    SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE products        SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE sales           SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE stock_movements SET branch_id = 1 WHERE branch_id IS NULL;

-- Roles de ámbito iniciales: admin existente → director global;
-- resto de usuarios → asesor de la sede 1 (ningún acceso nuevo se abre).
INSERT INTO user_branch_roles (user_id, branch_id, scope_role)
SELECT u.id, NULL, 'director' FROM users u
WHERE u.role = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO user_branch_roles (user_id, branch_id, scope_role)
SELECT u.id, 1, 'asesor' FROM users u
WHERE u.role <> 'admin'
  AND NOT EXISTS (SELECT 1 FROM user_branch_roles r WHERE r.user_id = u.id)
ON CONFLICT DO NOTHING;

-- Modelo estrella: sede como dimensión y etiqueta en hechos.
CREATE TABLE bi.dim_sede (
    branch_key serial PRIMARY KEY,
    branch_id  bigint UNIQUE NOT NULL,
    nombre     text NOT NULL
);

ALTER TABLE bi.fact_cita        ADD COLUMN IF NOT EXISTS sede_key integer REFERENCES bi.dim_sede(branch_key);
ALTER TABLE bi.fact_venta_linea ADD COLUMN IF NOT EXISTS sede_key integer REFERENCES bi.dim_sede(branch_key);

INSERT INTO bi.dim_sede (branch_id, nombre)
SELECT id, name FROM branches
ON CONFLICT (branch_id) DO NOTHING;
