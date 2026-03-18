-- ============================================================
--  Migration: Fix ativos.status ENUM
--  Run this if you already have an existing database.
--  For fresh installs, just use the updated setup.sql instead.
-- ============================================================

USE projetofinal;

-- Step 1: Temporarily convert to VARCHAR so data is preserved during transition
ALTER TABLE ativos MODIFY COLUMN status VARCHAR(20) DEFAULT 'disponivel';

-- Step 2: Map old values to new ones
--  (AND id > 0 satisfies MySQL safe update mode which requires a KEY column in WHERE)
UPDATE ativos SET status = 'disponivel' WHERE status = 'ativo' AND id > 0;
UPDATE ativos SET status = 'disponivel' WHERE status = 'reserva' AND id > 0;

-- Step 3: Re-apply the correct ENUM with the new values
ALTER TABLE ativos
  MODIFY COLUMN status ENUM('disponivel','em_uso','manutencao','emprestado','desativado')
  NOT NULL DEFAULT 'disponivel';

SELECT 'Migration concluída com sucesso!' AS resultado;