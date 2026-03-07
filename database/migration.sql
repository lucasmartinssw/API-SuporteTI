-- Migration script to create the project database and tables.
-- You can run this file directly in MySQL Workbench or use the Python helper.

-- change `projetofinal` if your DATABASE name in config.py is different
CREATE DATABASE IF NOT EXISTS projetofinal;
USE projetofinal;

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  senha VARCHAR(255) NOT NULL,
  cargo ENUM('admin', 'tecnico', 'usuario') DEFAULT 'usuario',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelas de Auxiliares (Parametrização)
CREATE TABLE IF NOT EXISTS categorias (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS prioridades (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nivel VARCHAR(20) NOT NULL -- Ex: Baixa, Média, Alta
);

CREATE TABLE IF NOT EXISTS status_chamado (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(30) NOT NULL -- Ex: Aberto, Em Atendimento, Concluído
);

-- Tabela Principal de Chamados
CREATE TABLE IF NOT EXISTS chamados (
  id INT PRIMARY KEY AUTO_INCREMENT,
  titulo VARCHAR(150) NOT NULL,
  descricao TEXT NOT NULL,
  user_id INT,
  categoria_id INT,
  prioridade_id INT,
  status_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  FOREIGN KEY (prioridade_id) REFERENCES prioridades(id),
  FOREIGN KEY (status_id) REFERENCES status_chamado(id)
);

-- Tabela de Mídias (Anexos)
CREATE TABLE IF NOT EXISTS chamados_midia (
  id INT PRIMARY KEY AUTO_INCREMENT,
  chamado_id INT,
  url_arquivo VARCHAR(255) NOT NULL,
  tipo_arquivo VARCHAR(50), -- Ex: image/png, video/mp4
  FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
);

-- Tabela de Chat (Interações)
CREATE TABLE IF NOT EXISTS chamados_mensagens (
  id INT PRIMARY KEY AUTO_INCREMENT,
  chamado_id INT,
  user_id INT,
  mensagem TEXT NOT NULL,
  enviado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Inserts iniciais
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
  (1, 'Hardware'),
  (2, 'Software'),
  (3, 'Conexão com Internet'),
  (4, 'Acessos'),
  (5, 'Sistemas'),
  (6, 'Segurança'),
  (7, 'Impressora'),
  (8, 'Telefone/Celular'),
  (9, 'Outros');
