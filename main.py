import oracledb
import getpass
import datetime
import sys

# --- CONFIGURAÇÃO ---
DB_USER = 'seu_usuario'
DB_PASS = 'sua_senha' 
DB_DSN = 'localhost:1521/xe'

# Conexão com o banco de dados conforme documentação da biblioteca oracledb
def conectar_banco():
    try:
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
    except oracledb.Error as e:
        sys.exit(f"[ERRO CRÍTICO] Conexão falhou: {e}")


# MENU 1: RELATÓRIOS (Baseado em consultas.sql) ======

def menu_relatorios(conn):
    while True:
        print("\n--- [ADM] PAINEL DE RELATÓRIOS ---")
        print("1. Relatório de Fidelidade (Users que foram em TODOS os pontos de algum bairro de São Carlos)")
        print("2. Ranking de Melhores Bikes (Agrupamento e Média)")
        print("3. Relatório de Inadimplência")
        print("4. Auditoria de Manutenção")
        print("5. Pontos Sobrecarregados")
        print("0. Voltar")
        op = input("Selecione o relatório: ")

        if op == '0': break
        
        cursor = conn.cursor()
        try:
            if op == '1':
                # CONSULTA 1: DIVISÃO RELACIONAL
                sql = """
                SELECT U.nome FROM Usuario U
                WHERE NOT EXISTS (
                    SELECT P.cod_ponto FROM Ponto P
                    WHERE P.bairro = 'Centro' AND p.cidade = 'São Carlos'
                    MINUS
                    SELECT A.ponto_retirada_id FROM Aluguel A
                    WHERE A.usuario_cpf = U.cpf
                )
                """
                print("\n>>> USUÁRIOS 'POWER USER' (Fidelidade Centro):")
                cursor.execute(sql)
                
            elif op == '2':
                # CONSULTA 2: JUNÇÃO INTERNA COM AGRUPAMENTO
                sql = """
                SELECT B.modelo, COUNT(A.id_aluguel), ROUND(AVG(CB.nota), 2)
                FROM Bike B
                JOIN Aluguel A ON B.n_registro = A.bike_n_registro
                JOIN Comentario_Bike CB ON A.id_aluguel = CB.aluguel_id
                GROUP BY B.modelo ORDER BY 3 DESC
                """
                print("\n>>> RANKING DE BIKES:")
                cursor.execute(sql)

            elif op == '3':
                # CONSULTA 3: LEFT JOIN
                sql = """
                SELECT U.nome, U.cpf, COALESCE(SUM(M.valor), 0.00)
                FROM Usuario U
                LEFT JOIN Aluguel A ON U.cpf = A.usuario_cpf
                LEFT JOIN Multa M ON A.id_aluguel = M.aluguel_id AND M.isPaid = 0
                GROUP BY U.cpf, U.nome ORDER BY 3 DESC
                """
                print("\n>>> RELATÓRIO DE DÍVIDAS:")
                cursor.execute(sql)

            elif op == '4':
                # CONSULTA 4: ANINHADA CORRELACIONADA
                sql = """
                SELECT B.modelo, M.tipo, M.valor, (SYSDATE - M.data_inicio)
                FROM Bike B JOIN Manutencao M ON B.n_registro = M.bike_n_registro
                WHERE M.data_fim IS NULL
                AND M.valor > (SELECT AVG(M2.valor) FROM Manutencao M2 WHERE M2.tipo = M.tipo)
                """
                print("\n>>> MANUTENÇÕES ACIMA DA MÉDIA DE CUSTO:")
                cursor.execute(sql)

            elif op == '5':
                # CONSULTA 5: HAVING
                sql = """
                SELECT P.rua, P.bairro, COUNT(A.id_aluguel)
                FROM Ponto P
                JOIN Aluguel A ON P.cod_ponto = A.ponto_retirada_id OR P.cod_ponto = A.ponto_devolucao_id
                WHERE P.capacidade_maxima < 30
                GROUP BY P.cod_ponto, P.rua, P.bairro, P.capacidade_maxima
                HAVING COUNT(A.id_aluguel) > 1
                ORDER BY 3 DESC
                """
                print("\n>>> PONTOS PEQUENOS COM ALTA MOVIMENTAÇÃO:")
                cursor.execute(sql)
            
            # Exibição dos Resultados
            rows = cursor.fetchall()
            if not rows:
                print("   (Nenhum registro encontrado para esta consulta)")
            for row in rows:
                print(f"   - {row}")
                
        except oracledb.Error as e:
            print(f"[ERRO SQL] {e}")
        finally:
            cursor.close()


# GESTÃO DOS PONTOS E BIKES ======

def cadastrar_ponto(conn):
    print("\n--- NOVO PONTO DE ESTACIONAMENTO ---")
    rua = input("Rua: ")
    bairro = input("Bairro: ")
    cidade = input("Cidade: ")
    uf = input("UF: ")
    cap = input("Capacidade Máxima: ")
    
    sql = "INSERT INTO Ponto (rua, bairro, cidade, uf, capacidade_maxima) VALUES (:1, :2, :3, :4, :5)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (rua, bairro, cidade, uf, cap))
        conn.commit()
        print("[SUCESSO] Ponto registrado.")
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] {e}")

def cadastrar_bike(conn):
    print("\n--- NOVA BICICLETA ---")
    modelo = input("Modelo: ")
    ano = input("Ano: ")
    cor = input("Cor: ")
    ponto_id = input("ID do Ponto de Estacionamento Inicial: ")
    
    # Bike nasce com 0 aluguéis e tempo 0
    sql = """
        INSERT INTO Bike (modelo, ano_fabricacao, cor, status, qnt_alugueis, tempo_total_utilizado, ponto_atual_id)
        VALUES (:1, :2, :3, 'DISPONIVEL', 0, 0, :4)
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (modelo, ano, cor, ponto_id))
        conn.commit()
        print("[SUCESSO] Bicicleta adicionada à frota.")
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] Verifique se o ID do ponto existe. Detalhes: {e}")


# MANUTENÇÃO E DEVOLUÇÃO DE BIKES  ======

def gerir_manutencao(conn):
    print("\n--- GESTÃO DE MANUTENÇÃO ---")
    print("1. Enviar Bike para Manutenção (Início)")
    print("2. Receber Bike da Manutenção (Fim)")
    op = input("Opção: ")
    
    cursor = conn.cursor()
    try:
        if op == '1':
            bike_id = input("ID da Bike: ")
            tipo = input("Tipo (PREVENTIVA/CORRETIVA/ANTECIPADA): ").upper()
            problema = input("Descrição do problema: ")
            
            # Transação Complexa:
            # 1. Verifica se bike pode ir pra manutenção (não pode estar EM_USO)
            cursor.execute("SELECT status FROM Bike WHERE n_registro = :1", (bike_id,))
            row = cursor.fetchone()
            if row and row[0] == 'EM_USO':
                print("[BLOQUEIO] Bike está alugada. Aguarde devolução.")
                return

            # 2. Insere registro de manutenção
            # 3. Atualiza status da bike [cite: 102]
            sql_insert = """
                INSERT INTO Manutencao (bike_n_registro, tipo, data_inicio, descricao_problema, valor)
                VALUES (:1, :2, SYSDATE, :3, 0)
            """
            sql_update = "UPDATE Bike SET status = 'MANUTENCAO', ponto_atual_id = NULL WHERE n_registro = :1"
            
            cursor.execute(sql_insert, (bike_id, tipo, problema))
            cursor.execute(sql_update, (bike_id,))
            conn.commit()
            print("[SUCESSO] Ordem de serviço aberta e Bike retirada de circulação.")

        elif op == '2':
            bike_id = input("ID da Bike voltando da oficina: ")
            custo = input("Custo final do reparo: ")
            ponto_novo = input("ID do Ponto onde ela será colocada: ")
            
            # Atualiza Manutenção (Fim) e Bike (Disponível)
            sql_manut = """
                UPDATE Manutencao SET data_fim = SYSDATE, valor = :1 
                WHERE bike_n_registro = :2 AND data_fim IS NULL
            """
            sql_bike = "UPDATE Bike SET status = 'DISPONIVEL', ponto_atual_id = :1 WHERE n_registro = :2"
            
            cursor.execute(sql_manut, (custo, bike_id))
            if cursor.rowcount == 0:
                print("[ERRO] Nenhuma manutenção aberta encontrada para essa bike.")
                conn.rollback()
            else:
                cursor.execute(sql_bike, (ponto_novo, bike_id))
                conn.commit()
                print("[SUCESSO] Bike disponível novamente.")

    except Exception as e:
        conn.rollback()
        print(f"[ERRO] {e}")
    finally:
        cursor.close()

def realizar_devolucao(conn):
    """
    Simula o encerramento de um aluguel.
    Cumpre a regra de atualizar estatísticas da bike via aplicação.
    """
    print("\n--- DEVOLUÇÃO DE BIKE ---")
    aluguel_id = input("ID do Aluguel: ")
    ponto_dest = input("ID do Ponto de Devolução: ")
    
    cursor = conn.cursor()
    try:
        # 1. Busca dados do aluguel para calcular tempo
        cursor.execute("SELECT bike_n_registro, data_hora_inicio FROM Aluguel WHERE id_aluguel = :1", (aluguel_id,))
        dados = cursor.fetchone()
        if not dados:
            print("Aluguel não encontrado.")
            return
            
        bike_id, inicio = dados
        agora = datetime.datetime.now()
        
        # Cálculo Python de tempo (minutos)
        duracao = (agora - inicio).total_seconds() / 60
        
        # 2. Atualiza Tabela Aluguel
        sql_aluguel = """
            UPDATE Aluguel SET 
                data_hora_fim = SYSDATE, 
                ponto_devolucao_id = :1, 
                status = 'CONCLUIDO' 
            WHERE id_aluguel = :2
        """
        cursor.execute(sql_aluguel, (ponto_dest, aluguel_id))
        
        # 3. Atualiza Tabela Bike
        # "Nota: qnt_alugueis e tempo_total_utilizado serão inseridos/atualizados de acordo com cálculos feitos pela aplicação"
        sql_bike_stats = """
            UPDATE Bike SET 
                status = 'DISPONIVEL',
                ponto_atual_id = :1,
                qnt_alugueis = qnt_alugueis + 1,
                tempo_total_utilizado = tempo_total_utilizado + :2
            WHERE n_registro = :3
        """
        cursor.execute(sql_bike_stats, (ponto_dest, duracao, bike_id))
        
        conn.commit()
        print(f"[SUCESSO] Devolução realizada. Tempo de uso: {int(duracao)} min.")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERRO NA TRANSAÇÃO] {e}")
    finally:
        cursor.close()


# MENU PRINCIPAL  ======

def main():
    global DB_PASS
    if not DB_PASS:
        DB_PASS = getpass.getpass("Senha Oracle: ")
        
    conn = conectar_banco()
    
    while True:
        print("\n=== SISTEMA DE GESTÃO DE BIKES CIRCULARES ===")
        print("1. Relatórios Gerenciais")
        print("2. Cadastrar Usuário")
        print("3. Cadastrar Ponto de Estacionamento")
        print("4. Cadastrar Nova Bike")
        print("5. Gerir Manutenção (Início/Fim)")
        print("6. Informar Devolução")
        print("0. Sair")
        
        op = input("Escolha: ")
        
        if op == '1': menu_relatorios(conn)
        elif op == '2': print("Funcionalidade de usuário") # Simplificado para focar no novo
        elif op == '3': cadastrar_ponto(conn)
        elif op == '4': cadastrar_bike(conn)
        elif op == '5': gerir_manutencao(conn)
        elif op == '6': realizar_devolucao(conn)
        elif op == '0': break
        else: print("Inválido.")
        
    conn.close()

if __name__ == "__main__":
    main()