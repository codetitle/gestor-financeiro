# 💰 Gestor Financeiro em Python (Web)

Aplicação web moderna, interativa e leve para controle completo de **contas a pagar, receber, vencimentos e relatórios financeiros**, desenvolvida em **Python** com **Streamlit**, **SQLite**, **Pandas** e **Plotly**.

---

## 🚀 Como Executar

### Opção 1: Pelo arquivo executável (Mais Fácil)
* **Para abrir**: Dê um duplo clique em [`iniciar.bat`](file:///C:/Users/PC-Gamer/gestor_contas/iniciar.bat). O navegador abrirá automaticamente em `http://localhost:8501`.
* **Para encerrar**: Dê um duplo clique em [`encerrar.bat`](file:///C:/Users/PC-Gamer/gestor_contas/encerrar.bat) ou feche a janela preta do Prompt de Comando.

### Opção 2: Pelo Terminal / PowerShell
Navegue até a pasta do projeto e execute:
```bash
cd C:\Users\PC-Gamer\gestor_contas
python -m streamlit run app.py
```
Para parar no terminal, basta pressionar **Ctrl + C**.

---

## ✨ Funcionalidades

1. **Dashboard & KPIs em Tempo Real:**
   * 🟢 Total de Receitas (previsto vs. já recebido).
   * 🔴 Total de Despesas (previsto vs. já pago).
   * 💵 Saldo Líquido Previsto vs. Realizado.
   * ⚠️ Contador e montante de contas em atraso.

2. **Gráficos Interativos (Plotly):**
   * Gráfico de Rosca (Donut) com distribuição de despesas por categoria.
   * Gráfico de Barras com comparativo Previsto vs. Realizado.
   * Cards de alerta para os próximos vencimentos mais urgentes.

3. **Gerenciador de Contas:**
   * Lista completa ordenada por data de vencimento.
   * Filtros por ano, mês, tipo (Despesa/Receita) e status (Pendente/Pago/Atrasado).
   * Campo de busca textual rápida (por descrição, categoria ou observação).
   * Botão de ação rápida para marcar como pago (✅) ou desfazer (↩️).
   * Exclusão rápida de lançamentos (🗑️).
   * Exportação instantânea para planilha CSV.

4. **Novo Lançamento:**
   * Cadastro intuitivo com categorias pré-definidas ou personalizadas.
   * Suporte a contas recorrentes / parceladas (repetir por X meses automaticamente).

5. **Banco de Dados SQLite:**
   * Armazenamento local no arquivo `dados.db`.
   * Atualização automática de contas vencidas para o status "Atrasado".
