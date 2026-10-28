import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import os
import shutil
import database

# Configuração da Página
st.set_page_config(
    page_title="Gestor Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa banco de dados
database.init_db()

# --- AUTENTICAÇÃO E SEGURANÇA ---
# Obtém a senha configurada no secrets ou usa "1234" como padrão
SENHA_MESTRA = st.secrets.get("SENHA_ACESSO", "1234")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def autenticar():
    if st.session_state.get("campo_senha") == SENHA_MESTRA:
        st.session_state["autenticado"] = True
        st.session_state["erro_senha"] = False
    else:
        st.session_state["erro_senha"] = True

# Se ainda não estiver autenticado, exibe a tela de login protegida
if not st.session_state["autenticado"]:
    st.markdown("""
    <style>
        .login-box {
            max-width: 420px;
            margin: 60px auto 20px auto;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }
        .login-icon {
            font-size: 3rem;
            margin-bottom: 12px;
        }
        .login-title {
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .login-sub {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_v1, col_center, col_v2 = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("""
        <div class="login-box">
            <div class="login-icon">🔒</div>
            <div class="login-title">Gestor Financeiro</div>
            <div class="login-sub">Área restrita. Digite sua senha para acessar suas contas.</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_login"):
            senha_digitada = st.text_input("Senha", type="password", key="campo_senha", placeholder="Digite sua senha")
            btn_entrar = st.form_submit_button("Acessar Gestor", use_container_width=True)
            if btn_entrar:
                autenticar()
                if st.session_state["autenticado"]:
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
    st.stop()


# --- ESTILOS CSS PRINCIPAIS ---
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .kpi-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #cbd5e1;
    }
    .badge-pago {
        background-color: #065f46;
        color: #6ee7b7;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-pendente {
        background-color: #854d0e;
        color: #fde047;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-atrasado {
        background-color: #991b1b;
        color: #fca5a5;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_data(data_iso):
    if not data_iso:
        return "-"
    try:
        dt = datetime.strptime(str(data_iso), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return str(data_iso)

# --- SIDEBAR (Filtros & Navegação) ---
st.sidebar.markdown("## 💰 Gestor Financeiro")
st.sidebar.caption("Controle de contas a pagar e receber")

anos_disponiveis = database.obter_anos_disponiveis()
ano_atual = str(date.today().year)
mes_atual = date.today().month

col_ano, col_mes = st.sidebar.columns(2)
with col_ano:
    ano_selecionado = st.selectbox("Ano", ["Todos"] + anos_disponiveis, index=1 if ano_atual in anos_disponiveis else 0)

with col_mes:
    opcoes_mes = ["Todos"] + list(MESES.values())
    mes_selecionado_nome = st.selectbox("Mês", opcoes_mes, index=mes_atual)
    
mes_numero = None
if mes_selecionado_nome != "Todos":
    mes_numero = [k for k, v in MESES.items() if v == mes_selecionado_nome][0]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros")
filtro_tipo = st.sidebar.radio("Tipo de Lançamento", ["Todos", "Despesa", "Receita"], horizontal=True)
filtro_status = st.sidebar.selectbox("Status", ["Todos", "Pendente", "Pago", "Atrasado"])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Ações Rápidas")

if st.sidebar.button("📦 Dados de Exemplo", use_container_width=True):
    inseriu = database.popular_dados_exemplo()
    if inseriu:
        st.sidebar.success("Exemplos adicionados com sucesso!")
        st.rerun()
    else:
        st.sidebar.info("O banco de dados já contém registros.")

if st.sidebar.button("🚪 Bloquear / Sair", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

# Consulta das contas
contas_raw = database.listar_contas(
    mes=mes_numero,
    ano=ano_selecionado if ano_selecionado != "Todos" else None,
    tipo=filtro_tipo,
    status=filtro_status
)
df_contas = pd.DataFrame(contas_raw)

todas_periodo = database.listar_contas(
    mes=mes_numero,
    ano=ano_selecionado if ano_selecionado != "Todos" else None
)
df_periodo = pd.DataFrame(todas_periodo)

receitas_total = 0.0
receitas_recebidas = 0.0
despesas_total = 0.0
despesas_pagas = 0.0
atrasadas_qtd = 0
atrasadas_total = 0.0

if not df_periodo.empty:
    df_rec = df_periodo[df_periodo["tipo"] == "Receita"]
    df_desp = df_periodo[df_periodo["tipo"] == "Despesa"]
    
    receitas_total = df_rec["valor"].sum()
    receitas_recebidas = df_rec[df_rec["status"] == "Pago"]["valor"].sum()
    
    despesas_total = df_desp["valor"].sum()
    despesas_pagas = df_desp[df_desp["status"] == "Pago"]["valor"].sum()
    
    df_atrasadas = df_periodo[df_periodo["status"] == "Atrasado"]
    atrasadas_qtd = len(df_atrasadas)
    atrasadas_total = df_atrasadas["valor"].sum()

saldo_previsto = receitas_total - despesas_total
saldo_realizado = receitas_recebidas - despesas_pagas

# --- CABEÇALHO COM CARDS DE KPI ---
st.title("Painel de Controle Financeiro")
periodo_str = f"{mes_selecionado_nome} / {ano_selecionado}" if mes_selecionado_nome != "Todos" else f"Ano {ano_selecionado}"
st.caption(f"Exibindo movimentações de: **{periodo_str}**")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">🟢 Receitas Totais</div>
        <div class="kpi-value" style="color: #4ade80;">{formatar_moeda(receitas_total)}</div>
        <div class="kpi-sub">Recebido: {formatar_moeda(receitas_recebidas)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">🔴 Despesas Totais</div>
        <div class="kpi-value" style="color: #f87171;">{formatar_moeda(despesas_total)}</div>
        <div class="kpi-sub">Pago: {formatar_moeda(despesas_pagas)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    cor_saldo = "#38bdf8" if saldo_previsto >= 0 else "#f87171"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">💵 Saldo Previsto</div>
        <div class="kpi-value" style="color: {cor_saldo};">{formatar_moeda(saldo_previsto)}</div>
        <div class="kpi-sub">Realizado atual: {formatar_moeda(saldo_realizado)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    cor_atraso = "#fbbf24" if atrasadas_qtd == 0 else "#f87171"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">⚠️ Contas Atrasadas</div>
        <div class="kpi-value" style="color: {cor_atraso};">{atrasadas_qtd} <span style="font-size:1rem; font-weight:normal;">pendente(s)</span></div>
        <div class="kpi-sub">Total em atraso: {formatar_moeda(atrasadas_total)}</div>
    </div>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO POR ABAS ---
tab_dashboard, tab_contas, tab_novo, tab_relatorios, tab_backup = st.tabs([
    "📊 Visão Geral & Gráficos",
    "📋 Gerenciador de Contas",
    "➕ Novo Lançamento",
    "📈 Análise por Categorias",
    "💾 Backup & Nuvem"
])

# ==========================================
# ABA 1: VISÃO GERAL & GRÁFICOS
# ==========================================
with tab_dashboard:
    if df_periodo.empty:
        st.info("Nenhuma movimentação encontrada para o período selecionado. Adicione contas na aba '➕ Novo Lançamento' ou use o botão 'Dados de Exemplo' na barra lateral.")
    else:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Despesas por Categoria")
            df_desp_cat = df_periodo[df_periodo["tipo"] == "Despesa"]
            if not df_desp_cat.empty:
                cat_summary = df_desp_cat.groupby("categoria")["valor"].sum().reset_index()
                fig_donut = px.pie(
                    cat_summary,
                    names="categoria",
                    values="valor",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                fig_donut.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=True,
                    height=320
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.write("Sem despesas cadastradas neste período.")

        with col_g2:
            st.subheader("Comparativo: Previsto vs Realizado")
            dados_comparativo = pd.DataFrame({
                "Categoria": ["Receitas", "Receitas", "Despesas", "Despesas"],
                "Status": ["Total Previsto", "Já Recebido", "Total Previsto", "Já Pago"],
                "Valor": [receitas_total, receitas_recebidas, despesas_total, despesas_pagas]
            })
            fig_bar = px.bar(
                dados_comparativo,
                x="Categoria",
                y="Valor",
                color="Status",
                barmode="group",
                color_discrete_map={
                    "Total Previsto": "#64748b",
                    "Já Recebido": "#22c55e",
                    "Já Pago": "#ef4444"
                }
            )
            fig_bar.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
                yaxis_title="Valor (R$)",
                xaxis_title=""
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("⏰ Próximos Vencimentos")
        df_proximas = df_periodo[df_periodo["status"] != "Pago"].sort_values(by="data_vencimento").head(5)
        
        if df_proximas.empty:
            st.success("🎉 Todas as contas deste período estão quitadas!")
        else:
            cols_cards = st.columns(len(df_proximas))
            for idx, (_, row) in enumerate(df_proximas.iterrows()):
                cor_borda = "#ef4444" if row["status"] == "Atrasado" else "#f59e0b"
                with cols_cards[idx]:
                    st.markdown(f"""
                    <div style="border-left: 4px solid {cor_borda}; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <div style="font-weight: bold; font-size: 0.95rem;">{row['descricao']}</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">Venc: {formatar_data(row['data_vencimento'])}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: white; margin-top: 4px;">{formatar_moeda(row['valor'])}</div>
                        <div style="margin-top: 6px;"><span class="badge-{row['status'].lower()}">{row['status']}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# ABA 2: GERENCIADOR DE CONTAS (LISTA E AÇÕES)
# ==========================================
with tab_contas:
    def obter_conta_direto(cid):
        if hasattr(database, "obter_conta"):
            try:
                res = database.obter_conta(cid)
                if res:
                    return res
            except:
                pass
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contas WHERE id = ?", (cid,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def salvar_edicao_direto(cid, desc, tipo, cat, val, venc, stt, obs):
        if hasattr(database, "editar_conta"):
            try:
                database.editar_conta(cid, desc, tipo, cat, val, venc, stt, obs)
                return
            except:
                pass
        conn = database.get_connection()
        cursor = conn.cursor()
        dt_pag = date.today().isoformat() if stt == "Pago" else None
        cursor.execute("""
            UPDATE contas
            SET descricao = ?, tipo = ?, categoria = ?, valor = ?, data_vencimento = ?, data_pagamento = ?, status = ?, observacoes = ?
            WHERE id = ?
        """, (desc, tipo, cat, float(val), str(venc), dt_pag, stt, obs, cid))
        conn.commit()
        conn.close()

    @st.dialog("✏️ Editar Lançamento")
    def modal_editar_conta(conta_id):
        conta = obter_conta_direto(conta_id)
        if not conta:
            st.error("Conta não encontrada.")
            return
            
        with st.form(f"form_edicao_{conta_id}"):
            st.write(f"Editando lançamento **#{conta_id}**")
            desc = st.text_input("Descrição*", value=conta["descricao"])
            
            c1, c2 = st.columns(2)
            with c1:
                tipo_idx = 0 if conta["tipo"] == "Despesa" else 1
                tipo = st.selectbox("Tipo*", ["Despesa", "Receita"], index=tipo_idx)
                valor = st.number_input("Valor (R$)*", min_value=0.01, step=10.0, value=float(conta["valor"]), format="%.2f")
                
            with c2:
                try:
                    dt_atual = datetime.strptime(str(conta["data_vencimento"]), "%Y-%m-%d").date()
                except:
                    dt_atual = date.today()
                venc = st.date_input("Data de Vencimento*", value=dt_atual)
                
                status_opts = ["Pendente", "Pago", "Atrasado"]
                st_idx = status_opts.index(conta["status"]) if conta["status"] in status_opts else 0
                status = st.selectbox("Status", status_opts, index=st_idx)
                
            categorias_sugeridas = [
                "Moradia", "Alimentação", "Transporte", "Contas Básicas",
                "Saúde", "Educação", "Lazer", "Cartão", "Salário", "Serviços", "Investimentos", "Outros"
            ]
            if conta["categoria"] not in categorias_sugeridas:
                categorias_sugeridas.append(conta["categoria"])
            cat_idx = categorias_sugeridas.index(conta["categoria"]) if conta["categoria"] in categorias_sugeridas else 0
            categoria = st.selectbox("Categoria", categorias_sugeridas, index=cat_idx)
            
            obs = st.text_area("Observações", value=conta["observacoes"] or "")
            
            btn_salvar = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
            if btn_salvar:
                if not desc.strip():
                    st.error("A descrição não pode ficar vazia.")
                elif valor <= 0:
                    st.error("O valor deve ser maior que zero.")
                else:
                    salvar_edicao_direto(conta_id, desc.strip(), tipo, categoria, valor, venc.isoformat(), status, obs.strip())
                    st.success("Conta atualizada com sucesso!")
                    st.rerun()

    col_busca, col_exp = st.columns([3, 1])
    with col_busca:
        busca_texto = st.text_input("🔍 Buscar por nome, categoria ou observação:", placeholder="Ex: aluguel, mercado, luz...")
    with col_exp:
        if not df_contas.empty:
            csv = df_contas.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Exportar CSV",
                data=csv,
                file_name=f"contas_{periodo_str.replace(' ', '_').replace('/', '-')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    contas_filtradas = database.listar_contas(
        mes=mes_numero,
        ano=ano_selecionado if ano_selecionado != "Todos" else None,
        tipo=filtro_tipo,
        status=filtro_status,
        busca=busca_texto if busca_texto else None
    )

    if not contas_filtradas:
        st.info("Nenhuma conta encontrada com os filtros atuais.")
    else:
        st.write(f"Mostrando **{len(contas_filtradas)}** lançamentos:")
        
        st.markdown("""
        <div style="display: grid; grid-template-columns: 1fr 2.3fr 1fr 1.2fr 1fr 1fr 1.8fr; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.06); border-radius: 6px; font-weight: bold; font-size: 0.85rem; color: #94a3b8;">
            <div>VENCIMENTO</div>
            <div>DESCRIÇÃO</div>
            <div>TIPO</div>
            <div>CATEGORIA</div>
            <div>VALOR</div>
            <div>STATUS</div>
            <div style="text-align: right;">AÇÕES</div>
        </div>
        """, unsafe_allow_html=True)

        for conta in contas_filtradas:
            cid = conta["id"]
            cor_tipo = "#4ade80" if conta["tipo"] == "Receita" else "#f87171"
            
            c_venc, c_desc, c_tipo, c_cat, c_val, c_st, c_act = st.columns([1, 2.3, 1, 1.2, 1, 1, 1.8])
            
            with c_venc:
                st.write(formatar_data(conta["data_vencimento"]))
            with c_desc:
                obs_txt = f"<br><small style='color:#64748b;'>{conta['observacoes']}</small>" if conta["observacoes"] else ""
                st.markdown(f"**{conta['descricao']}**{obs_txt}", unsafe_allow_html=True)
            with c_tipo:
                st.markdown(f"<span style='color: {cor_tipo}; font-weight: 600;'>{conta['tipo']}</span>", unsafe_allow_html=True)
            with c_cat:
                st.write(conta["categoria"])
            with c_val:
                st.markdown(f"**{formatar_moeda(conta['valor'])}**")
            with c_st:
                badge_class = f"badge-{conta['status'].lower()}"
                st.markdown(f"<span class='{badge_class}'>{conta['status']}</span>", unsafe_allow_html=True)
            with c_act:
                col_btn_pago, col_btn_edit, col_btn_del = st.columns(3)
                with col_btn_pago:
                    if conta["status"] == "Pago":
                        if st.button("↩️", key=f"desfazer_{cid}", help="Marcar como Pendente"):
                            database.marcar_como_pago(cid, pago=False)
                            st.rerun()
                    else:
                        if st.button("✅", key=f"pagar_{cid}", help="Marcar como Pago"):
                            database.marcar_como_pago(cid, pago=True)
                            st.rerun()
                with col_btn_edit:
                    if st.button("✏️", key=f"edit_{cid}", help="Editar Lançamento"):
                        modal_editar_conta(cid)
                with col_btn_del:
                    if st.button("🗑️", key=f"del_{cid}", help="Excluir Lançamento"):
                        database.excluir_conta(cid)
                        st.rerun()
            st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

# ==========================================
# ABA 3: NOVO LANÇAMENTO
# ==========================================
with tab_novo:
    st.subheader("➕ Cadastrar Nova Conta ou Receita")
    
    with st.form("form_novo_lancamento", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nova_desc = st.text_input("Descrição*", placeholder="Ex: Conta de Luz, Salário, Internet...")
            novo_tipo = st.selectbox("Tipo*", ["Despesa", "Receita"])
            novo_valor = st.number_input("Valor (R$)*", min_value=0.01, step=10.0, format="%.2f")
            
        with col_f2:
            novo_venc = st.date_input("Data de Vencimento*", value=date.today())
            
            categorias_sugeridas = [
                "Moradia", "Alimentação", "Transporte", "Contas Básicas",
                "Saúde", "Educação", "Lazer", "Cartão", "Salário", "Serviços", "Investimentos", "Outros"
            ]
            nova_cat = st.selectbox("Categoria*", categorias_sugeridas)
            cat_personalizada = st.text_input("Ou digite uma nova categoria (opcional):", placeholder="Ex: Manutenção Carro")
            
        st.markdown("---")
        col_f3, col_f4 = st.columns(2)
        with col_f3:
            novo_status = st.selectbox("Status Inicial", ["Pendente", "Pago"])
            meses_recorrencia = st.number_input("Repetir por quantos meses? (1 = apenas uma vez)", min_value=1, max_value=48, value=1)
            
        with col_f4:
            novas_obs = st.text_area("Observações (opcional)", placeholder="Detalhes, chave Pix, número do código de barras...")

        submit = st.form_submit_button("💾 Salvar Lançamento", use_container_width=True)
        
        if submit:
            if not nova_desc.strip():
                st.error("Por favor, preencha a descrição da conta.")
            elif novo_valor <= 0:
                st.error("O valor deve ser maior que zero.")
            else:
                cat_final = cat_personalizada.strip() if cat_personalizada.strip() else nova_cat
                database.adicionar_conta(
                    descricao=nova_desc.strip(),
                    tipo=novo_tipo,
                    categoria=cat_final,
                    valor=novo_valor,
                    data_vencimento=novo_venc.isoformat(),
                    status=novo_status,
                    recorrente=1 if meses_recorrencia > 1 else 0,
                    observacoes=novas_obs.strip(),
                    meses_recorrencia=meses_recorrencia
                )
                st.success(f"✅ Conta '{nova_desc}' cadastrada com sucesso ({meses_recorrencia} lançamento(s))!")
                st.rerun()

# ==========================================
# ABA 4: ANÁLISE POR CATEGORIAS & RELATÓRIOS
# ==========================================
with tab_relatorios:
    st.subheader("📈 Análise Detalhada de Despesas e Receitas")
    
    if df_periodo.empty:
        st.info("Nenhum dado disponível no período.")
    else:
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("#### Top Categorias de Despesas")
            df_desp = df_periodo[df_periodo["tipo"] == "Despesa"]
            if not df_desp.empty:
                cat_df = df_desp.groupby("categoria")["valor"].agg(["sum", "count"]).reset_index()
                cat_df.columns = ["Categoria", "Total (R$)", "Qtd Contas"]
                cat_df = cat_df.sort_values(by="Total (R$)", ascending=False)
                cat_df["% do Total"] = (cat_df["Total (R$)"] / cat_df["Total (R$)"].sum()) * 100
                
                cat_df_formatado = cat_df.copy()
                cat_df_formatado["Total (R$)"] = cat_df_formatado["Total (R$)"].apply(formatar_moeda)
                cat_df_formatado["% do Total"] = cat_df_formatado["% do Total"].map("{:.1f}%".format)
                
                st.dataframe(cat_df_formatado, use_container_width=True, hide_index=True)
            else:
                st.write("Sem despesas no período.")

        with col_r2:
            st.markdown("#### Histórico de Lançamentos por Status")
            status_df = df_periodo.groupby(["tipo", "status"])["valor"].sum().reset_index()
            fig_hist = px.bar(
                status_df,
                x="status",
                y="valor",
                color="tipo",
                barmode="group",
                color_discrete_map={"Receita": "#22c55e", "Despesa": "#ef4444"}
            )
            fig_hist.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=300,
                xaxis_title="Status",
                yaxis_title="Total (R$)"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

# ==========================================
# ABA 5: BACKUP & NUVEM
# ==========================================
with tab_backup:
    st.subheader("💾 Backup e Segurança dos Dados")
    st.caption("Faça download periódico do seu banco de dados ou restaure seus dados em qualquer dispositivo.")
    
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.markdown("#### 📥 Baixar Cópia de Segurança")
        st.write("Baixe o arquivo completo do banco SQLite (`dados.db`) para guardar no seu computador ou celular:")
        
        if os.path.exists(database.DB_PATH):
            with open(database.DB_PATH, "rb") as f:
                dados_bytes = f.read()
            st.download_button(
                label="⬇️ Baixar Backup Completo (dados.db)",
                data=dados_bytes,
                file_name=f"backup_contas_{date.today().isoformat()}.db",
                mime="application/octet-stream",
                use_container_width=True
            )
        else:
            st.warning("Banco de dados ainda não foi criado.")

    with col_b2:
        st.markdown("#### 📤 Restaurar Backup")
        st.write("Selecione um arquivo `.db` anterior para substituir os dados atuais:")
        arquivo_upload = st.file_uploader("Enviar arquivo de backup (.db)", type=["db", "sqlite"])
        if arquivo_upload is not None:
            if st.button("⚠️ Confirmar e Restaurar Banco", use_container_width=True):
                with open(database.DB_PATH, "wb") as f_out:
                    f_out.write(arquivo_upload.getbuffer())
                st.success("✅ Banco de dados restaurado com sucesso!")
                st.rerun()
