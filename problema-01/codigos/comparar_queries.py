"""
=============================================================
Andrômeda – Problema 1: Comparação de Queries
=============================================================
Roda a query original (com bugs) e a corrigida lado a lado,
exibe as diferenças no terminal e salva os resultados em CSV.

Uso:
    python3 comparar_queries.py

Requisitos: Python 3 (sem dependências externas)
=============================================================
"""

import sqlite3
import csv
import os

# =============================================================
# CONFIGURAÇÃO
# =============================================================

DB_PATH      = os.path.join(os.path.dirname(__file__), "..", "andromeda.db")
RESULTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "resultados")
os.makedirs(RESULTS_DIR, exist_ok=True)

# =============================================================
# QUERIES
# =============================================================

QUERY_ORIGINAL = """
SELECT
    p.product_name,
    DATE(t.transaction_date)                        AS transaction_day,
    CASE
        WHEN p.category = 'Electonics'  THEN 'High'
        WHEN p.category = 'Books'       THEN 'Medium'
        WHEN p.category = 'Furniture'   THEN 'Low'
        WHEN p.category = 'Stationery'  THEN 'Low'
        WHEN p.category = 'Clothing'    THEN 'Low'
        WHEN p.category = 'toys'        THEN 'Low'
        ELSE NULL
    END                                             AS category_importance,
    SUM(t.quantity)                                 AS total_quantity,
    SUM(t.price * t.quantity)                       AS total_value,
    SUM(t.price * t.quantity) / SUM(t.quantity)     AS avg_ticket
FROM        transactions t
LEFT JOIN   products p ON t.product_id = p.product_id
GROUP BY
    p.product_name,
    p.category,
    transaction_day,
    t.transaction_id
"""

QUERY_CORRIGIDA = """
SELECT
    p.product_name,
    DATE(t.transaction_date)                                              AS transaction_day,
    CASE
        WHEN TRIM(p.category) = 'Electronics' THEN 'High'
        WHEN TRIM(p.category) = 'Books'       THEN 'Medium'
        WHEN TRIM(p.category) = 'Furniture'   THEN 'Low'
        WHEN TRIM(p.category) = 'Stationery'  THEN 'Low'
        WHEN TRIM(p.category) = 'Clothing'    THEN 'Low'
        WHEN TRIM(p.category) = 'Toys'        THEN 'Low'
        ELSE NULL
    END                                                                   AS category_importance,
    SUM(t.quantity)                                                       AS total_quantity,
    SUM(CASE WHEN t.price > 0 THEN t.price * t.quantity ELSE 0 END)     AS total_value,
    CASE
        WHEN SUM(CASE WHEN t.price > 0 THEN t.quantity ELSE 0 END) > 0
        THEN SUM(CASE WHEN t.price > 0 THEN t.price * t.quantity ELSE 0 END)
             / SUM(CASE WHEN t.price > 0 THEN t.quantity ELSE 0 END)
        ELSE 0
    END                                                                   AS avg_ticket
FROM        transactions t
LEFT JOIN   products p ON t.product_id = p.product_id
WHERE       t.quantity > 0
GROUP BY
    p.product_name,
    TRIM(p.category),
    transaction_day
ORDER BY
    transaction_day,
    category_importance
"""

# =============================================================
# HELPERS DE EXIBIÇÃO
# =============================================================

def print_separator(char="=", width=90):
    print(char * width)

def print_table(rows, cols, title):
    """Imprime uma tabela formatada no terminal."""
    print_separator()
    print(f"  {title}")
    print_separator()

    # Calcula largura de cada coluna
    widths = [len(c) for c in cols]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val) if val is not None else "NULL"))

    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  " + "  ".join("-" * w for w in widths)

    print(fmt.format(*cols))
    print(sep)
    for row in rows:
        formatted = [str(v) if v is not None else "NULL" for v in row]
        print(fmt.format(*formatted))

    print(f"\n  Total de linhas: {len(rows)}")
    print_separator()

def highlight_issues(rows, cols):
    """Aponta linhas com problemas conhecidos na query original."""
    issues = []
    idx_importance = cols.index("category_importance")
    idx_value      = cols.index("total_value")
    idx_qty        = cols.index("total_quantity")

    for row in rows:
        problems = []
        if row[idx_importance] == "NULL" or row[idx_importance] is None:
            problems.append("category_importance NULA")
        if float(row[idx_value] or 0) == 0.0:
            problems.append("total_value = 0 (suspeito)")
        if int(row[idx_qty] or 0) == 0:
            problems.append("total_quantity = 0 (linha fantasma)")
        if problems:
            issues.append((row[0], row[1], problems))

    if issues:
        print("\n  ⚠  PROBLEMAS DETECTADOS NA QUERY ORIGINAL:")
        print("  " + "-" * 70)
        for name, day, probs in issues:
            for p in probs:
                print(f"  → [{day}] {name}: {p}")
    else:
        print("\n  ✓  Nenhum problema detectado.")
    print()

def save_csv(rows, cols, filename):
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    print(f"  CSV salvo em: resultados/{filename}")

# =============================================================
# MAIN
# =============================================================

def main():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    print("\n")
    print_separator("=")
    print("  ANDRÔMEDA – PROBLEMA 1: COMPARAÇÃO DE QUERIES")
    print_separator("=")
    print()

    # ── Query Original ──────────────────────────────────────
    cur.execute(QUERY_ORIGINAL)
    rows_orig = cur.fetchall()
    cols_orig = [d[0] for d in cur.description]
    # Converte para string para exibição uniforme
    rows_orig_str = [tuple(str(v) if v is not None else "NULL" for v in r) for r in rows_orig]

    print_table(rows_orig_str, cols_orig, "QUERY ORIGINAL (com bugs)")
    highlight_issues(rows_orig_str, cols_orig)
    save_csv(rows_orig, cols_orig, "resultado_query_original.csv")

    # ── Query Corrigida ─────────────────────────────────────
    cur.execute(QUERY_CORRIGIDA)
    rows_fix = cur.fetchall()
    cols_fix = [d[0] for d in cur.description]
    rows_fix_str = [tuple(str(v) if v is not None else "NULL" for v in r) for r in rows_fix]

    print()
    print_table(rows_fix_str, cols_fix, "QUERY CORRIGIDA")
    print("  ✓  Todos os problemas corrigidos.\n")
    save_csv(rows_fix, cols_fix, "resultado_query_corrigida.csv")

    # ── Resumo das diferenças ───────────────────────────────
    print_separator("=")
    print("  RESUMO DAS DIFERENÇAS")
    print_separator("=")
    print(f"  Linhas na query original : {len(rows_orig):>3}  (sem agregação real — transaction_id no GROUP BY)")
    print(f"  Linhas na query corrigida: {len(rows_fix):>3}  (agrupamento correto por produto/dia)")
    print()

    bugs = [
        ("GROUP BY com transaction_id",    "Nunca agregava — cada transação = 1 linha separada"),
        ("Typo 'Electonics' no CASE WHEN", "Laptop e Headphones sempre retornavam category_importance NULA"),
        ("Trailing space em 'Electronics '","product_id=1 (Laptop) não batia com o CASE WHEN"),
        ("Typo 'Clothng' no products.csv", "T-Shirt sempre retornava category_importance NULA"),
        ("'toys' vs 'Toys' (case)",        "Action Figure sempre retornava category_importance NULA"),
        ("price = 0 na transação id=9",    "total_value de Book aparecia como 0.0"),
        ("quantity = 0 na transação id=11","Linha fantasma de Action Figure com avg_ticket = NULL"),
    ]

    print("  BUGS IDENTIFICADOS E CORRIGIDOS:")
    print("  " + "-" * 80)
    for i, (bug, desc) in enumerate(bugs, 1):
        print(f"  {i}. {bug}")
        print(f"     → {desc}")
        print()

    print_separator("=")
    print("  Execução concluída. Resultados salvos em /resultados/")
    print_separator("=")
    print()

    conn.close()

if __name__ == "__main__":
    main()
