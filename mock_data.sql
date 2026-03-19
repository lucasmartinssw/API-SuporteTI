-- ============================================================
--  Suporte TI — Mock Data for Presentation
--  Run AFTER setup.sql on the projetofinal database.
--  All accounts use password: Suporte2025
-- ============================================================

USE projetofinal;

-- ============================================================
--  USERS
--  Password for all accounts: Suporte2025
-- ============================================================

INSERT INTO users (id, nome, email, senha, cargo, bio, ativo) VALUES
  (10, 'Lucas Oliveira',   'lucas.ti@empresa.com',      '$2b$12$udGSYFxtevZkXL0FfrZ0AOW018liyfWein3htvMHjtH2awp25gxo.', 'tecnico', 'Analista de TI responsável pela infraestrutura e suporte técnico da empresa. 3 anos de experiência.', 1),
  (11, 'Ana Paula Souza',  'ana.financeiro@empresa.com','$2b$12$udGSYFxtevZkXL0FfrZ0AOW018liyfWein3htvMHjtH2awp25gxo.', 'usuario', 'Analista financeira, Departamento Financeiro.', 1),
  (12, 'Roberto Mendes',   'roberto.rh@empresa.com',    '$2b$12$udGSYFxtevZkXL0FfrZ0AOW018liyfWein3htvMHjtH2awp25gxo.', 'usuario', 'Coordenador de RH, Departamento de Recursos Humanos.', 1),
  (13, 'Carla Ferreira',   'carla.diretoria@empresa.com','$2b$12$udGSYFxtevZkXL0FfrZ0AOW018liyfWein3htvMHjtH2awp25gxo.', 'usuario', 'Assistente de Diretoria.', 1);


-- ============================================================
--  CHAMADOS
-- ============================================================

INSERT INTO chamados (id, titulo, descricao, user_id, categoria_id, prioridade_id, status_id, created_at, updated_at) VALUES

  -- URGENTE / Em Atendimento (SLA vencido — criado 10h atrás)
  (100, 'Sistema ERP fora do ar — produção parada',
   'O sistema ERP parou de responder às 08h00. Todos os usuários do financeiro estão sem acesso. Mensagem de erro: "Connection timeout". A equipe inteira está parada aguardando resolução urgente.',
   11, 1, 4, 2,
   DATE_SUB(NOW(), INTERVAL 10 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR)),

  -- URGENTE / Aberto (SLA quase vencendo — criado 3h atrás)
  (101, 'Servidor de arquivos inacessível',
   'O servidor de arquivos compartilhados (\\\\SERVER01\\Dados) está inacessível desde às 14h. Não consigo acessar nenhum arquivo do projeto. Preciso entregar um relatório hoje.',
   13, 4, 4, 1,
   DATE_SUB(NOW(), INTERVAL 3 HOUR), DATE_SUB(NOW(), INTERVAL 3 HOUR)),

  -- ALTA / Em Atendimento
  (102, 'Notebook não liga após atualização do Windows',
   'Após a atualização automática do Windows ontem à noite, o notebook não consegue mais iniciar. Fica preso na tela azul com o erro: INACCESSIBLE_BOOT_DEVICE. Tentei reiniciar várias vezes sem sucesso.',
   12, 2, 3, 2,
   DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 5 HOUR)),

  -- ALTA / Aberto
  (103, 'Impressora do financeiro não imprime',
   'A impressora HP LaserJet do corredor do 1° andar não está imprimindo. Os trabalhos ficam na fila mas nunca saem. Já tentei cancelar a fila e reiniciar o spooler sem resultado. Precisamos imprimir notas fiscais urgentemente.',
   11, 2, 3, 1,
   DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),

  -- MÉDIA / Em Atendimento
  (104, 'Sem acesso ao e-mail corporativo',
   'Desde esta manhã não consigo acessar o Outlook. Aparece a mensagem "Não é possível conectar ao servidor". Já reiniciei o computador e o problema persiste. Estou perdendo e-mails importantes.',
   13, 5, 2, 2,
   DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),

  -- MÉDIA / Aberto
  (105, 'VPN não conecta quando trabalho em casa',
   'Toda vez que tento conectar a VPN corporativa de casa, recebo o erro "Authentication failed". Na empresa funciona normalmente. Já desinstalei e reinstalei o cliente sem sucesso.',
   12, 4, 2, 1,
   DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),

  -- MÉDIA / Concluído
  (106, 'Monitor com linhas horizontais na tela',
   'O monitor do meu computador está apresentando linhas horizontais que aparecem e desaparecem aleatoriamente. Não sei se é problema no cabo ou no monitor em si.',
   11, 2, 2, 3,
   DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),

  -- BAIXA / Concluído
  (107, 'Instalar Adobe Reader no computador',
   'Preciso do Adobe Reader instalado no meu computador para abrir documentos PDF enviados por clientes. Não tenho permissão de administrador para instalar.',
   12, 3, 1, 3,
   DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 8 DAY)),

  -- BAIXA / Fechado
  (108, 'Teclado com teclas travando',
   'Algumas teclas do meu teclado estão travando, especialmente as letras A, S e D. Provavelmente é sujeira acumulada mas prefiro que o TI avalie antes de tentar limpar.',
   13, 2, 1, 4,
   DATE_SUB(NOW(), INTERVAL 14 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY)),

  -- BAIXA / Fechado
  (109, 'Configurar assinatura de e-mail',
   'Preciso configurar a assinatura de e-mail no Outlook com o novo padrão da empresa (logo + dados de contato). Não sei como fazer e não quero mexer errado.',
   11, 3, 1, 4,
   DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 18 DAY)),

  -- ALTA / Em Atendimento (com ativo vinculado)
  (110, 'Computador reiniciando sozinho durante o trabalho',
   'Meu computador reinicia aleatoriamente durante o trabalho, especialmente quando tenho muitos programas abertos. Perco o trabalho não salvo toda vez. Suspeito que seja superaquecimento.',
   12, 2, 3, 2,
   DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),

  -- URGENTE / Concluído
  (111, 'Ataque de ransomware detectado na máquina',
   'Recebi um e-mail suspeito e após clicar em um anexo, meu computador começou a mostrar uma tela pedindo resgate em Bitcoin. Desliguei imediatamente e estou aguardando instruções do TI.',
   13, 3, 4, 3,
   DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),

  -- MÉDIA / Aberto
  (112, 'Webcam não é reconhecida no Teams',
   'A webcam interna do notebook não é reconhecida pelo Microsoft Teams. Em outras aplicações como o Zoom funciona normalmente. Tenho reuniões com clientes e preciso resolver.',
   11, 3, 2, 1,
   DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),

  -- BAIXA / Aberto
  (113, 'Solicitar segundo monitor para home office',
   'Gostaria de solicitar um segundo monitor para utilizar em home office. Tenho trabalhado remotamente 3 dias por semana e a produtividade melhoraria muito com dois monitores.',
   12, 1, 1, 1,
   DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),

  -- ALTA / Fechado
  (114, 'Sem internet na sala de reuniões',
   'O Wi-Fi da sala de reuniões principal não está funcionando. Temos uma apresentação para cliente amanhã e precisamos de internet. O switch da sala parece estar desligado.',
   13, 4, 3, 4,
   DATE_SUB(NOW(), INTERVAL 8 DAY), DATE_SUB(NOW(), INTERVAL 6 DAY));


-- ============================================================
--  TECNICO ASSIGNMENTS
-- ============================================================

INSERT INTO chamados_tecnicos (chamado_id, user_id, assigned_at) VALUES
  (100, 10, DATE_SUB(NOW(), INTERVAL 9 HOUR)),
  (102, 10, DATE_SUB(NOW(), INTERVAL 1 DAY)),
  (104, 10, DATE_SUB(NOW(), INTERVAL 2 DAY)),
  (106, 10, DATE_SUB(NOW(), INTERVAL 6 DAY)),
  (107, 10, DATE_SUB(NOW(), INTERVAL 9 DAY)),
  (108, 10, DATE_SUB(NOW(), INTERVAL 13 DAY)),
  (109, 10, DATE_SUB(NOW(), INTERVAL 19 DAY)),
  (110, 10, DATE_SUB(NOW(), INTERVAL 3 DAY)),
  (111, 10, DATE_SUB(NOW(), INTERVAL 4 DAY)),
  (114, 10, DATE_SUB(NOW(), INTERVAL 7 DAY));


-- ============================================================
--  ASSET LINKS (auto-status handled manually here)
-- ============================================================

INSERT INTO chamados_ativos (chamado_id, ativo_id) VALUES
  (102, 3),   -- Notebook Lenovo ThinkPad → Em Atendimento
  (103, 8),   -- Impressora HP LaserJet
  (110, 2),   -- Desktop Dell OptiPlex Financeiro
  (114, 13);  -- Switch Cisco

-- Update asset statuses to reflect linked chamados
UPDATE ativos SET status = 'manutencao' WHERE id IN (3, 8, 2);


-- ============================================================
--  MENSAGENS (realistic conversations)
-- ============================================================

-- Chamado 100: ERP fora do ar (urgente)
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (100, 11, 'Bom dia Lucas, o sistema caiu às 08h em ponto. Toda a equipe está parada. Consegue dar uma olhada urgente?', DATE_SUB(NOW(), INTERVAL 9 HOUR), 0),
  (100, 10, 'Bom dia Ana, já estou verificando. Consegui acessar o servidor e vejo que o serviço do MySQL travou. Vou reiniciar o serviço agora.', DATE_SUB(NOW(), INTERVAL 510 MINUTE), 0),
  (100, 10, 'Serviço reiniciado. Pode tentar acessar novamente?', DATE_SUB(NOW(), INTERVAL 8 HOUR), 0),
  (100, 11, 'Funcionou! Estou conseguindo entrar. Mas está bem lento ainda...', DATE_SUB(NOW(), INTERVAL 465 MINUTE), 0),
  (100, 10, 'Normal, o sistema está reconstruindo o cache. Em cerca de 30 minutos deve normalizar. Vou monitorar o servidor.', DATE_SUB(NOW(), INTERVAL 450 MINUTE), 0),
  (100, 10, 'Nota interna: MySQL travou por falta de espaço em disco — partição /var estava a 98%. Limpei logs antigos e liberou 12GB. Preciso agendar expansão do disco.', DATE_SUB(NOW(), INTERVAL 7 HOUR), 1),
  (100, 11, 'Sistema voltou ao normal! Obrigada pela rapidez Lucas!', DATE_SUB(NOW(), INTERVAL 2 HOUR), 0);

-- Chamado 102: Notebook não liga
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (102, 10, 'Oi Roberto, recebi seu chamado. Vou até sua sala agora para verificar pessoalmente.', DATE_SUB(NOW(), INTERVAL 47 HOUR), 0),
  (102, 12, 'Obrigado Lucas, estou na sala 103.', DATE_SUB(NOW(), INTERVAL 2825 MINUTE), 0),
  (102, 10, 'Verificado in loco. A atualização do Windows corrompeu o boot loader. Vou precisar do notebook por algumas horas para fazer a recuperação pelo ambiente WinRE.', DATE_SUB(NOW(), INTERVAL 46 HOUR), 0),
  (102, 12, 'Tudo bem, fico no computador de reserva. Tem previsão?', DATE_SUB(NOW(), INTERVAL 2770 MINUTE), 0),
  (102, 10, 'Acredito que até o fim do dia de hoje. Vou te avisar assim que estiver pronto.', DATE_SUB(NOW(), INTERVAL 2775 MINUTE), 0),
  (102, 10, 'Nota interna: Usado bootrec /fixmbr e /rebuildbcd. Testando agora se o sistema inicia corretamente.', DATE_SUB(NOW(), INTERVAL 5 HOUR), 1);

-- Chamado 104: Sem acesso ao e-mail
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (104, 10, 'Carla, pode tentar acessar o webmail pelo navegador em https://mail.empresa.com para ver se o problema é só no Outlook?', DATE_SUB(NOW(), INTERVAL 50 HOUR), 0),
  (104, 13, 'Testei sim, pelo navegador funciona! O problema parece ser só no Outlook mesmo.', DATE_SUB(NOW(), INTERVAL 49 HOUR), 0),
  (104, 10, 'Entendido. O perfil do Outlook provavelmente corrompeu. Vou criar um novo perfil remotamente. Pode deixar o computador ligado?', DATE_SUB(NOW(), INTERVAL 2 DAY), 0),
  (104, 13, 'Sim, pode acessar!', DATE_SUB(NOW(), INTERVAL 47 HOUR), 0),
  (104, 10, 'Pronto! Criei um novo perfil e reconfigurei a conta. O Outlook deve estar funcionando agora. Pode testar?', DATE_SUB(NOW(), INTERVAL 1 DAY), 0);

-- Chamado 106: Monitor com linhas (concluído)
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (106, 10, 'Ana, testei com outro cabo DisplayPort e as linhas desapareceram. Era o cabo mesmo — vou trocar por um novo do estoque.', DATE_SUB(NOW(), INTERVAL 6 DAY), 0),
  (106, 11, 'Que alívio! Pensei que fosse o monitor. Muito obrigada!', DATE_SUB(NOW(), INTERVAL 8670 MINUTE), 0),
  (106, 10, 'Cabo trocado e monitor funcionando perfeitamente. Vou fechar o chamado.', DATE_SUB(NOW(), INTERVAL 3 DAY), 0);

-- Chamado 107: Adobe Reader (concluído)
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (107, 10, 'Roberto, instalei o Adobe Reader 23 no seu computador. Aproveitei e instalei também o 7-Zip que você comentou que precisava.', DATE_SUB(NOW(), INTERVAL 8 DAY), 0),
  (107, 12, 'Perfeito! Muito obrigado pela atenção Lucas. Já testei e está funcionando.', DATE_SUB(NOW(), INTERVAL 193 HOUR), 0);

-- Chamado 111: Ransomware (concluído)
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (111, 10, 'Carla, recebi seu chamado. MUITO BEM em desligar imediatamente — isso foi a ação certa. Não ligue o computador novamente. Vou até você agora.', DATE_SUB(NOW(), INTERVAL 7170 MINUTE), 0),
  (111, 10, 'Nota interna: Confirmado ransomware LockBit. Máquina isolada da rede. Backup do dia anterior disponível. Procedendo com formatação e restauração.', DATE_SUB(NOW(), INTERVAL 119 HOUR), 1),
  (111, 13, 'Lucas, fico aliviada que você chegou rápido. O que acontece agora com meus arquivos?', DATE_SUB(NOW(), INTERVAL 116 HOUR), 0),
  (111, 10, 'Seus arquivos do servidor estão salvos — o ransomware só afetou o computador local. Vou restaurar do backup de ontem. Você perde apenas as alterações de hoje. A máquina fica pronta amanhã cedo.', DATE_SUB(NOW(), INTERVAL 115 HOUR), 0),
  (111, 13, 'Ufa! Que susto. Aprendi a lição sobre e-mails suspeitos...', DATE_SUB(NOW(), INTERVAL 114 HOUR), 0),
  (111, 10, 'Computador restaurado e atualizado com novo antivírus. Realizei treinamento rápido com a Carla sobre phishing. Chamado concluído.', DATE_SUB(NOW(), INTERVAL 3 DAY), 0);

-- Chamado 114: Sem internet na sala (fechado)
INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES
  (114, 10, 'Fui verificar a sala de reuniões. O switch estava desligado — alguém provavelmente puxou o cabo de energia sem querer. Já liguei e a rede está normalizada.', DATE_SUB(NOW(), INTERVAL 170 HOUR), 0),
  (114, 13, 'Que rápido! Testei aqui e está funcionando perfeitamente. Obrigada!', DATE_SUB(NOW(), INTERVAL 169 HOUR), 0),
  (114, 10, 'Ótimo! Vou fechar o chamado. Aproveito para sugerir fixar o cabo de energia do switch com abraçadeira para evitar que aconteça novamente.', DATE_SUB(NOW(), INTERVAL 6 DAY), 0);


-- ============================================================
--  NOTIFICATIONS
-- ============================================================

INSERT INTO notificacoes (user_id, tipo, chamado_id, mensagem, lida, created_at) VALUES
  -- Notificações para o tecnico (user 10)
  (10, 'ticket_created', 101, 'Novo chamado urgente: Servidor de arquivos inacessível', 0, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
  (10, 'ticket_created', 103, 'Novo chamado: Impressora do financeiro não imprime', 0, DATE_SUB(NOW(), INTERVAL 1 DAY)),
  (10, 'ticket_created', 105, 'Novo chamado: VPN não conecta quando trabalho em casa', 1, DATE_SUB(NOW(), INTERVAL 2 DAY)),
  (10, 'ticket_created', 112, 'Novo chamado: Webcam não é reconhecida no Teams', 0, DATE_SUB(NOW(), INTERVAL 1 DAY)),
  (10, 'ticket_created', 113, 'Novo chamado: Solicitar segundo monitor para home office', 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
  (10, 'new_message', 100, 'Nova mensagem do usuário no chamado ''Sistema ERP fora do ar''', 1, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (10, 'new_message', 104, 'Nova mensagem do usuário no chamado ''Sem acesso ao e-mail corporativo''', 1, DATE_SUB(NOW(), INTERVAL 47 HOUR)),

  -- Notificações para a Ana (user 11)
  (11, 'status_change', 100, 'Seu chamado ''Sistema ERP fora do ar'' foi atualizado para: Em Atendimento', 1, DATE_SUB(NOW(), INTERVAL 9 HOUR)),
  (11, 'new_message', 100, 'Nova resposta da equipe de TI no chamado ''Sistema ERP fora do ar''', 0, DATE_SUB(NOW(), INTERVAL 510 MINUTE)),
  (11, 'status_change', 106, 'Seu chamado ''Monitor com linhas horizontais'' foi atualizado para: Concluído', 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),

  -- Notificações para o Roberto (user 12)
  (12, 'status_change', 102, 'Seu chamado ''Notebook não liga após atualização do Windows'' foi atualizado para: Em Atendimento', 1, DATE_SUB(NOW(), INTERVAL 46 HOUR)),
  (12, 'new_message', 102, 'Nova resposta da equipe de TI no chamado ''Notebook não liga após atualização do Windows''', 0, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
  (12, 'status_change', 107, 'Seu chamado ''Instalar Adobe Reader'' foi atualizado para: Concluído', 1, DATE_SUB(NOW(), INTERVAL 8 DAY)),

  -- Notificações para a Carla (user 13)
  (13, 'status_change', 104, 'Seu chamado ''Sem acesso ao e-mail corporativo'' foi atualizado para: Em Atendimento', 1, DATE_SUB(NOW(), INTERVAL 2 DAY)),
  (13, 'new_message', 104, 'Nova resposta da equipe de TI no chamado ''Sem acesso ao e-mail corporativo''', 0, DATE_SUB(NOW(), INTERVAL 1 DAY)),
  (13, 'status_change', 111, 'Seu chamado ''Ataque de ransomware detectado'' foi atualizado para: Concluído', 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
  (13, 'status_change', 114, 'Seu chamado ''Sem internet na sala de reuniões'' foi atualizado para: Fechado', 1, DATE_SUB(NOW(), INTERVAL 6 DAY));


-- ============================================================
--  AUDIT LOG
-- ============================================================

INSERT INTO auditoria (tabela, registro_id, usuario_id, acao, descricao, created_at) VALUES
  ('chamados', 100, 10, 'status_alterado',    'Status alterado para ''Em Atendimento'' por Lucas Oliveira', DATE_SUB(NOW(), INTERVAL 9 HOUR)),
  ('chamados', 102, 10, 'status_alterado',    'Status alterado para ''Em Atendimento'' por Lucas Oliveira', DATE_SUB(NOW(), INTERVAL 46 HOUR)),
  ('chamados', 104, 10, 'status_alterado',    'Status alterado para ''Em Atendimento'' por Lucas Oliveira', DATE_SUB(NOW(), INTERVAL 2 DAY)),
  ('chamados', 106, 10, 'status_alterado',    'Status alterado para ''Concluído'' por Lucas Oliveira',      DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('chamados', 107, 10, 'status_alterado',    'Status alterado para ''Concluído'' por Lucas Oliveira',      DATE_SUB(NOW(), INTERVAL 8 DAY)),
  ('chamados', 108, 10, 'status_alterado',    'Status alterado para ''Fechado'' por Lucas Oliveira',        DATE_SUB(NOW(), INTERVAL 10 DAY)),
  ('chamados', 109, 10, 'status_alterado',    'Status alterado para ''Fechado'' por Lucas Oliveira',        DATE_SUB(NOW(), INTERVAL 18 DAY)),
  ('chamados', 110, 10, 'status_alterado',    'Status alterado para ''Em Atendimento'' por Lucas Oliveira', DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('chamados', 111, 10, 'status_alterado',    'Status alterado para ''Concluído'' por Lucas Oliveira',      DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('chamados', 114, 10, 'status_alterado',    'Status alterado para ''Fechado'' por Lucas Oliveira',        DATE_SUB(NOW(), INTERVAL 6 DAY)),
  ('ativos',   3,  10, 'ativo_vinculado',    'Chamado #102 vinculado por Lucas Oliveira',                  DATE_SUB(NOW(), INTERVAL 2 DAY)),
  ('ativos',   8,  10, 'ativo_vinculado',    'Chamado #103 vinculado por Lucas Oliveira',                  DATE_SUB(NOW(), INTERVAL 1 DAY)),
  ('ativos',   2,  10, 'ativo_vinculado',    'Chamado #110 vinculado por Lucas Oliveira',                  DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('ativos',   13, 10, 'ativo_vinculado',    'Chamado #114 vinculado por Lucas Oliveira',                  DATE_SUB(NOW(), INTERVAL 7 DAY)),
  ('ativos',   13, 10, 'ativo_desvinculado', 'Chamado #114 desvinculado por Lucas Oliveira',               DATE_SUB(NOW(), INTERVAL 6 DAY));

UPDATE ativos SET status = 'ativo' WHERE id = 13;

-- ============================================================
--  VERIFY
-- ============================================================

SELECT 'Mock data inserido com sucesso!' AS status;
SELECT COUNT(*) AS total_usuarios   FROM users          WHERE id >= 10;
SELECT COUNT(*) AS total_chamados   FROM chamados        WHERE id >= 100;
SELECT COUNT(*) AS total_mensagens  FROM chamados_mensagens;
SELECT COUNT(*) AS total_notificacoes FROM notificacoes;