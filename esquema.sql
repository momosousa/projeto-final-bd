-- PROJETO: GESTÃO DE BIKES NAS CIDADES - PARTE 3
-- ARQUIVO: esquema_oracle.sql
-- Linguagem: PL-SQL
-- GRUPO: G12


-- Tabela USUARIO
CREATE TABLE Usuario (
    cpf VARCHAR2(11) PRIMARY KEY, -- Recebe apenas os números do CPF não formatado
    nome VARCHAR2(100) NOT NULL,
    data_nasc DATE NOT NULL,
    rua VARCHAR2(100),
    numero VARCHAR2(10),
    bairro VARCHAR2(50),
    cidade VARCHAR2(50),
    uf CHAR(2),

    -- Oracle não tem BOOLEAN nativo. Usamos 0 ou 1 no lugar.
    is_cadUnico NUMBER(1) DEFAULT 0 CHECK (is_cadUnico IN (0, 1))
);

-- Tabela PONTO (Pontos de Estacionamento)
CREATE TABLE Ponto (
    cod_ponto NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
    rua VARCHAR2(100) NOT NULL,
    numero VARCHAR2(10),
    bairro VARCHAR2(50),
    cidade VARCHAR2(50) NOT NULL,
    uf CHAR(2) NOT NULL,
    referencia VARCHAR2(100),
    capacidade_maxima NUMBER CHECK (capacidade_maxima > 0)
);

-- Tabela CARTAO
CREATE TABLE Cartao (
    id_cartao NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_cpf VARCHAR2(11) NOT NULL UNIQUE, 
    saldo NUMBER(10, 2) DEFAULT 0.00 CHECK (saldo >= 0),
    data_validade DATE NOT NULL,
    data_emissao DATE DEFAULT SYSDATE,
    CONSTRAINT fk_cartao_usuario FOREIGN KEY (usuario_cpf) REFERENCES Usuario(cpf)
);

-- Tabela BIKE
CREATE TABLE Bike (
    n_registro NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    modelo VARCHAR2(50) NOT NULL,
    ano_fabricacao NUMBER,
    cor VARCHAR2(30),
    qnt_alugueis NUMBER DEFAULT 0,
    -- Esse quantificador será atualizado pela aplicação
    status VARCHAR2(20) CHECK (status IN ('DISPONIVEL', 'EM_USO', 'MANUTENCAO')),
    tempo_total_utilizado NUMBER DEFAULT 0, -- Em minutos
    -- Esse quantificador será atualizado pela aplicação, considerando alugueis finalizados.
    ponto_atual_id NUMBER, 
    CONSTRAINT fk_bike_ponto FOREIGN KEY (ponto_atual_id) REFERENCES Ponto(cod_ponto)
);


-- Tabela ALUGUEL
CREATE TABLE Aluguel (
    id_aluguel NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bike_n_registro NUMBER NOT NULL,
    usuario_cpf VARCHAR2(11) NOT NULL,
    ponto_retirada_id NUMBER NOT NULL,
    ponto_devolucao_id NUMBER,
    data_hora_inicio TIMESTAMP NOT NULL,
    data_hora_fim TIMESTAMP,
    valor_aluguel NUMBER(10, 2),
    
    -- Coluna Calculada
    -- Obtem a diferença em dias
    periodo_alugado NUMBER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (data_hora_fim - data_hora_inicio)) * 1440 +
        EXTRACT(HOUR FROM (data_hora_fim - data_hora_inicio)) * 60 +
        EXTRACT(MINUTE FROM (data_hora_fim - data_hora_inicio))
    ) VIRTUAL,
    
    status VARCHAR2(20) CHECK (status IN ('EM_ANDAMENTO', 'CONCLUIDO', 'CANCELADO')),
    
    CONSTRAINT fk_aluguel_bike FOREIGN KEY (bike_n_registro) REFERENCES Bike(n_registro),
    CONSTRAINT fk_aluguel_usuario FOREIGN KEY (usuario_cpf) REFERENCES Usuario(cpf),
    CONSTRAINT fk_aluguel_ponto_ret FOREIGN KEY (ponto_retirada_id) REFERENCES Ponto(cod_ponto),
    CONSTRAINT fk_aluguel_ponto_dev FOREIGN KEY (ponto_devolucao_id) REFERENCES Ponto(cod_ponto),
    CONSTRAINT chk_status_devolucao CHECK (
        (status = 'CONCLUIDO' AND ponto_devolucao_id IS NOT NULL AND data_hora_fim IS NOT NULL) OR
        (status = 'EM_ANDAMENTO' AND ponto_devolucao_id IS NULL AND data_hora_fim IS NULL) OR
        (status = 'CANCELADO')
    )
);

-- Tabela MANUTENCAO
CREATE TABLE Manutencao (
    id_manutencao NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bike_n_registro NUMBER NOT NULL,
    tipo VARCHAR2(20) CHECK (tipo IN ('PREVENTIVA', 'CORRETIVA', 'ANTECIPADA')),
    valor NUMBER(10, 2),
    data_inicio DATE NOT NULL,
    data_fim DATE,
    descricao_problema VARCHAR2(4000),
    CONSTRAINT fk_manutencao_bike FOREIGN KEY (bike_n_registro) REFERENCES Bike(n_registro)
);


-- Tabela MULTA
CREATE TABLE Multa (
    id_multa NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluguel_id NUMBER NOT NULL,
    valor NUMBER(10, 2) NOT NULL,
    tipo VARCHAR2(50) CHECK (tipo IN ('ATRASO', 'DANO', 'NAO_DEVOLUCAO')),
    vencimento DATE NOT NULL,
    data_pagamento_multa DATE,
    isPaid NUMBER(1) DEFAULT 0 CHECK (isPaid IN (0, 1)), --Adaptação de Boolean com 0 e 1
    tempo_bloqueio NUMBER DEFAULT 0, -- Em dias
    CONSTRAINT fk_multa_aluguel FOREIGN KEY (aluguel_id) REFERENCES Aluguel(id_aluguel)
);


-- Tabela COMENTARIO_BIKE
CREATE TABLE Comentario_Bike (
    aluguel_id NUMBER PRIMARY KEY,
    nota NUMBER CHECK (nota BETWEEN 0 AND 10),
    freios VARCHAR2(20), 
    rodas VARCHAR2(20),
    aparencia VARCHAR2(20),
    acessorios VARCHAR2(20),
    pecas VARCHAR2(20),
    texto_livre VARCHAR2(4000),
    CONSTRAINT fk_comm_bike_aluguel FOREIGN KEY (aluguel_id) REFERENCES Aluguel(id_aluguel)
);


-- Tabela COMENTARIO_PONTO
CREATE TABLE Comentario_Ponto (
    aluguel_id NUMBER PRIMARY KEY,
    nota NUMBER CHECK (nota BETWEEN 0 AND 10),
    sistema_aluguel VARCHAR2(20),
    disponibilidade VARCHAR2(20),
    n_bikes_avaliacao VARCHAR2(20),
    aparencia_geral VARCHAR2(20),
    CONSTRAINT fk_comm_ponto_aluguel FOREIGN KEY (aluguel_id) REFERENCES Aluguel(id_aluguel)
);

-- Tabela COMENTARIO_TIPO
CREATE TABLE Comentario_Tipo (
    id_historico NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluguel_id NUMBER NOT NULL,
    tipo VARCHAR2(10) CHECK (tipo IN ('BIKE', 'PONTO')),
    CONSTRAINT fk_comm_tipo_aluguel FOREIGN KEY (aluguel_id) REFERENCES Aluguel(id_aluguel)
);

CREATE INDEX idx_aluguel_usuario ON Aluguel(usuario_cpf);
CREATE INDEX idx_aluguel_bike ON Aluguel(bike_n_registro);
CREATE INDEX idx_aluguel_ponto_ret ON Aluguel(ponto_retirada_id);
CREATE INDEX idx_aluguel_ponto_dev ON Aluguel(ponto_devolucao_id);
CREATE INDEX idx_multa_aluguel ON Multa(aluguel_id);