-- CORR01/R08: costo conocido por línea de venta (snapshot en el momento).
-- NULL = costo desconocido; NO se infiere ni se recalca con el costo actual
-- del producto. Las líneas históricas quedan NULL expresamente.

ALTER TABLE sale_lines
    ADD COLUMN IF NOT EXISTS unit_cost numeric(12,2);
