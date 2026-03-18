# 🔍 Observatório da Corrupção Brasileira

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://SEU-APP.streamlit.app)
[![Licença](https://img.shields.io/badge/licença-MIT-green)](LICENSE)
[![Dados](https://img.shields.io/badge/dados-públicos-blue)](https://portaldatransparencia.gov.br)

**Banco de dados educacional e open source sobre corrupção no Brasil (1988–2024)**

> Dados de fontes públicas: MPF · STF · TCU · CGU · PF · Portal da Transparência

---

## 🎯 Para que serve

Este projeto reúne, estrutura e conecta informações públicas sobre casos de corrupção no Brasil desde 1988. **Nenhum banco unificado assim existe publicamente** — os dados existem espalhados em centenas de documentos do MPF, STF, TCU, PF e jornais investigativos. Este projeto conecta essas peças.

### Quem pode usar
- 🎓 **Estudantes e pesquisadores** — TCCs, dissertações, análise de redes políticas
- 📰 **Jornalistas investigativos** — cruzamento de nomes, conexões entre investigados
- 🏛️ **Cidadãos e ativistas** — educação cívica, monitoramento de casos
- 💻 **Desenvolvedores** — base para aplicações de transparência

---

## 📁 Estrutura do projeto

```
.
├── painel_corrupcao.py      # App Streamlit (painel web interativo)
├── atualizador.py           # Script de atualização automática
├── analisar_corrupcao.py    # Script Python para análise local
├── corrupcao_brasil.db      # Banco de dados SQLite
├── requirements.txt         # Dependências Python
└── README.md
```

---

## 🚀 Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/corrupcao-brasil
cd corrupcao-brasil

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o painel
streamlit run painel_corrupcao.py
```

O painel abre automaticamente em `http://localhost:8501`

---

## 🌐 Como publicar online (gratuito)

1. Suba o projeto para um repositório **público** no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte sua conta GitHub
4. Selecione este repositório e o arquivo `painel_corrupcao.py`
5. Clique **Deploy** — em ~2 minutos seu app tem uma URL pública

---

## 🔄 Atualização automática

### Windows (Agendador de Tarefas)
```
Programa: python
Argumentos: C:\caminho\atualizador.py
Disparar: Diariamente às 06:00
```

### Linux/Mac (cron)
```bash
0 6 * * * cd /caminho/projeto && python atualizador.py
```

### Com API do Portal da Transparência
Cadastre gratuitamente em [portaldatransparencia.gov.br/api](https://portaldatransparencia.gov.br/api) e adicione sua chave no `atualizador.py`:
```python
API_KEY_TRANSPARENCIA = "sua-chave-aqui"
```

---

## 🗄️ Estrutura do banco de dados

```sql
casos          -- Escândalos de corrupção (15 registros iniciais)
pessoas        -- Investigados: políticos, empresários, laranjas, doleiros
empresas       -- Empreiteiras, fachadas, offshores, bancos
partidos       -- Partidos políticos com espectro ideológico
operacoes      -- Operações da PF e MPF
caso_pessoa    -- Liga casos ↔ pessoas (com papel: mandante, delator...)
caso_empresa   -- Liga casos ↔ empresas
pessoa_empresa -- Liga pessoas ↔ empresas (sócio, laranja, controlador...)
pessoa_partido -- Liga pessoas ↔ partidos (com datas de entrada/saída)
relacionamentos-- Liga pessoas ↔ pessoas (ordenou, delatou, laranja_de...)
```

---

## 📊 Fontes

- **MPF** (mpf.mp.br) — Denúncias, acordos de delação, estatísticas
- **STF/STJ/TRFs** — Acórdãos e decisões judiciais
- **TCU** (tcu.gov.br) — Auditorias e relatórios de fiscalização
- **CGU / Portal da Transparência** — Contratos, CEIS, CNEP
- **PF** — Operações e inquéritos
- **Agência Pública, The Intercept Brasil, Piauí, Folha, Globo, Estadão** — Jornalismo investigativo

---

## ⚖️ Uso ético

✅ Pesquisa acadêmica e educacional  
✅ Jornalismo investigativo  
✅ Monitoramento cívico  
❌ Não é prova jurídica  
❌ Não define culpa definitiva  
❌ Não tem fins políticos partidários  

**Todos os partidos estão representados igualmente.**

---

## 🤝 Como contribuir

1. Fork este repositório
2. Adicione novos casos, pessoas ou empresas com fontes documentadas
3. Abra um Pull Request com a descrição e a fonte da informação

---

## 📄 Licença

MIT — use livremente para fins educacionais e de pesquisa, mantendo a atribuição.
