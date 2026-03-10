-- ============================================================
--  Suporte TI — Database Setup
--  Run this file once on a fresh MySQL installation.
--  MySQL Workbench: File > Open SQL Script > Run All
-- ============================================================

-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS projetofinal
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE projetofinal;

-- ============================================================
--  LOOKUP TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS prioridades (
  id   INT PRIMARY KEY AUTO_INCREMENT,
  nivel VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS status_chamado (
  id   INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS categorias (
  id   INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(50) NOT NULL
);

-- ============================================================
--  USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  nome       VARCHAR(100) NOT NULL,
  email      VARCHAR(100) UNIQUE NOT NULL,
  senha      VARCHAR(255) NOT NULL,
  cargo      VARCHAR(100) DEFAULT 'usuario',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
--  ASSETS (Ativos)
-- ============================================================

CREATE TABLE IF NOT EXISTS ativos (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  nome           VARCHAR(100) NOT NULL,
  tipo           ENUM('computador','monitor','impressora','telefone','servidor','switch','outro') NOT NULL,
  numero_serie   VARCHAR(100),
  patrimonio     VARCHAR(50),
  localizacao    VARCHAR(100),
  status         ENUM('ativo','manutencao','reserva','desativado') DEFAULT 'ativo',
  responsavel_id INT NULL,
  observacoes    TEXT,
  created_at     DATETIME DEFAULT NOW(),
  updated_at     DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (responsavel_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
--  TICKETS (Chamados)
-- ============================================================

CREATE TABLE IF NOT EXISTS chamados (
  id           INT PRIMARY KEY AUTO_INCREMENT,
  titulo       VARCHAR(150) NOT NULL,
  descricao    TEXT NOT NULL,
  user_id      INT,
  categoria_id INT,
  prioridade_id INT,
  status_id    INT,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)       REFERENCES users(id),
  FOREIGN KEY (categoria_id)  REFERENCES categorias(id),
  FOREIGN KEY (prioridade_id) REFERENCES prioridades(id),
  FOREIGN KEY (status_id)     REFERENCES status_chamado(id)
);

-- ============================================================
--  TICKET MESSAGES (Chat)
-- ============================================================

CREATE TABLE IF NOT EXISTS chamados_mensagens (
  id          INT PRIMARY KEY AUTO_INCREMENT,
  chamado_id  INT,
  user_id     INT,
  mensagem    TEXT NOT NULL,
  enviado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_internal BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users(id)
);

-- ============================================================
--  TICKET ATTACHMENTS (Mídia)
-- ============================================================

CREATE TABLE IF NOT EXISTS chamados_midia (
  id           INT PRIMARY KEY AUTO_INCREMENT,
  chamado_id   INT,
  mensagem_id  INT NULL,
  url_arquivo  VARCHAR(255) NOT NULL,
  tipo_arquivo VARCHAR(50),
  FOREIGN KEY (chamado_id)  REFERENCES chamados(id)          ON DELETE CASCADE,
  FOREIGN KEY (mensagem_id) REFERENCES chamados_mensagens(id) ON DELETE CASCADE
);

-- ============================================================
--  TICKET <-> TECHNICIAN LINK
-- ============================================================

CREATE TABLE IF NOT EXISTS chamados_tecnicos (
  chamado_id  INT NOT NULL,
  user_id     INT NOT NULL,
  assigned_at DATETIME DEFAULT NOW(),
  PRIMARY KEY (chamado_id, user_id),
  FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
);

-- ============================================================
--  TICKET <-> ASSET LINK
-- ============================================================

CREATE TABLE IF NOT EXISTS chamados_ativos (
  chamado_id INT NOT NULL,
  ativo_id   INT NOT NULL,
  PRIMARY KEY (chamado_id, ativo_id),
  FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE,
  FOREIGN KEY (ativo_id)   REFERENCES ativos(id)   ON DELETE CASCADE
);

-- ============================================================
--  SEED DATA
-- ============================================================

INSERT IGNORE INTO prioridades (id, nivel) VALUES
  (1, 'Baixa'),
  (2, 'Média'),
  (3, 'Alta'),
  (4, 'Urgente');

INSERT IGNORE INTO status_chamado (id, nome) VALUES
  (1, 'Aberto'),
  (2, 'Em Atendimento'),
  (3, 'Concluído');

INSERT IGNORE INTO categorias (id, nome) VALUES
  (1, 'Geral'),
  (2, 'Hardware'),
  (3, 'Software'),
  (4, 'Rede'),
  (5, 'Acesso'),
  (6, 'Outros');

-- ============================================================
--  NOTIFICATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS notificacoes (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  tipo       ENUM('status_change','new_message','ticket_created') NOT NULL,
  chamado_id INT NOT NULL,
  mensagem   VARCHAR(255) NOT NULL,
  lida       BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT NOW(),
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
);

-- ============================================================
--  VERIFY
-- ============================================================

SELECT 'Setup concluído com sucesso!' AS status;
SELECT TABLE_NAME FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = 'projetofinal'
  ORDER BY TABLE_NAME;