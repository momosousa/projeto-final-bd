import oracledb
import getpass
import datetime
import re
import sys
from datetime import datetime as dt

# --- CONFIGURAÇÃO ---
DB_USER = 'system'
DB_PASS = 'oracle'
DB_DSN = 'localhost:1521/xe'

# --- FUNÇÕES AUXILIARES DE VALIDAÇÃO ---
def validar_cpf(cpf):
    """Valida se o CPF tem 11 dígitos numéricos"""
    return cpf.isdigit() and len(cpf) == 11

def validar_data(data_str, formato='%d/%m/%Y'):
    """Valida se a data está no formato correto"""
    try:
        dt.strptime(data_str, formato)
        return True
    except ValueError:
        return False

def validar_data_futura(data_str, formato='%d/%m/%Y'):
    """Valida se a data é futura"""
    try:
        data = dt.strptime(data_str, formato)
        return data.date() > dt.now().date()
    except ValueError:
        return False

def validar_data_passado(data_str, formato='%d/%m/%Y'):
    """Valida se a data é no passado (para nascimento)"""
    try:
        data = dt.strptime(data_str, formato)
        return data.date() < dt.now().date()
    except ValueError:
        return False

def validar_uf(uf):
    """Valida UF (2 letras maiúsculas)"""
    return len(uf) == 2 and uf.isalpha() and uf.isupper()

def validar_numero_positivo(valor_str, decimal=False):
    """Valida número positivo"""
    try:
        if decimal:
            valor = float(valor_str)
            return valor >= 0
        else:
            valor = int(valor_str)
            return valor > 0
    except ValueError:
        return False

def validar_email(email):
    """Valida formato de email básico"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefone(telefone):
    """Valida telefone (10 ou 11 dígitos)"""
    telefone_limpo = re.sub(r'\D', '', telefone)
    return len(telefone_limpo) in [10, 11]

def validar_sn(resposta):
    """Valida resposta Sim/Não"""
    return resposta.upper() in ['S', 'N']

def validar_tipo_manutencao(tipo):
    """Valida tipo de manutenção"""
    return tipo.upper() in ['PREVENTIVA', 'CORRETIVA', 'ANTECIPADA']

def validar_status_bike(status):
    """Valida status da bike"""
    return status.upper() in ['DISPONIVEL', 'EM_USO', 'MANUTENCAO']

def formatar_cpf(cpf):
    """Formata CPF para exibição"""
    cpf_limpo = re.sub(r'\D', '', cpf)
    if len(cpf_limpo) == 11:
        return f'{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}'
    return cpf

def conectar_banco():
    """Estabelece a conexão com o banco de dados Oracle"""
    try:
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
    except oracledb.Error as e:
        sys.exit(f"[ERRO CRÍTICO] Conexão falhou: {e}")

# --- FUNÇÕES PRINCIPAIS COM VALIDAÇÕES ---
def cadastrar_usuario(conn):
    print("\n--- CADASTRO UNIFICADO (USUÁRIO + CARTÃO) ---")
    
    try:
        print(">> Dados Pessoais:")
        
        # Validação CPF
        while True:
            cpf = input("CPF (apenas números, 11 dígitos): ").strip()
            if validar_cpf(cpf):
                # Verifica se CPF já existe
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Usuario WHERE cpf = :1", (cpf,))
                if cursor.fetchone()[0] > 0:
                    print(f"[ERRO] CPF {formatar_cpf(cpf)} já cadastrado!")
                    cursor.close()
                    continue
                cursor.close()
                break
            else:
                print("[ERRO] CPF inválido! Deve conter exatamente 11 números.")
        
        # Nome (obrigatório)
        while True:
            nome = input("Nome Completo: ").strip()
            if nome and len(nome) >= 3:
                break
            print("[ERRO] Nome deve ter pelo menos 3 caracteres.")
        
        # Data de Nascimento
        while True:
            data_nasc = input("Data de Nascimento (DD/MM/AAAA): ").strip()
            if validar_data(data_nasc) and validar_data_passado(data_nasc):
                break
            print("[ERRO] Data inválida ou futura! Use formato DD/MM/AAAA.")
        
        # Endereço
        rua = input("Rua: ").strip() or None
        numero = input("Número: ").strip() or None
        bairro = input("Bairro: ").strip() or None
        
        while True:
            cidade = input("Cidade: ").strip()
            if cidade:
                break
            print("[ERRO] Cidade é obrigatória.")
        
        while True:
            uf = input("UF (2 letras): ").strip().upper()
            if validar_uf(uf):
                break
            print("[ERRO] UF inválida! Use 2 letras (ex: SP, RJ).")
        
        # CadÚnico
        while True:
            cad_unico_in = input("Possui CadÚnico? (S/N): ").strip().upper()
            if validar_sn(cad_unico_in):
                is_cad_unico = 1 if cad_unico_in == 'S' else 0
                break
            print("[ERRO] Digite apenas 'S' ou 'N'.")
        
        print("\n>> Emissão do Cartão:")
        
        # Saldo
        while True:
            saldo_str = input("Saldo Inicial (R$): ").strip().replace(',', '.')
            if validar_numero_positivo(saldo_str, decimal=True):
                saldo = float(saldo_str)
                break
            print("[ERRO] Saldo deve ser um número positivo (ex: 50.00).")
        
        # Validade do cartão (mínimo 1 mês, máximo 5 anos)
        while True:
            validade = input("Validade do Cartão (DD/MM/AAAA): ").strip()
            if validar_data(validade):
                data_validade = dt.strptime(validade, '%d/%m/%Y')
                data_minima = dt.now() + datetime.timedelta(days=30)
                data_maxima = dt.now() + datetime.timedelta(days=5*365)
                
                if data_validade.date() < data_minima.date():
                    print("[ERRO] Validade deve ser pelo menos 1 mês à frente.")
                elif data_validade.date() > data_maxima.date():
                    print("[ERRO] Validade não pode ultrapassar 5 anos.")
                else:
                    break
            else:
                print("[ERRO] Data inválida! Use formato DD/MM/AAAA.")
        
        cursor = conn.cursor()
        
        # Inserir usuário
        sql_usuario = """
            INSERT INTO Usuario (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cadUnico)
            VALUES (:1, :2, TO_DATE(:3, 'DD/MM/YYYY'), :4, :5, :6, :7, :8, :9)
        """
        cursor.execute(sql_usuario, (cpf, nome, data_nasc, rua, numero, bairro, cidade, uf, is_cad_unico))
        
        # Inserir cartão
        sql_cartao = """
            INSERT INTO Cartao (usuario_cpf, saldo, data_validade, data_emissao)
            VALUES (:1, :2, TO_DATE(:3, 'DD/MM/YYYY'), SYSDATE)
        """
        cursor.execute(sql_cartao, (cpf, saldo, validade))
        
        conn.commit()
        print(f"\n✅ [SUCESSO] Usuário {nome} cadastrado com sucesso!")
        print(f"   CPF: {formatar_cpf(cpf)}")
        print(f"   Cartão emitido com saldo: R$ {saldo:.2f}")
        print(f"   Validade: {validade}")
        
    except oracledb.DatabaseError as e:
        conn.rollback()
        error, = e.args
        print(f"\n❌ [ERRO DE BANCO] Falha no cadastro: {error.message}")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ [ERRO] {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()

def registrar_aluguel(conn):
    print("\n--- NOVO ALUGUEL ---")
    
    cursor = conn.cursor()
    try:
        # Validação CPF
        while True:
            cpf = input("CPF do Usuário (11 dígitos): ").strip()
            if validar_cpf(cpf):
                break
            print("[ERRO] CPF inválido! 11 dígitos necessários.")
        
        # Verificar usuário
        sql_user_check = """
            SELECT U.nome, C.saldo,
                   (SELECT COUNT(*) FROM Aluguel A 
                    JOIN Multa M ON A.id_aluguel = M.aluguel_id 
                    WHERE A.usuario_cpf = U.cpf AND M.isPaid = 0) as multas_pendentes
            FROM Usuario U 
            LEFT JOIN Cartao C ON U.cpf = C.usuario_cpf
            WHERE U.cpf = :1
        """
        cursor.execute(sql_user_check, (cpf,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print(f"❌ [ERRO] Usuário com CPF {formatar_cpf(cpf)} não encontrado.")
            return
        
        nome, saldo, multas = user_data
        
        if multas > 0:
            print(f"❌ [BLOQUEIO] Usuário {nome} possui {multas} multa(s) pendente(s).")
            return
        
        # Verificar saldo mínimo (R$ 5.00)
        if saldo is None or saldo < 5.00:
            print(f"❌ [BLOQUEIO] Saldo insuficiente. Mínimo necessário: R$ 5.00")
            print(f"   Saldo atual: R$ {saldo:.2f if saldo else 0.00}")
            return
        
        # Validação Bike ID
        while True:
            bike_id_str = input("Número de Registro da Bike: ").strip()
            if validar_numero_positivo(bike_id_str):
                bike_id = int(bike_id_str)
                break
            print("[ERRO] ID da bike deve ser um número positivo.")
        
        # Verificar bike
        sql_bike_check = """
            SELECT B.status, B.ponto_atual_id, P.rua, P.bairro
            FROM Bike B 
            LEFT JOIN Ponto P ON B.ponto_atual_id = P.cod_ponto
            WHERE B.n_registro = :1
        """
        cursor.execute(sql_bike_check, (bike_id,))
        bike_data = cursor.fetchone()
        
        if not bike_data:
            print("❌ [ERRO] Bicicleta não encontrada.")
            return
        
        status, ponto_atual, rua, bairro = bike_data
        
        if status != 'DISPONIVEL':
            print(f"❌ [ERRO] Bike indisponível. Status atual: {status}")
            return
        
        print(f"\n📍 Bike disponível no ponto: {rua}, {bairro}")
        print(f"👤 Usuário: {nome}")
        print(f"💳 Saldo disponível: R$ {saldo:.2f}")
        
        # Confirmar aluguel
        while True:
            confirmar = input("\nConfirmar aluguel? (S/N): ").strip().upper()
            if validar_sn(confirmar):
                break
            print("[ERRO] Digite S ou N.")
        
        if confirmar != 'S':
            print("Aluguel cancelado pelo usuário.")
            return
        
        # Registrar aluguel
        sql_insert_aluguel = """
            INSERT INTO Aluguel (bike_n_registro, usuario_cpf, ponto_retirada_id, 
                                data_hora_inicio, status)
            VALUES (:1, :2, :3, SYSTIMESTAMP, 'EM_ANDAMENTO')
        """
        cursor.execute(sql_insert_aluguel, (bike_id, cpf, ponto_atual))
        
        # Atualizar bike
        sql_update_bike = "UPDATE Bike SET status = 'EM_USO' WHERE n_registro = :1"
        cursor.execute(sql_update_bike, (bike_id,))
        
        conn.commit()
        print(f"\n✅ [SUCESSO] Aluguel registrado!")
        print(f"   Bike: {bike_id}")
        print(f"   Usuário: {nome}")
        print(f"   Hora de início: {datetime.datetime.now().strftime('%H:%M')}")
        
    except oracledb.DatabaseError as e:
        conn.rollback()
        error, = e.args
        print(f"❌ [ERRO DE BANCO] Não foi possível registrar o aluguel: {error.message}")
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERRO] {e}")
    finally:
        cursor.close()

def menu_relatorios(conn):
    while True:
        print("\n" + "="*50)
        print("📊 [ADM] PAINEL DE RELATÓRIOS")
        print("="*50)
        print("1. Relatório de Fidelidade (Users em todos pontos do Centro)")
        print("2. Ranking de Melhores Bikes")
        print("3. Relatório de Inadimplência")
        print("4. Auditoria de Manutenção")
        print("5. Pontos Sobrecarregados")
        print("6. Histórico de Usuário")
        print("0. Voltar")
        
        while True:
            op = input("\nSelecione o relatório (0-6): ").strip()
            if op in ['0', '1', '2', '3', '4', '5', '6']:
                break
            print("[ERRO] Digite um número entre 0 e 6.")
        
        if op == '0': 
            break
        
        cursor = conn.cursor()
        try:
            if op == '1':
                print("\n📋 USUÁRIOS 'POWER USER' (Fidelidade Centro)")
                print("-" * 50)
                sql = """
                SELECT U.nome, U.cpf, COUNT(DISTINCT A.ponto_retirada_id) as pontos_centro
                FROM Usuario U
                JOIN Aluguel A ON U.cpf = A.usuario_cpf
                JOIN Ponto P ON A.ponto_retirada_id = P.cod_ponto
                WHERE P.bairro = 'Centro' AND P.cidade = 'São Carlos'
                GROUP BY U.cpf, U.nome
                HAVING COUNT(DISTINCT A.ponto_retirada_id) = (
                    SELECT COUNT(*) FROM Ponto 
                    WHERE bairro = 'Centro' AND cidade = 'São Carlos'
                )
                ORDER BY pontos_centro DESC
                """
                cursor.execute(sql)
                
            elif op == '2':
                print("\n🏆 RANKING DE BIKES (por avaliação)")
                print("-" * 50)
                sql = """
                SELECT B.n_registro, B.modelo, 
                       COUNT(A.id_aluguel) as total_alugueis,
                       ROUND(AVG(CB.nota), 2) as nota_media,
                       SUM(B.tempo_total_utilizado) as horas_uso
                FROM Bike B
                LEFT JOIN Aluguel A ON B.n_registro = A.bike_n_registro
                LEFT JOIN Comentario_Bike CB ON A.id_aluguel = CB.aluguel_id
                GROUP BY B.n_registro, B.modelo 
                HAVING COUNT(A.id_aluguel) > 0
                ORDER BY nota_media DESC NULLS LAST
                FETCH FIRST 10 ROWS ONLY
                """
                cursor.execute(sql)
                
            elif op == '3':
                print("\n💰 RELATÓRIO DE DÍVIDAS")
                print("-" * 50)
                sql = """
                SELECT U.nome, U.cpf, 
                       COUNT(M.id_multa) as multas_pendentes,
                       COALESCE(SUM(M.valor), 0.00) as valor_total
                FROM Usuario U
                LEFT JOIN Aluguel A ON U.cpf = A.usuario_cpf
                LEFT JOIN Multa M ON A.id_aluguel = M.aluguel_id AND M.isPaid = 0
                GROUP BY U.cpf, U.nome 
                HAVING COALESCE(SUM(M.valor), 0) > 0
                ORDER BY valor_total DESC
                """
                cursor.execute(sql)
                
            elif op == '4':
                print("\n🔧 AUDITORIA DE MANUTENÇÃO")
                print("-" * 50)
                sql = """
                SELECT B.n_registro, B.modelo, 
                       M.tipo, M.valor, 
                       M.data_inicio,
                       (SYSDATE - M.data_inicio) as dias_em_manutencao,
                       M.descricao_problema
                FROM Bike B 
                JOIN Manutencao M ON B.n_registro = M.bike_n_registro
                WHERE M.data_fim IS NULL
                ORDER BY dias_em_manutencao DESC
                """
                cursor.execute(sql)
                
            elif op == '5':
                print("\n⚠️ PONTOS COM ALTA OCUPAÇÃO")
                print("-" * 50)
                sql = """
                SELECT P.cod_ponto, P.rua, P.bairro, P.capacidade_maxima,
                       COUNT(A.id_aluguel) as movimentacoes,
                       ROUND(COUNT(A.id_aluguel) / P.capacidade_maxima * 100, 2) as taxa_ocupacao
                FROM Ponto P
                JOIN Aluguel A ON (P.cod_ponto = A.ponto_retirada_id OR P.cod_ponto = A.ponto_devolucao_id)
                WHERE A.data_hora_inicio >= SYSDATE - 30
                GROUP BY P.cod_ponto, P.rua, P.bairro, P.capacidade_maxima
                HAVING COUNT(A.id_aluguel) > P.capacidade_maxima * 0.8
                ORDER BY taxa_ocupacao DESC
                """
                cursor.execute(sql)
                
            elif op == '6':
                print("\n👤 HISTÓRICO COMPLETO DO USUÁRIO")
                print("-" * 50)
                while True:
                    cpf_hist = input("Digite o CPF do usuário: ").strip()
                    if validar_cpf(cpf_hist):
                        break
                    print("[ERRO] CPF inválido!")
                
                sql = """
                SELECT U.nome, COUNT(A.id_aluguel) as total_alugueis,
                       COALESCE(SUM(A.periodo_alugado), 0) as minutos_totais,
                       ROUND(AVG(CB.nota), 2) as nota_media_bikes,
                       ROUND(AVG(CP.nota), 2) as nota_media_pontos
                FROM Usuario U
                LEFT JOIN Aluguel A ON U.cpf = A.usuario_cpf
                LEFT JOIN Comentario_Bike CB ON A.id_aluguel = CB.aluguel_id
                LEFT JOIN Comentario_Ponto CP ON A.id_aluguel = CP.aluguel_id
                WHERE U.cpf = :1
                GROUP BY U.nome
                """
                cursor.execute(sql, (cpf_hist,))
                historico = cursor.fetchone()
                
                if historico:
                    nome, total, minutos, nota_bike, nota_ponto = historico
                    print(f"\n📊 RESUMO DO USUÁRIO: {nome}")
                    print(f"   Total de aluguéis: {total}")
                    print(f"   Tempo total de uso: {minutos} minutos ({minutos/60:.1f} horas)")
                    print(f"   Nota média das bikes: {nota_bike if nota_bike else 'N/A'}/10")
                    print(f"   Nota média dos pontos: {nota_ponto if nota_ponto else 'N/A'}/10")
                else:
                    print("Usuário não encontrado ou sem histórico.")
                continue
            
            rows = cursor.fetchall()
            if not rows:
                print("   📭 Nenhum registro encontrado para esta consulta")
            else:
                for i, row in enumerate(rows, 1):
                    print(f"{i:2}. {row}")
                print(f"\nTotal de registros: {len(rows)}")
                
        except oracledb.Error as e:
            print(f"❌ [ERRO SQL] {e}")
        finally:
            cursor.close()

def cadastrar_ponto(conn):
    print("\n📍 NOVO PONTO DE ESTACIONAMENTO")
    
    try:
        # Endereço
        while True:
            rua = input("Rua: ").strip()
            if rua:
                break
            print("[ERRO] Rua é obrigatória.")
        
        numero = input("Número: ").strip() or None
        bairro = input("Bairro: ").strip() or None
        
        while True:
            cidade = input("Cidade: ").strip()
            if cidade:
                break
            print("[ERRO] Cidade é obrigatória.")
        
        while True:
            uf = input("UF (2 letras): ").strip().upper()
            if validar_uf(uf):
                break
            print("[ERRO] UF inválida! Use 2 letras (ex: SP, RJ).")
        
        referencia = input("Referência/Complemento: ").strip() or None
        
        while True:
            cap_str = input("Capacidade Máxima (número inteiro positivo): ").strip()
            if validar_numero_positivo(cap_str):
                capacidade = int(cap_str)
                if capacidade <= 100:  # Limite razoável
                    break
                else:
                    print("[ERRO] Capacidade máxima muito alta (máx: 100).")
            else:
                print("[ERRO] Capacidade deve ser um número inteiro positivo.")
        
        cursor = conn.cursor()
        sql = """
            INSERT INTO Ponto (rua, numero, bairro, cidade, uf, referencia, capacidade_maxima)
            VALUES (:1, :2, :3, :4, :5, :6, :7)
        """
        cursor.execute(sql, (rua, numero, bairro, cidade, uf, referencia, capacidade))
        conn.commit()
        
        print(f"✅ [SUCESSO] Ponto registrado com capacidade para {capacidade} bikes.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERRO] {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()

def cadastrar_bike(conn):
    print("\n🚲 NOVA BICICLETA")
    
    cursor = conn.cursor()
    try:
        # Modelo
        while True:
            modelo = input("Modelo: ").strip()
            if modelo:
                break
            print("[ERRO] Modelo é obrigatório.")
        
        # Ano de fabricação (1900-ano atual)
        while True:
            ano_str = input(f"Ano de Fabricação (1900-{datetime.datetime.now().year}): ").strip()
            if validar_numero_positivo(ano_str):
                ano = int(ano_str)
                ano_atual = datetime.datetime.now().year
                if 1900 <= ano <= ano_atual:
                    break
                else:
                    print(f"[ERRO] Ano deve estar entre 1900 e {ano_atual}.")
            else:
                print("[ERRO] Ano deve ser um número inteiro.")
        
        cor = input("Cor: ").strip() or "Não especificada"
        
        # Ponto atual
        while True:
            ponto_id_str = input("ID do Ponto de Estacionamento Inicial: ").strip()
            if validar_numero_positivo(ponto_id_str):
                ponto_id = int(ponto_id_str)
                # Verificar se ponto existe
                cursor.execute("SELECT COUNT(*) FROM Ponto WHERE cod_ponto = :1", (ponto_id,))
                if cursor.fetchone()[0] > 0:
                    break
                else:
                    print("[ERRO] Ponto não encontrado. Verifique o ID.")
            else:
                print("[ERRO] ID do ponto deve ser um número positivo.")
        
        sql = """
            INSERT INTO Bike (modelo, ano_fabricacao, cor, status, qnt_alugueis, tempo_total_utilizado, ponto_atual_id)
            VALUES (:1, :2, :3, 'DISPONIVEL', 0, 0, :4)
        """
        cursor.execute(sql, (modelo, ano, cor, ponto_id))
        conn.commit()
        
        print(f"✅ [SUCESSO] Bicicleta {modelo} {ano} adicionada à frota.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERRO] {e}")
    finally:
        cursor.close()

def gerir_manutencao(conn):
    print("\n🔧 GESTÃO DE MANUTENÇÃO")
    
    cursor = conn.cursor()
    try:
        while True:
            print("\n1. Enviar Bike para Manutenção (Início)")
            print("2. Receber Bike da Manutenção (Fim)")
            print("0. Voltar")
            
            op = input("Opção (0-2): ").strip()
            if op in ['0', '1', '2']:
                break
            print("[ERRO] Digite 0, 1 ou 2.")
        
        if op == '0':
            return
        
        elif op == '1':
            # Validar bike ID
            while True:
                bike_id_str = input("ID da Bike: ").strip()
                if validar_numero_positivo(bike_id_str):
                    bike_id = int(bike_id_str)
                    break
                print("[ERRO] ID da bike deve ser um número positivo.")
            
            # Verificar status da bike
            cursor.execute("SELECT status FROM Bike WHERE n_registro = :1", (bike_id,))
            row = cursor.fetchone()
            
            if not row:
                print("❌ [ERRO] Bike não encontrada.")
                return
            
            if row[0] == 'EM_USO':
                print("❌ [BLOQUEIO] Bike está alugada. Aguarde devolução.")
                return
            elif row[0] == 'MANUTENCAO':
                print("⚠️ [AVISO] Bike já está em manutenção.")
                return
            
            # Tipo de manutenção
            while True:
                tipo = input("Tipo (PREVENTIVA/CORRETIVA/ANTECIPADA): ").strip().upper()
                if validar_tipo_manutencao(tipo):
                    break
                print("[ERRO] Tipo inválido. Escolha entre: PREVENTIVA, CORRETIVA ou ANTECIPADA.")
            
            # Descrição do problema
            while True:
                problema = input("Descrição do problema (mínimo 10 caracteres): ").strip()
                if len(problema) >= 10:
                    break
                print("[ERRO] Descrição muito curta. Forneça mais detalhes.")
            
            # Inserir manutenção
            sql_insert = """
                INSERT INTO Manutencao (bike_n_registro, tipo, data_inicio, descricao_problema, valor)
                VALUES (:1, :2, SYSDATE, :3, 0)
            """
            cursor.execute(sql_insert, (bike_id, tipo, problema))
            
            # Atualizar status da bike
            sql_update = "UPDATE Bike SET status = 'MANUTENCAO', ponto_atual_id = NULL WHERE n_registro = :1"
            cursor.execute(sql_update, (bike_id,))
            
            conn.commit()
            print(f"✅ [SUCESSO] Bike {bike_id} enviada para manutenção.")
        
        elif op == '2':
            # Validar bike ID
            while True:
                bike_id_str = input("ID da Bike voltando da oficina: ").strip()
                if validar_numero_positivo(bike_id_str):
                    bike_id = int(bike_id_str)
                    break
                print("[ERRO] ID da bike deve ser um número positivo.")
            
            # Validar custo
            while True:
                custo_str = input("Custo final do reparo (R$): ").strip().replace(',', '.')
                if validar_numero_positivo(custo_str, decimal=True):
                    custo = float(custo_str)
                    break
                print("[ERRO] Custo deve ser um número positivo.")
            
            # Validar ponto
            while True:
                ponto_novo_str = input("ID do Ponto onde ela será colocada: ").strip()
                if validar_numero_positivo(ponto_novo_str):
                    ponto_novo = int(ponto_novo_str)
                    break
                print("[ERRO] ID do ponto deve ser um número positivo.")
            
            # Finalizar manutenção
            sql_manut = """
                UPDATE Manutencao SET data_fim = SYSDATE, valor = :1 
                WHERE bike_n_registro = :2 AND data_fim IS NULL
            """
            cursor.execute(sql_manut, (custo, bike_id))
            
            if cursor.rowcount == 0:
                print("❌ [ERRO] Nenhuma manutenção aberta encontrada para essa bike.")
                conn.rollback()
                return
            
            # Atualizar bike
            sql_bike = """
                UPDATE Bike SET status = 'DISPONIVEL', ponto_atual_id = :1 
                WHERE n_registro = :2
            """
            cursor.execute(sql_bike, (ponto_novo, bike_id))
            
            conn.commit()
            print(f"✅ [SUCESSO] Bike {bike_id} disponível novamente.")
            print(f"   Custo da manutenção: R$ {custo:.2f}")
    
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERRO] {e}")
    finally:
        cursor.close()

def realizar_devolucao(conn):
    print("\n🔄 DEVOLUÇÃO DE BIKE")
    
    cursor = conn.cursor()
    try:
        # Validar ID do aluguel
        while True:
            aluguel_id_str = input("ID do Aluguel: ").strip()
            if validar_numero_positivo(aluguel_id_str):
                aluguel_id = int(aluguel_id_str)
                break
            print("[ERRO] ID do aluguel deve ser um número positivo.")
        
        # Verificar aluguel
        sql_check = """
            SELECT A.bike_n_registro, A.data_hora_inicio, A.status, U.nome, B.modelo
            FROM Aluguel A
            JOIN Usuario U ON A.usuario_cpf = U.cpf
            JOIN Bike B ON A.bike_n_registro = B.n_registro
            WHERE A.id_aluguel = :1
        """
        cursor.execute(sql_check, (aluguel_id,))
        dados = cursor.fetchone()
        
        if not dados:
            print("❌ [ERRO] Aluguel não encontrado.")
            return
        
        bike_id, inicio, status, nome, modelo = dados
        
        if status != 'EM_ANDAMENTO':
            print(f"❌ [ERRO] Este aluguel não está ativo. Status: {status}")
            return
        
        # Validar ponto de devolução
        while True:
            ponto_dest_str = input("ID do Ponto de Devolução: ").strip()
            if validar_numero_positivo(ponto_dest_str):
                ponto_dest = int(ponto_dest_str)
                # Verificar se ponto existe
                cursor.execute("SELECT COUNT(*) FROM Ponto WHERE cod_ponto = :1", (ponto_dest,))
                if cursor.fetchone()[0] > 0:
                    break
                else:
                    print("[ERRO] Ponto não encontrado.")
            else:
                print("[ERRO] ID do ponto deve ser um número positivo.")
        
        # Calcular duração
        agora = datetime.datetime.now()
        duracao_minutos = (agora - inicio).total_seconds() / 60
        
        # Atualizar aluguel
        sql_aluguel = """
            UPDATE Aluguel SET 
                data_hora_fim = SYSDATE, 
                ponto_devolucao_id = :1, 
                status = 'CONCLUIDO',
                valor_aluguel = ROUND(:2 * 0.10, 2) -- Exemplo: R$ 0,10 por minuto
            WHERE id_aluguel = :3
        """
        cursor.execute(sql_aluguel, (ponto_dest, duracao_minutos, aluguel_id))
        
        # Atualizar bike
        sql_bike_stats = """
            UPDATE Bike SET 
                status = 'DISPONIVEL',
                ponto_atual_id = :1,
                qnt_alugueis = qnt_alugueis + 1,
                tempo_total_utilizado = tempo_total_utilizado + :2
            WHERE n_registro = :3
        """
        cursor.execute(sql_bike_stats, (ponto_dest, duracao_minutos, bike_id))
        
        conn.commit()
        
        print(f"\n✅ [SUCESSO] Devolução realizada com sucesso!")
        print(f"   Usuário: {nome}")
        print(f"   Bike: {modelo} (ID: {bike_id})")
        print(f"   Tempo de uso: {int(duracao_minutos)} minutos")
        print(f"   Ponto de devolução: {ponto_dest}")
        
        # Sugerir comentário
        print("\n💬 Lembre-se de avaliar sua experiência:")
        print("   - Use a opção 8 no menu para ver detalhes do aluguel")
        print("   - Você pode adicionar comentários sobre a bike e o ponto")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERRO NA TRANSAÇÃO] {e}")
    finally:
        cursor.close()

def consultar_situacao_usuario(conn):
    print("\n👤 CONSULTA DE SITUAÇÃO DO USUÁRIO")
    
    cursor = conn.cursor()
    try:
        while True:
            cpf_input = input("Digite o CPF para consultar (11 dígitos): ").strip()
            if validar_cpf(cpf_input):
                break
            print("[ERRO] CPF inválido! 11 dígitos necessários.")
        
        sql = """
            SELECT U.nome, U.cidade, U.is_cadUnico,
                   C.saldo, C.data_validade,
                   (SELECT COUNT(*) FROM Aluguel A WHERE A.usuario_cpf = U.cpf AND A.status = 'EM_ANDAMENTO') as alugueis_ativos,
                   (SELECT COUNT(*) FROM Multa M 
                    JOIN Aluguel A ON M.aluguel_id = A.id_aluguel 
                    WHERE A.usuario_cpf = U.cpf AND M.isPaid = 0) as multas_pendentes,
                   (SELECT COALESCE(SUM(M.valor), 0) FROM Multa M 
                    JOIN Aluguel A ON M.aluguel_id = A.id_aluguel 
                    WHERE A.usuario_cpf = U.cpf AND M.isPaid = 0) as valor_multas
            FROM Usuario U
            LEFT JOIN Cartao C ON U.cpf = C.usuario_cpf
            WHERE U.cpf = :1
        """
        cursor.execute(sql, (cpf_input,))
        dados = cursor.fetchone()
        
        if not dados:
            print(f"📭 Nenhum usuário encontrado com o CPF {formatar_cpf(cpf_input)}.")
            return
        
        nome, cidade, is_cad, saldo, validade, ativos, multas, valor_multas = dados
        
        # Formatação dos dados
        tipo_pagamento = "✅ Isento (CadÚnico)" if is_cad == 1 else "💰 Pagante"
        validade_str = validade.strftime('%d/%m/%Y') if validade else "❌ Não definida"
        saldo_str = f"R$ {saldo:.2f}" if saldo is not None else "❌ Sem Cartão"
        
        print("\n" + "="*60)
        print(f"📋 FICHA DO USUÁRIO: {nome}")
        print("="*60)
        print(f"📍 Local: {cidade}")
        print(f"🎫 Perfil: {tipo_pagamento}")
        print(f"💳 Cartão: {saldo_str} (Validade: {validade_str})")
        print(f"🚴 Aluguéis em Andamento: {ativos}")
        print(f"⚠️  Multas Pendentes: {multas}")
        
        if valor_multas > 0:
            print(f"💰 Valor Total em Multas: R$ {valor_multas:.2f}")
        
        print("\n" + "-"*60)
        
        if multas > 0:
            print("❌ [ALERTA] Este usuário possui pendências financeiras!")
            print("   Bloqueado para novos aluguéis até regularização.")
        elif ativos > 0:
            print("ℹ️  [INFO] Usuário está utilizando uma bicicleta no momento.")
        else:
            print("✅ [SITUAÇÃO REGULAR] Liberado para novos aluguéis.")
        
        # Histórico recente
        if multas > 0:
            sql_multas = """
                SELECT M.id_multa, M.valor, M.tipo, M.vencimento
                FROM Multa M
                JOIN Aluguel A ON M.aluguel_id = A.id_aluguel
                WHERE A.usuario_cpf = :1 AND M.isPaid = 0
                ORDER BY M.vencimento
            """
            cursor.execute(sql_multas, (cpf_input,))
            multas_detalhes = cursor.fetchall()
            
            if multas_detalhes:
                print("\n📝 Detalhes das Multas Pendentes:")
                for m_id, valor, tipo, venc in multas_detalhes:
                    print(f"   • ID {m_id}: {tipo} - R$ {valor:.2f} (Vence: {venc.strftime('%d/%m/%Y')})")
        
        print("="*60)
        
    except oracledb.DatabaseError as e:
        print(f"❌ [ERRO NA CONSULTA] {e}")
    finally:
        cursor.close()

# MENU PRINCIPAL 
def main():
    global DB_PASS
    if not DB_PASS:
        DB_PASS = getpass.getpass("Senha Oracle: ")
    
    print("\n" + "="*60)
    print("🚲 SISTEMA DE GESTÃO DE BIKES CIRCULARES")
    print("="*60)
    
    conn = conectar_banco()
    print("✅ Conectado ao banco de dados com sucesso!")
    
    while True:
        print("\n" + "="*60)
        print("📋 MENU PRINCIPAL")
        print("="*60)
        print("1. 📊 Relatórios Gerenciais")
        print("2. 👤 Cadastrar Usuário e Cartão")
        print("3. 📍 Cadastrar Ponto de Estacionamento")
        print("4. 🚲 Cadastrar Nova Bike")
        print("5. 🔧 Gerir Manutenção")
        print("6. 🚀 Realizar Aluguel")
        print("7. 🔄 Informar Devolução")
        print("8. 👁️  Consultar Situação do Usuário")
        print("0. 🚪 Sair")
        print("-"*60)
        
        while True:
            op = input("Escolha uma opção (0-8): ").strip()
            if op in ['0', '1', '2', '3', '4', '5', '6', '7', '8']:
                break
            print("[ERRO] Digite um número entre 0 e 8.")
        
        if op == '0':
            print("\n👋 Obrigado por usar o Sistema de Gestão de Bikes!")
            break
        elif op == '1': menu_relatorios(conn)
        elif op == '2': cadastrar_usuario(conn)
        elif op == '3': cadastrar_ponto(conn)
        elif op == '4': cadastrar_bike(conn)
        elif op == '5': gerir_manutencao(conn)
        elif op == '6': registrar_aluguel(conn)
        elif op == '7': realizar_devolucao(conn)
        elif op == '8': consultar_situacao_usuario(conn)
    
    conn.close()
    print("Conexão com o banco encerrada.")

if __name__ == "__main__":
    main()