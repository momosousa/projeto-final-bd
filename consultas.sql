-- PROJETO: GESTÃO DE BIKES NAS CIDADES - PARTE 3
-- ARQUIVO: consultas.sql
-- DESCRIÇÃO: 5 Consultas SQL de complexidade média/alta, incluindo divisão relacional.

-- CONSULTA 1: DIVISÃO RELACIONAL
-- Relatório de Fidelidade e Engajamento de Usuários
-- Lista o nome dos usuários que alugaram bicicletas em TODOS os pontos 
-- de estacionamento estão no Centro de São Carlos.
-- Justificativa: Identificar "power users" que frequentam especificamente todos os 
-- pontos de uma determinada categoria ou localidade para programas de fidelidade.

SELECT U.nome
FROM Usuario U
WHERE NOT EXISTS (
    -- Seleciona o ponto de interesse (Divisor)
    SELECT P.cod_ponto
    FROM Ponto P
    WHERE P.bairro = 'Centro' AND p.cidade = 'São Carlos'
    
    EXCEPT
    
    -- Seleciona os pontos onde o usuário já alugou (Dividendo)
    SELECT A.ponto_retirada_id
    FROM Aluguel A
    WHERE A.usuario_cpf = U.cpf
);

-- CONSULTA 2: JUNÇÃO INTERNA COM AGRUPAMENTO E ORDENAÇÃO
-- Relatório de uso dos veículos
-- Lista o modelo da bike, a quantidade total de aluguéis e a média 
-- das notas recebidas nos comentários (join com tabela Comentario_Bike), ordenando 
-- as bikes mais bem avaliadas primeiro.
-- Justificativa: Análise de qualidade da frota para decidir  
-- quais modelos comprar ou descontinuar.

SELECT 
    B.modelo,
    COUNT(A.id_aluguel) AS total_alugueis,
    ROUND(AVG(CB.nota), 2) AS media_nota_usuario
FROM Bike B
JOIN Aluguel A ON B.n_registro = A.bike_n_registro
JOIN Comentario_Bike CB ON A.id_aluguel = CB.aluguel_id
GROUP BY B.modelo
ORDER BY media_nota_usuario DESC;


-- CONSULTA 3: JUNÇÃO EXTERNA (LEFT JOIN) COM TRATAMENTO DE NULOS
-- Relatório de multas aplicadas.
-- Lista todos os usuários cadastrados e o valor total de multas que 
-- eles possuem em aberto (não pagas). Exibe R$ 0.00 caso não tenham multas.
-- Justificativa: Controle financeiro para identificar inadimplência  
-- e bloquear novos aluguéis via sistema.


SELECT 
    U.nome,
    U.cpf,
    COALESCE(SUM(M.valor), 0.00) AS total_divida_multas
FROM Usuario U
LEFT JOIN Aluguel A ON U.cpf = A.usuario_cpf
LEFT JOIN Multa M ON A.id_aluguel = M.aluguel_id AND M.isPaid = FALSE
GROUP BY U.cpf, U.nome
ORDER BY total_divida_multas DESC;



-- CONSULTA 4: CONSULTA ANINHADA CORRELACIONADA
-- Relatório de manutenções realizadas
-- Lista as bicicletas que estão atualmente em manutenção, mostrando 
-- há quantos dias estão paradas e qual o custo dessa manutenção, comparando 
-- com a média de custo de todas as manutenções do mesmo tipo.
-- Justificativa: Auditoria de custos de oficina para identificar manutenções 
-- que estão saindo mais caras que a média histórica.

SELECT 
    B.modelo,
    M.tipo AS tipo_manutencao,
    M.valor AS custo_atual,
    (CURRENT_DATE - M.data_inicio) AS dias_parada,
    (SELECT AVG(M2.valor) 
     FROM Manutencao M2 
     WHERE M2.tipo = M.tipo) AS media_custo_tipo
FROM Bike B
JOIN Manutencao M ON B.n_registro = M.bike_n_registro
WHERE M.data_fim IS NULL -- Manutenção ainda aberta
AND M.valor > (
    SELECT AVG(M2.valor) 
    FROM Manutencao M2 
    WHERE M2.tipo = M.tipo
);


-- CONSULTA 5: AGRUPAMENTO COM CLÁUSULA HAVING
-- Relatório de distribuição de veículos
-- Descrição: Listar os Pontos de Estacionamento (Nome da Rua) que tiveram 
-- movimentação alta (mais de 5 retiradas ou devoluções somadas) e cuja capacidade 
-- máxima é inferior a 30 bicicletas.
-- Justificativa: Identificar pontos pequenos que estão sobrecarregados 
-- e precisam de expansão física.
-- OBS: Como os dados de exemplo são poucos, a condição > 5 pode não retornar nada,
-- ajustado para > 1 para fins de teste da consulta.

SELECT 
    P.rua,
    P.bairro,
    P.capacidade_maxima,
    COUNT(A.id_aluguel) AS total_movimentacao
FROM Ponto P
JOIN Aluguel A ON P.cod_ponto = A.ponto_retirada_id OR P.cod_ponto = A.ponto_devolucao_id
WHERE P.capacidade_maxima < 30
GROUP BY P.cod_ponto, P.rua, P.bairro, P.capacidade_maxima
HAVING COUNT(A.id_aluguel) > 1 -- Ajustar este valor conforme volume de dados real
ORDER BY total_movimentacao DESC;