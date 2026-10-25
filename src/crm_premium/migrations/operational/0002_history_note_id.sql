-- Corrección del núcleo: el historial necesita note_id para vincular
-- observaciones internas (regla de V3: entrada de historial por nota).

ALTER TABLE appointment_history
    ADD COLUMN IF NOT EXISTS note_id bigint;
