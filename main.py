import oracledb
import getpass
import datetime
import sys

# --- CONFIGURAÇÃO ---
# Ajuste aqui com seus dados reais do Oracle
DB_USER = 'system'     # Ex: 'system' ou seu RM
DB_PASS = 'oracle'     # Sua senha
DB_DSN = 'localhost:1521/xe' # Endereço do banco

def conectar_banco():
    """Estabelece a conexão com o banco de dados Oracle"""
    try:
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
    except oracledb.Error as e:
        sys.exit(f"[ERRO CRÍTICO] Conexão falhou: {e}")


def cadastrar_usuario(conn):
    print("\n--- CADASTRO UNIFICADO (USUÁRIO + CARTÃO) ---")
    
    try:
        print(">> Dados Pessoais:")
        cpf = input("CPF (apenas números): ").strip()
        nome = input("Nome Completo: ").strip()
        data_nasc = input("Data de Nascimento (DD/MM/AAAA): ").strip()
        rua = input("Rua: ").strip()
        numero = input("Número: ").strip()
        bairro = input("Bairro: ").strip()
        cidade = input("Cidade: ").strip()
        uf = input("UF (2 letras): ").strip().upper()
        cad_unico_in = input("Possui CadÚnico? (S/N): ").strip().upper()
        is_cad_unico = 1 if cad_unico_in == 'S' else 0

        print("\n>> Emissão do Cartão:")
        saldo = input("Saldo Inicial (R$): ").strip().replace(',', '.')
        validade = input("Validade do Cartão (DD/MM/AAAA): ").strip()

        cursor = conn.cursor()

        sql_usuario = """
            INSERT INTO Usuario (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cadUnico)
            VALUES (:1, :2, TO_DATE(:3, 'DD/MM/YYYY'), :4, :5, :6, :7, :8, :9)
        """
        cursor.execute(sql_usuario, (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cad_unico))

        sql_cartao = """
            INSERT INTO Cartao (usuario_cpf, saldo, data_validade, data_emissao)
            VALUES (:1, :2, TO_DATE(:3, 'DD/MM/YYYY'), SYSDATE)
        """
        cursor.execute(sql_cartao, (cpf, saldo, validade))

        conn.commit()
        print(f"\n[SUCESSO] Usuário {nome} cadastrado e cartão emitido com saldo de R$ {saldo}!")

    except oracledb.DatabaseError as e:
        conn.rollback()
        error, = e.args
        print(f"\n[ERRO DE BANCO] Falha no cadastro: {error.message}")
        print("Transação desfeita. Nenhum dado foi salvo.")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO GENÉRICO] {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()

def registrar_aluguel(conn):
    print("\n--- NOVO ALUGUEL ---")
    
    # 1. Coleta de dados
    cpf = input("CPF do Usuário: ")
    bike_id = input("Número de Registro da Bike: ")
    ponto_id = input("ID do Ponto de Retirada: ")

    cursor = conn.cursor()
    try:
        # Valida usuário e multa
        sql_user_check = """
            SELECT U.nome, 
                   (SELECT COUNT(*) FROM Aluguel A 
                    JOIN Multa M ON A.id_aluguel = M.aluguel_id 
                    WHERE A.usuario_cpf = U.cpf AND M.isPaid = 0) as multas_pendentes
            FROM Usuario U 
            WHERE U.cpf = :1
        """
        cursor.execute(sql_user_check, (cpf,))
        user_data = cursor.fetchone()

        if not user_data:
            print(f"[ERRO] Usuário com CPF {cpf} não encontrado.")
            return
        
        nome, multas = user_data
        if multas > 0:
            print(f"[BLOQUEIO] O usuário {nome} possui {multas} multa(s) pendente(s). Regularize antes de alugar.")
            return


        # Validar disponibilidade e local da bike
        sql_bike_check = "SELECT status, ponto_atual_id FROM Bike WHERE n_registro = :1"
        cursor.execute(sql_bike_check, (bike_id,))
        bike_data = cursor.fetchone()

        if not bike_data:
            print("[ERRO] Bicicleta não encontrada.")
            return
        
        status, ponto_atual = bike_data
        
        if status != 'DISPONIVEL':
            print(f"[ERRO] Bike indisponível. Status atual: {status}")
            return
        

        print(f"Autorizando aluguel para {nome}...")

        sql_insert_aluguel = """
            INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, data_hora_inicio, status)
            VALUES (:1, :2, :3, SYSTIMESTAMP, 'EM_ANDAMENTO')
        """
        cursor.execute(sql_insert_aluguel, (bike_id, cpf, ponto_id))

        # Atualização da Bike para status 'EM_USO'
        sql_update_bike = "UPDATE Bike SET status = 'EM_USO' WHERE n_registro = :1"
        cursor.execute(sql_update_bike, (bike_id,))

        # Efetiva a transação
        conn.commit()
        print(f"[SUCESSO] Aluguel registrado! Boa viagem, {nome}.")

    except oracledb.DatabaseError as e:
        conn.rollback()
        error, = e.args
        print(f"[ERRO DE BANCO] Não foi possível registrar o aluguel: {error.message}")
    except Exception as e:
        conn.rollback()
        print(f"[ERRO GENÉRICO] {e}")
    finally:
        cursor.close()


def menu_relatorios(conn):
    while True:
        print("\n--- [ADM] PAINEL DE RELATÓRIOS ---")
        print("1. Relatório de Fidelidade (Users em todos pontos do Centro)")
        print("2. Ranking de Melhores Bikes")
        print("3. Relatório de Inadimplência")
        print("4. Auditoria de Manutenção")
        print("5. Pontos Sobrecarregados")
        print("0. Voltar")
        op = input("Selecione o relatório: ")

        if op == '0': break
        
        cursor = conn.cursor()
        try:
            if op == '1':
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
                sql = """
                SELECT B.modelo, M.tipo, M.valor, (SYSDATE - M.data_inicio)
                FROM Bike B JOIN Manutencao M ON B.n_registro = M.bike_n_registro
                WHERE M.data_fim IS NULL
                AND M.valor > (SELECT AVG(M2.valor) FROM Manutencao M2 WHERE M2.tipo = M.tipo)
                """
                print("\n>>> MANUTENÇÕES ACIMA DA MÉDIA DE CUSTO:")
                cursor.execute(sql)

            elif op == '5':
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
            
            rows = cursor.fetchall()
            if not rows:
                print("   (Nenhum registro encontrado para esta consulta)")
            for row in rows:
                print(f"   - {row}")
                
        except oracledb.Error as e:
            print(f"[ERRO SQL] {e}")
        finally:
            cursor.close()

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
            
            cursor.execute("SELECT status FROM Bike WHERE n_registro = :1", (bike_id,))
            row = cursor.fetchone()
            if row and row[0] == 'EM_USO':
                print("[BLOQUEIO] Bike está alugada. Aguarde devolução.")
                return

            sql_insert = """
                INSERT INTO Manutencao (bike_n_registro, tipo, data_inicio, descricao_problema, valor)
                VALUES (:1, :2, SYSDATE, :3, 0)
            """
            sql_update = "UPDATE Bike SET status = 'MANUTENCAO', ponto_atual_id = NULL WHERE n_registro = :1"
            
            cursor.execute(sql_insert, (bike_id, tipo, problema))
            cursor.execute(sql_update, (bike_id,))
            conn.commit()
            print("[SUCESSO] Ordem de serviço aberta.")

        elif op == '2':
            bike_id = input("ID da Bike voltando da oficina: ")
            custo = input("Custo final do reparo: ")
            ponto_novo = input("ID do Ponto onde ela será colocada: ")
            
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
    print("\n--- DEVOLUÇÃO DE BIKE ---")
    aluguel_id = input("ID do Aluguel: ")
    ponto_dest = input("ID do Ponto de Devolução: ")
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT bike_n_registro, data_hora_inicio FROM Aluguel WHERE id_aluguel = :1", (aluguel_id,))
        dados = cursor.fetchone()
        if not dados:
            print("Aluguel não encontrado.")
            return
            
        bike_id, inicio = dados
        agora = datetime.datetime.now()
        duracao = (agora - inicio).total_seconds() / 60
        
        sql_aluguel = """
            UPDATE Aluguel SET 
                data_hora_fim = SYSDATE, 
                ponto_devolucao_id = :1, 
                status = 'CONCLUIDO' 
            WHERE id_aluguel = :2
        """
        cursor.execute(sql_aluguel, (ponto_dest, aluguel_id))
        
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


# MENU PRINCIPAL 

def main():
    global DB_PASS # Se senha não estiver na variável, pede pro usuário
    if not DB_PASS:
        DB_PASS = getpass.getpass("Senha Oracle: ")
        
    conn = conectar_banco()
    print("✅ Conectado ao banco com sucesso!")
    
    while True:
        print("\n=== SISTEMA DE GESTÃO DE BIKES CIRCULARES ===")
        print("1. Relatórios Gerenciais")
        print("2. Cadastrar Usuário e Cartão")
        print("3. Cadastrar Ponto de Estacionamento")
        print("4. Cadastrar Nova Bike")
        print("5. Gerir Manutenção (Início/Fim)")
        print("6. Realizar aluguel")
        print("7. Informar Devolução")
        print("0. Sair")
        
        op = input("Escolha: ")
        
        if op == '1': menu_relatorios(conn)
        elif op == '2': cadastrar_usuario(conn)
        elif op == '3': cadastrar_ponto(conn)
        elif op == '4': cadastrar_bike(conn)
        elif op == '5': gerir_manutencao(conn)
        elif op == '6': registrar_aluguel(conn)
        elif op == '7': realizar_devolucao(conn)
        elif op == '0': break
        else: print("Opção inválida")
        
    conn.close()

if __name__ == "__main__":
    main()