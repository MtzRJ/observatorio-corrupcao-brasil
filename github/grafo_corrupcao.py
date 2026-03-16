"""
╔══════════════════════════════════════════════════════════════╗
║  MÓDULO DE ANÁLISE DE GRAFOS — grafo_corrupcao.py           ║
║                                                              ║
║  Conceitos de 2º ano de CC aplicados AGORA:                 ║
║  • Centralidade de grau (quem tem mais conexões)            ║
║  • Betweenness centrality (quem faz a ponte entre grupos)   ║
║  • PageRank (quem é mais influente na rede)                 ║
║  • Componentes conectados (grupos isolados)                  ║
║  • Caminho mais curto entre dois investigados               ║
║                                                              ║
║  Uso standalone:                                             ║
║    python grafo_corrupcao.py                                 ║
║  Ou importe:                                                 ║
║    from grafo_corrupcao import construir_grafo, pagerank     ║
╚══════════════════════════════════════════════════════════════╝
"""

import sqlite3
import json
import os
from collections import defaultdict

try:
    import networkx as nx
    NETWORKX_OK = True
except ImportError:
    NETWORKX_OK = False
    print("⚠️  networkx não instalado. Rode: pip install networkx")

DB_PATH = "corrupcao_brasil.db"


def _conectar(db_path=None):
    path = db_path or DB_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Banco não encontrado: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


# ══════════════════════════════════════════════════════════════
#  1. CONSTRUIR O GRAFO
# ══════════════════════════════════════════════════════════════

def construir_grafo(conn, dirigido=True):
    """
    Constrói um grafo NetworkX a partir do banco SQLite.

    Nós = pessoas (com atributos: tipo, partido, situacao_legal)
    Arestas = relacionamentos (com atributo: tipo da relação)

    Parâmetro:
        dirigido (bool): True = DiGraph (ex: A → ordenou → B)
                         False = Graph (sem direção, para análises de centralidade)
    """
    if not NETWORKX_OK:
        return None

    G = nx.DiGraph() if dirigido else nx.Graph()

    # Adicionar nós
    pessoas = conn.execute("SELECT id, nome, tipo, partido, situacao_legal FROM pessoas").fetchall()
    for p in pessoas:
        G.add_node(p["id"],
                   label=p["nome"],
                   tipo=p["tipo"] or "outro",
                   partido=p["partido"] or "",
                   situacao=p["situacao_legal"] or "")

    # Adicionar arestas
    rels = conn.execute("""
        SELECT r.pessoa_a, r.pessoa_b, r.tipo, r.descricao,
               c.nome AS caso_nome
        FROM relacionamentos r
        LEFT JOIN casos c ON c.id = r.caso_id
    """).fetchall()

    for r in rels:
        G.add_edge(r["pessoa_a"], r["pessoa_b"],
                   tipo=r["tipo"],
                   caso=r["caso_nome"] or "",
                   descricao=r["descricao"] or "")
        if not dirigido:
            G.add_edge(r["pessoa_b"], r["pessoa_a"],
                       tipo=r["tipo"] + "_inv",
                       caso=r["caso_nome"] or "")

    return G


# ══════════════════════════════════════════════════════════════
#  2. MÉTRICAS PRINCIPAIS
# ══════════════════════════════════════════════════════════════

def calcular_pagerank(G, top_n=10):
    """
    PageRank: quem é mais influente na rede.
    Mesma lógica do Google — um nó é importante se nós importantes apontam para ele.
    Aplicação: encontrar quem 'centraliza' o fluxo de propinas.

    Usa implementação pura Python (não precisa de scipy).
    """
    # nstart força o algoritmo a usar a implementação Python pura,
    # evitando a dependência opcional do scipy no NetworkX 3.x
    nstart = {n: 1.0 / G.number_of_nodes() for n in G.nodes()}
    pr = nx.pagerank(G, alpha=0.85, max_iter=200, nstart=nstart)
    ranking = sorted(pr.items(), key=lambda x: x[1], reverse=True)
    return [(G.nodes[n]["label"], score, G.nodes[n]["tipo"]) for n, score in ranking[:top_n]]


def calcular_betweenness(G_undir, top_n=10):
    """
    Betweenness Centrality: quem faz a ponte entre grupos.
    Um nó com alta betweenness é o 'elo' que conecta partes distintas da rede.
    Aplicação: identificar operadores que ligam políticos a empresas.
    """
    bc = nx.betweenness_centrality(G_undir, normalized=True)
    ranking = sorted(bc.items(), key=lambda x: x[1], reverse=True)
    return [(G_undir.nodes[n]["label"], score, G_undir.nodes[n]["tipo"]) for n, score in ranking[:top_n]]


def calcular_degree_centrality(G_undir, top_n=10):
    """
    Grau de centralidade: quem tem mais conexões diretas.
    O mais simples — mas revela os hubs da rede.
    """
    dc = nx.degree_centrality(G_undir)
    ranking = sorted(dc.items(), key=lambda x: x[1], reverse=True)
    return [(G_undir.nodes[n]["label"], score, G_undir.nodes[n]["tipo"]) for n, score in ranking[:top_n]]


def componentes_conectados(G_undir):
    """
    Componentes conectados: grupos de pessoas que se conectam entre si,
    mas sem conexão com outros grupos.
    Aplicação: identificar 'ilhas' de corrupção isoladas.
    """
    comps = list(nx.connected_components(G_undir))
    result = []
    for comp in sorted(comps, key=len, reverse=True):
        nomes = [G_undir.nodes[n]["label"] for n in comp]
        result.append(nomes)
    return result


def caminho_entre(G_undir, nome_a, nome_b):
    """
    Caminho mais curto entre dois investigados.
    '6 graus de separação' aplicado à corrupção.
    Ex: qual é o elo entre Lula e Bolsonaro na rede?
    """
    # Encontrar IDs pelos nomes
    id_a = id_b = None
    for n, data in G_undir.nodes(data=True):
        if nome_a.lower() in data["label"].lower():
            id_a = n
        if nome_b.lower() in data["label"].lower():
            id_b = n

    if id_a is None or id_b is None:
        return None, f"Pessoa não encontrada: {'A' if id_a is None else 'B'}"

    try:
        path_ids = nx.shortest_path(G_undir, id_a, id_b)
        path_names = [G_undir.nodes[n]["label"] for n in path_ids]
        return path_names, None
    except nx.NetworkXNoPath:
        return None, "Sem caminho — as duas pessoas estão em componentes desconectados"


def detectar_triangulos(G_undir, top_n=8):
    """
    Triângulos: grupos de 3 pessoas onde cada uma conhece as outras duas.
    Em redes de corrupção, triângulos são núcleos de confiança — grupos fechados
    que operam esquemas de forma mais coesa.
    """
    triangles = nx.triangles(G_undir)
    ranking = sorted(triangles.items(), key=lambda x: x[1], reverse=True)
    return [(G_undir.nodes[n]["label"], count, G_undir.nodes[n]["tipo"])
            for n, count in ranking[:top_n] if count > 0]


def estatisticas_gerais(G, G_undir):
    """
    Resumo estatístico da rede completa.
    """
    if G.number_of_nodes() == 0:
        return {}

    stats = {
        "nos": G.number_of_nodes(),
        "arestas": G.number_of_edges(),
        "densidade": round(nx.density(G_undir), 4),
        "componentes_conectados": nx.number_connected_components(G_undir),
        "diametro": None,
        "media_grau": round(sum(dict(G_undir.degree()).values()) / G_undir.number_of_nodes(), 2),
    }
    # Diâmetro só no maior componente
    largest = max(nx.connected_components(G_undir), key=len)
    sub = G_undir.subgraph(largest)
    try:
        stats["diametro"] = nx.diameter(sub)
    except Exception:
        stats["diametro"] = "N/A"

    return stats


# ══════════════════════════════════════════════════════════════
#  3. EXPORTAÇÃO PARA FERRAMENTAS EXTERNAS
# ══════════════════════════════════════════════════════════════

def exportar_para_gephi(G, caminho="rede_gephi.gexf"):
    """
    Exporta para GEXF — formato do Gephi.
    Gephi é a ferramenta visual de grafos mais usada em pesquisa acadêmica.
    """
    nx.write_gexf(G, caminho)
    print(f"  ✅ Exportado para Gephi: {caminho}")
    print("     Abra no Gephi → File → Open → Selecione o .gexf")
    print("     Use: Layout → ForceAtlas2 → Run por ~30 segundos")
    print("     Colorir por: Aparência → Nós → Partition → tipo")


def exportar_para_d3(G, caminho="rede_d3.json"):
    """
    Exporta para JSON no formato nodes/links do D3.js.
    Use para criar visualizações interativas na web.
    """
    nodes = [
        {
            "id": n,
            "label": data["label"],
            "tipo": data["tipo"],
            "partido": data["partido"],
            "group": _tipo_para_grupo(data["tipo"])
        }
        for n, data in G.nodes(data=True)
    ]
    links = [
        {
            "source": u,
            "target": v,
            "tipo": data.get("tipo", ""),
            "caso": data.get("caso", "")
        }
        for u, v, data in G.edges(data=True)
    ]
    grafo_json = {"nodes": nodes, "links": links}

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(grafo_json, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Exportado para D3.js: {caminho}")
    return grafo_json


def _tipo_para_grupo(tipo):
    grupos = {"politico": 1, "operador": 2, "empresario": 3,
              "doleiro": 4, "laranja": 5, "servidor": 6, "outro": 7}
    return grupos.get(tipo, 7)


# ══════════════════════════════════════════════════════════════
#  4. ANÁLISE COMPLETA (modo standalone)
# ══════════════════════════════════════════════════════════════

def analise_completa(db_path=None):
    """
    Roda todas as análises e imprime um relatório no terminal.
    """
    if not NETWORKX_OK:
        print("❌ Instale networkx: pip install networkx")
        return

    conn = _conectar(db_path)
    G_dir  = construir_grafo(conn, dirigido=True)
    G_undir = construir_grafo(conn, dirigido=False)

    sep = lambda t: print(f"\n{'─'*55}\n  {t}\n{'─'*55}")

    # ── Stats gerais ────────────────────────────────────────────
    sep("ESTATÍSTICAS GERAIS DA REDE")
    stats = estatisticas_gerais(G_dir, G_undir)
    print(f"  Nós (pessoas):          {stats['nos']}")
    print(f"  Arestas (relações):     {stats['arestas']}")
    print(f"  Densidade da rede:      {stats['densidade']}  (0=isolada, 1=todos conectados)")
    print(f"  Componentes isolados:   {stats['componentes_conectados']}")
    print(f"  Grau médio:             {stats['media_grau']} conexões por pessoa")
    print(f"  Diâmetro (maior comp.): {stats['diametro']} saltos")

    # ── PageRank ─────────────────────────────────────────────────
    sep("PAGERANK — As 10 pessoas mais influentes")
    print(f"  {'Nome':<35} {'Score':>8}  Tipo")
    print("  " + "-"*55)
    for nome, score, tipo in calcular_pagerank(G_dir):
        bar = "█" * int(score * 500)
        print(f"  {nome:<35} {score:>8.4f}  {tipo:<12}  {bar}")

    # ── Betweenness ──────────────────────────────────────────────
    sep("BETWEENNESS — Quem faz a ponte entre grupos (operadores-chave)")
    print(f"  {'Nome':<35} {'Score':>8}  Tipo")
    print("  " + "-"*55)
    for nome, score, tipo in calcular_betweenness(G_undir):
        bar = "█" * int(score * 100)
        print(f"  {nome:<35} {score:>8.4f}  {tipo:<12}  {bar}")

    # ── Grau ─────────────────────────────────────────────────────
    sep("GRAU — Quem tem mais conexões diretas")
    for nome, score, tipo in calcular_degree_centrality(G_undir, top_n=8):
        print(f"  {nome:<35}  {tipo}")

    # ── Triângulos ───────────────────────────────────────────────
    sep("TRIÂNGULOS — Núcleos de confiança na rede")
    triangs = detectar_triangulos(G_undir)
    if triangs:
        for nome, count, tipo in triangs:
            print(f"  {nome:<35}  {count} triângulo(s)  [{tipo}]")
    else:
        print("  Nenhum triângulo — rede ainda esparsa. Adicione mais relacionamentos.")

    # ── Componentes ──────────────────────────────────────────────
    sep("COMPONENTES CONECTADOS — Grupos isolados")
    comps = componentes_conectados(G_undir)
    for i, comp in enumerate(comps, 1):
        print(f"  Grupo {i} ({len(comp)} pessoa(s)): {', '.join(comp[:5])}" +
              (" ..." if len(comp) > 5 else ""))

    # ── Caminho entre pessoas ────────────────────────────────────
    sep("CAMINHO MAIS CURTO — Exemplos de '6 graus'")
    pares = [
        ("Lula", "Michel Temer"),
        ("Alberto Youssef", "José Dirceu"),
        ("Lula", "Carlinhos Cachoeira"),
    ]
    for a, b in pares:
        path, err = caminho_entre(G_undir, a, b)
        if path:
            print(f"\n  {a} → {b}:")
            print("  " + " → ".join(path) + f"  ({len(path)-1} salto(s))")
        else:
            print(f"\n  {a} → {b}: {err}")

    # ── Exportação ───────────────────────────────────────────────
    sep("EXPORTAÇÃO")
    exportar_para_gephi(G_dir)
    exportar_para_d3(G_dir)

    conn.close()
    print("\n✅ Análise completa finalizada!")


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    analise_completa(db)
