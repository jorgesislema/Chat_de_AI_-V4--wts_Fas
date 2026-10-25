-- E01-M: backfill idempotente a sede Principal (la migración 0006 podía
-- ejecutarse con la tabla organization aún vacía en bases nuevas).

INSERT INTO branches (id, name, timezone)
SELECT 1, 'Principal', COALESCE((SELECT zone FROM organization WHERE id = 1), 'UTC')
WHERE NOT EXISTS (SELECT 1 FROM branches WHERE id = 1);

UPDATE resources       SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE appointments    SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE products        SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE sales           SET branch_id = 1 WHERE branch_id IS NULL;
UPDATE stock_movements SET branch_id = 1 WHERE branch_id IS NULL;

INSERT INTO user_branch_roles (user_id, branch_id, scope_role)
SELECT u.id, NULL, 'director' FROM users u
WHERE u.role = 'admin'
  AND NOT EXISTS (SELECT 1 FROM user_branch_roles r WHERE r.user_id = u.id);

INSERT INTO user_branch_roles (user_id, branch_id, scope_role)
SELECT u.id, 1, 'asesor' FROM users u
WHERE u.role <> 'admin'
  AND NOT EXISTS (SELECT 1 FROM user_branch_roles r WHERE r.user_id = u.id);

INSERT INTO bi.dim_sede (branch_id, nombre)
SELECT id, name FROM branches
ON CONFLICT (branch_id) DO NOTHING;
