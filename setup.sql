-- ============================================================
--  Suporte TI — Database Setup
--  Run once on a fresh MySQL installation.
--  MySQL Workbench: File > Open SQL Script > Run All
-- ============================================================

CREATE DATABASE IF NOT EXISTS projetofinal
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE projetofinal;

-- ============================================================
--  LOOKUP TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS prioridades (
  id    INT PRIMARY KEY AUTO_INCREMENT,
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
  bio        TEXT NULL,
  avatar_url VARCHAR(500) NULL,
  ativo      TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
--  ASSETS (Ativos)
-- ============================================================

CREATE TABLE IF NOT EXISTS ativos (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  nome               VARCHAR(100) NOT NULL,
  tipo               ENUM('computador','monitor','impressora','telefone','servidor','switch','outro') NOT NULL,
  numero_serie       VARCHAR(100),
  patrimonio         VARCHAR(50),
  localizacao        VARCHAR(100),
  status             ENUM('ativo','manutencao','reserva','desativado') DEFAULT 'ativo',
  responsavel_id     INT NULL,
  observacoes        TEXT,
  warranty_expires_at DATE NULL,
  created_at         DATETIME DEFAULT NOW(),
  updated_at         DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (responsavel_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ativos_midia (
  id           INT PRIMARY KEY AUTO_INCREMENT,
  ativo_id     INT NOT NULL,
  url_arquivo  VARCHAR(500) NOT NULL,
  tipo_arquivo VARCHAR(100),
  nome_arquivo VARCHAR(255),
  created_at   DATETIME DEFAULT NOW(),
  FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE CASCADE
);

-- ============================================================
--  TICKETS (Chamados)
-- ============================================================

CREATE TABLE IF NOT EXISTS chamados (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  titulo        VARCHAR(150) NOT NULL,
  descricao     TEXT NOT NULL,
  user_id       INT,
  categoria_id  INT,
  prioridade_id INT,
  status_id     INT,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)       REFERENCES users(id),
  FOREIGN KEY (categoria_id)  REFERENCES categorias(id),
  FOREIGN KEY (prioridade_id) REFERENCES prioridades(id),
  FOREIGN KEY (status_id)     REFERENCES status_chamado(id)
);

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

CREATE TABLE IF NOT EXISTS chamados_midia (
  id           INT PRIMARY KEY AUTO_INCREMENT,
  chamado_id   INT,
  mensagem_id  INT NULL,
  url_arquivo  VARCHAR(255) NOT NULL,
  tipo_arquivo VARCHAR(50),
  nome_arquivo VARCHAR(255) NULL,
  FOREIGN KEY (chamado_id)  REFERENCES chamados(id)           ON DELETE CASCADE,
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
--  AUDIT LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS auditoria (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  tabela       VARCHAR(50) NOT NULL,
  registro_id  INT NOT NULL,
  usuario_id   INT,
  acao         VARCHAR(100) NOT NULL,
  descricao    TEXT,
  created_at   DATETIME DEFAULT NOW(),
  FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE SET NULL
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
  (3, 'Concluído'),
  (4, 'Fechado');

INSERT IGNORE INTO categorias (id, nome) VALUES
  (1, 'Geral'),
  (2, 'Hardware'),
  (3, 'Software'),
  (4, 'Rede'),
  (5, 'Acesso'),
  (6, 'Outros');

INSERT IGNORE INTO ativos (id, nome, tipo, numero_serie, patrimonio, localizacao, status, observacoes) VALUES
  (1,  'Desktop Dell OptiPlex 7090',     'computador', 'SN-DELL-7090-001',    'PAT-2024-001', 'Sala 101 - TI',           'ativo',      'Core i7, 16GB RAM, SSD 512GB'),
  (2,  'Desktop Dell OptiPlex 7090',     'computador', 'SN-DELL-7090-002',    'PAT-2024-002', 'Sala 102 - Financeiro',   'ativo',      'Core i7, 16GB RAM, SSD 512GB'),
  (3,  'Notebook Lenovo ThinkPad T14',   'computador', 'SN-LNVO-T14-001',    'PAT-2024-003', 'Home Office - Diretoria', 'ativo',      'Core i5, 8GB RAM, SSD 256GB'),
  (4,  'Notebook HP ProBook 450 G8',     'computador', 'SN-HP-450G8-001',     'PAT-2024-004', 'Sala 103 - RH',           'manutencao', 'Tela com defeito, aguardando peça'),
  (5,  'Monitor LG 24" IPS',             'monitor',    'SN-LG-24IPS-001',     'PAT-2024-005', 'Sala 101 - TI',           'ativo',      'Full HD, HDMI + DisplayPort'),
  (6,  'Monitor LG 24" IPS',             'monitor',    'SN-LG-24IPS-002',     'PAT-2024-006', 'Sala 102 - Financeiro',   'ativo',      'Full HD, HDMI + DisplayPort'),
  (7,  'Monitor Samsung 27" Curvo',      'monitor',    'SN-SAMS-27C-001',     'PAT-2024-007', 'Sala 201 - Diretoria',    'ativo',      'QHD, USB-C'),
  (8,  'Impressora HP LaserJet Pro',     'impressora', 'SN-HP-LJ-PRO-001',   'PAT-2024-008', 'Corredor 1° andar',       'ativo',      'Rede Wi-Fi, duplex automático'),
  (9,  'Impressora Epson EcoTank L3250', 'impressora', 'SN-EPSON-L3250-001',  'PAT-2024-009', 'Sala 102 - Financeiro',   'ativo',      'Jato de tinta, tanque de tinta'),
  (10, 'Telefone IP Grandstream',        'telefone',   'SN-GS-GXP1625-001',  'PAT-2024-010', 'Recepção',                'ativo',      'Ramal 1001, PoE'),
  (11, 'Telefone IP Grandstream',        'telefone',   'SN-GS-GXP1625-002',  'PAT-2024-011', 'Sala 201 - Diretoria',    'ativo',      'Ramal 1002, PoE'),
  (12, 'Servidor Dell PowerEdge T340',   'servidor',   'SN-DELL-PE-T340-01', 'PAT-2024-012', 'Rack - Sala TI',          'ativo',      'Xeon E-2224, 32GB ECC, RAID 1'),
  (13, 'Switch Cisco SG350-28',          'switch',     'SN-CISCO-SG350-001',  'PAT-2024-013', 'Rack - Sala TI',          'ativo',      '28 portas Gigabit, gerenciável'),
  (14, 'Notebook Dell Latitude 5520',    'computador', 'SN-DELL-5520-001',    'PAT-2024-014', 'Estoque TI',              'reserva',    'Reserva para substituição'),
  (15, 'Monitor Dell 22" HD',            'monitor',    'SN-DELL-22HD-001',    'PAT-2024-015', 'Estoque TI',              'desativado', 'Defeito na fonte, sem conserto');

-- ============================================================
--  VERIFY
-- ============================================================

SELECT 'Setup concluído com sucesso!' AS status;

SELECT TABLE_NAME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'projetofinal'
ORDER BY TABLE_NAME;