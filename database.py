import sqlite3
from datetime import date, datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dados.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'Despesa' ou 'Receita'
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento DATE NOT NULL,
            data_pagamento DATE,
            status TEXT NOT NULL, -- 'Pendente', 'Pago', 'Atrasado'
            recorrente INTEGER DEFAULT 0, -- 0: Não, 1: Sim
            observacoes TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    atualizar_status_atrasados()

def atualizar_status_atrasados():
    """Atualiza automaticamente contas pendentes com vencimento no passado para 'Atrasado'."""
    conn = get_connection()
    cursor = conn.cursor()
    hoje = date.today().isoformat()
    cursor.execute("""
        UPDATE contas
        SET status = 'Atrasado'
        WHERE status = 'Pendente' AND data_vencimento < ?
    """, (hoje,))
    conn.commit()
    conn.close()

def adicionar_conta(descricao, tipo, categoria, valor, data_vencimento, status="Pendente", recorrente=0, observacoes="", meses_recorrencia=1):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Se a conta já tiver sido marcada como paga
    data_pagamento = date.today().isoformat() if status == "Pago" else None
    
    # Se a data de vencimento já passou e está pendente
    if status == "Pendente" and str(data_vencimento) < date.today().isoformat():
        status = "Atrasado"

    data_base = datetime.strptime(str(data_vencimento), "%Y-%m-%d").date()
    
    for i in range(meses_recorrencia):
        if i == 0:
            venc = data_base
        else:
            ano = data_base.year + ((data_base.month + i - 1) // 12)
            mes = ((data_base.month + i - 1) % 12) + 1
            dia = min(data_base.day, 28)
            venc = date(ano, mes, dia)
            status = "Pendente"
            data_pagamento = None

        cursor.execute("""
            INSERT INTO contas (descricao, tipo, categoria, valor, data_vencimento, data_pagamento, status, recorrente, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            descricao if meses_recorrencia == 1 else f"{descricao} ({i+1}/{meses_recorrencia})",
            tipo,
            categoria,
            float(valor),
            venc.isoformat(),
            data_pagamento,
            status,
            1 if recorrente or meses_recorrencia > 1 else 0,
            observacoes
        ))
        
    conn.commit()
    conn.close()

def listar_contas(mes=None, ano=None, tipo=None, status=None, busca=None):
    atualizar_status_atrasados()
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM contas WHERE 1=1"
    params = []
    
    if ano and ano != "Todos":
        query += " AND strftime('%Y', data_vencimento) = ?"
        params.append(str(ano))
        
    if mes and mes != "Todos":
        mes_str = f"{int(mes):02d}"
        query += " AND strftime('%m', data_vencimento) = ?"
        params.append(mes_str)
        
    if tipo and tipo != "Todos":
        query += " AND tipo = ?"
        params.append(tipo)
        
    if status and status != "Todos":
        query += " AND status = ?"
        params.append(status)
        
    if busca:
        query += " AND (descricao LIKE ? OR categoria LIKE ? OR observacoes LIKE ?)"
        term = f"%{busca}%"
        params.extend([term, term, term])
        
    query += " ORDER BY data_vencimento ASC, id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def marcar_como_pago(conta_id, pago=True):
    conn = get_connection()
    cursor = conn.cursor()
    if pago:
        hoje = date.today().isoformat()
        cursor.execute("UPDATE contas SET status = 'Pago', data_pagamento = ? WHERE id = ?", (hoje, conta_id))
    else:
        cursor.execute("SELECT data_vencimento FROM contas WHERE id = ?", (conta_id,))
        row = cursor.fetchone()
        if row:
            venc = row["data_vencimento"]
            novo_status = "Atrasado" if venc < date.today().isoformat() else "Pendente"
            cursor.execute("UPDATE contas SET status = ?, data_pagamento = NULL WHERE id = ?", (novo_status, conta_id))
    conn.commit()
    conn.close()

def excluir_conta(conta_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contas WHERE id = ?", (conta_id,))
    conn.commit()
    conn.close()

def obter_anos_disponiveis():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT strftime('%Y', data_vencimento) as ano FROM contas ORDER BY ano DESC")
    anos = [row["ano"] for row in cursor.fetchall() if row["ano"]]
    conn.close()
    ano_atual = str(date.today().year)
    if ano_atual not in anos:
        anos.insert(0, ano_atual)
    return anos

def popular_dados_exemplo():
    """Insere dados de exemplo para demonstração rápida."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM contas")
    if cursor.fetchone()["total"] > 0:
        conn.close()
        return False
    
    hoje = date.today()
    mes = hoje.month
    ano = hoje.year

    exemplos = [
        ("Salário Mensal", "Receita", "Salário", 5500.00, date(ano, mes, 5), "Pago"),
        ("Freelance / Bônus", "Receita", "Serviços", 1200.00, date(ano, mes, 20), "Pendente"),
        ("Aluguel do Apartamento", "Despesa", "Moradia", 1600.00, date(ano, mes, 10), "Pago"),
        ("Condomínio", "Despesa", "Moradia", 450.00, date(ano, mes, 10), "Pago"),
        ("Conta de Energia Elétrica", "Despesa", "Contas Básicas", 185.40, date(ano, mes, 15), "Pago"),
        ("Internet Fibra", "Despesa", "Contas Básicas", 129.90, date(ano, mes, 18), "Pendente"),
        ("Supermercado Mensal", "Despesa", "Alimentação", 850.00, date(ano, mes, 12), "Pago"),
        ("Fatura Cartão de Crédito", "Despesa", "Cartão", 1420.50, date(ano, mes, 25), "Pendente"),
        ("Plano de Saúde", "Despesa", "Saúde", 380.00, date(ano, mes, 22), "Pendente"),
        ("Academia", "Despesa", "Saúde", 110.00, date(ano, mes, 8), "Pago"),
        ("Netflix & Spotify", "Despesa", "Lazer", 75.80, date(ano, mes, 2), "Pago"),
        ("Combustível / Transporte", "Despesa", "Transporte", 320.00, date(ano, mes, 28), "Pendente"),
    ]

    for desc, tipo, cat, val, dt, st in exemplos:
        adicionar_conta(desc, tipo, cat, val, dt.isoformat(), status=st, recorrente=1)

    return True
