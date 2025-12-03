-- PROJETO: GESTÃO DE BIKES NAS CIDADES - PARTE 3
-- ARQUIVO: dados_oracle.sql
-- Linguagem: PL-SQL
-- GRUPO: G12


-- Inserindo USUARIOS
-- Usuário 1: Paga normal (is_cadUnico = 0)
INSERT INTO Usuario (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cadUnico)
VALUES ('76863621088', 'Larissa Mendes', DATE '1999-05-15', 'Rua Episcopal', '1996', 'Centro', 'São Carlos', 'SP', 0);

-- Usuario 2: Isento, possui CadUnico (is_cadUnico = 1)
INSERT INTO Usuario (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cadUnico)
VALUES ('69348393073', 'Mariana Oliveira', DATE '1985-10-20', 'Rua Alvarenga Peixoto', '55', 'Parque Arnold Schimidt', 'São Carlos', 'SP', 1);

-- Usuario 3: Paga normal (is_cadUnico = 0)
INSERT INTO Usuario (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cadUnico)
VALUES ('55627925086', 'Carlos Souza', DATE '2004-01-01', 'Alameda das Papoulas', '157', 'Cidade Jardim', 'São Carlos', 'SP', 0);



-- Inserindo Pontos de Estacionamento
-- Nota: O ID (cod_ponto) é gerado automaticamente pela BD
INSERT INTO Ponto (rua, numero, bairro, cidade, uf, referencia, capacidade_maxima)
VALUES ('Rua 15 de Novembro', '1477', 'Parque Santa Mônica', 'São Carlos', 'SP', 'Próximo à Praça XV, ao lado do ponto de ônibus', 20);

INSERT INTO Ponto (rua, numero, bairro, cidade, uf, referencia, capacidade_maxima)
VALUES ('Avenida São Carlos', '21666', 'Centro', 'São Carlos', 'SP', 'Ponto de Ônibus da Escola Álvaro Guião', 15);

INSERT INTO Ponto (rua, numero, bairro, cidade, uf, referencia, capacidade_maxima)
VALUES ('Rua Episcopal', '700', 'Centro', 'São Carlos', 'SP', 'Senac São Carlos', 50);



-- Inserindo CARTOES
-- Por fins de teste, está sendo inserido a Data de emissão, mas por default, pega a data do sistema na hora do cadastro.
INSERT INTO Cartao (usuario_cpf, saldo, data_validade, data_emissao)
VALUES ('76863621088', 50.00, DATE '2026-12-31', DATE '2024-01-01');

INSERT INTO Cartao (usuario_cpf, saldo, data_validade, data_emissao)
VALUES ('69348393073', 0.00, DATE '2026-12-31', DATE '2024-01-01'); 


-- Inserindo BIKES
-- Nota: qnt_alugueis e tempo_total_utilizado serão inseridos/atualizados de acordo com cálculos feitos pela aplicação
-- Bike 1
INSERT INTO Bike (modelo, ano_fabricacao, cor, status, qnt_alugueis, tempo_total_utilizado, ponto_atual_id)
VALUES ('Mountain Bike X', 2022, 'Vermelha', 'DISPONIVEL', 10, 500, 1);

-- Bike 2
INSERT INTO Bike (modelo, ano_fabricacao, cor, status, qnt_alugueis, tempo_total_utilizado, ponto_atual_id)
VALUES ('Urban City', 2023, 'Azul', 'DISPONIVEL', 2,  200, 2);

-- Bike 3
-- Bike cadastrada, mas sem ponto de estacionamento, pois está em manutenção
INSERT INTO Bike (modelo, ano_fabricacao, cor, status, qnt_alugueis, tempo_total_utilizado, ponto_atual_id)
VALUES ('Eletrica Z', 2024, 'Branca', 'MANUTENCAO', 5, 100, NULL); 


-- 5. Inserindo ALUGUEIS (Histórico)
-- Nota: Removemos 'periodo_alugado' da inserção pois é gerado automaticamente por uma Coluna Virtual

-- Aluguel 1: Concluído
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (2, '76863621088', 1, 2, TIMESTAMP '2024-11-01 10:00:00', TIMESTAMP '2024-11-01 11:00:00', 5.00, 'CONCLUIDO');

-- Aluguel 2: Concluído (Isenta)
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (2, '69348393073', 2, 1, TIMESTAMP '2024-11-02 14:00:00', TIMESTAMP '2024-11-02 15:30:00', 0.00, 'CONCLUIDO');

-- Aluguel 3: Em andamento
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (2, '76863621088', 1, NULL, CURRENT_TIMESTAMP, NULL, NULL, 'EM_ANDAMENTO');

-- Aluguel 4: Atrasado/Multado
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (1, '55627925086', 1, 1, TIMESTAMP '2024-10-01 08:00:00', TIMESTAMP '2024-10-02 20:00:00', 50.00, 'CONCLUIDO');

-- Aluguel 5: Concluído
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (1, '76863621088', 2, 3, TIMESTAMP '2024-10-03 09:00:00', TIMESTAMP '2024-11-03 10:00:00', 5.00, 'CONCLUIDO');

-- Aluguel 6: Concluído
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (1, '76863621088', 3, 2, TIMESTAMP '2024-10-04 14:00:00', TIMESTAMP '2024-11-04 15:00:00', 5.00, 'CONCLUIDO');

-- Aluguel 7: Atrasado/Multado
INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, ponto_devolucao_id, data_hora_inicio, data_hora_fim, valor_aluguel, status)
VALUES (2, '76863621088', 2, 1, TIMESTAMP '2024-11-02 14:00:00', TIMESTAMP '2024-11-02 15:30:00', 0.00, 'CONCLUIDO');



-- Inserindo MANUTENCAO
INSERT INTO Manutencao (bike_n_registro, tipo, valor, data_inicio, data_fim, descricao_problema)
VALUES (3, 'CORRETIVA', 150.00, DATE '2024-11-20', NULL, 'Pneu furado e corrente quebrada');

INSERT INTO Manutencao (bike_n_registro, tipo, valor, data_inicio, data_fim, descricao_problema)
VALUES (1, 'PREVENTIVA', 50.00, DATE '2024-06-01', DATE '2024-06-02', 'Lubrificação geral');


-- Inserindo MULTAS
-- Multa do Aluguel 4 (isPaid = 0)
INSERT INTO Multa (aluguel_id, valor, tipo, vencimento, data_pagamento_multa, isPaid, tempo_bloqueio)
VALUES (4, 20.00, 'ATRASO', DATE '2024-10-10', NULL, 0, 5);

INSERT INTO Multa (aluguel_id, valor, tipo, vencimento, data_pagamento_multa, isPaid, tempo_bloqueio)
VALUES (7, 20.00, 'ATRASO', DATE '2024-11-10', NULL, 0, 5);

-- Inserindo COMENTARIOS
-- Comentário sobre a Bike do Aluguel 1
INSERT INTO Comentario_Bike (aluguel_id, nota, freios, rodas, aparencia, acessorios, pecas, texto_livre)
VALUES (1, 9, 'Bom', 'Bom', 'Regular', 'Bom', 'Bom', 'Bike muito boa, mas arranhada.');

-- Comentário sobre o Ponto do Aluguel 1
INSERT INTO Comentario_Ponto (aluguel_id, nota, sistema_aluguel, disponibilidade, n_bikes_avaliacao, aparencia_geral)
VALUES (1, 10, 'Otimo', 'Otimo', 'Suficiente', 'Limpo');

-- Registro na tabela de tipo
INSERT INTO Comentario_Tipo (aluguel_id, tipo) VALUES (1, 'BIKE');
INSERT INTO Comentario_Tipo (aluguel_id, tipo) VALUES (1, 'PONTO');

COMMIT;