"""
=============================================================
Andrômeda – Problema 2: Geração de Resultados (PostgreSQL)
=============================================================
Lê o banco pokemon no Postgres e exporta CSVs de resultado
para a pasta /resultados, além de exibir resumo no terminal.

Uso:
    python3 gerar_resultados.py
=============================================================
"""

import csv
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "pokemon"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")
os.makedirs(RESULTS_DIR, exist_ok=True)


def print_separator(char="=", width=90):
    print(char * width)


def print_table(rows, cols, title, max_rows=15):
    print_separator()
    print(f"  {title}")
    print_separator()
    widths = [len(c) for c in cols]
    for row in rows[:max_rows]:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val) if val is not None else "NULL"))
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  " + "  ".join("-" * w for w in widths)
    print(fmt.format(*cols))
    print(sep)
    for row in rows[:max_rows]:
        print(fmt.format(*[str(v) if v is not None else "NULL" for v in row]))
    if len(rows) > max_rows:
        print(f"\n  ... e mais {len(rows) - max_rows} linhas (veja o CSV completo)")
    print(f"\n  Total: {len(rows)} linhas")
    print_separator()


def save_csv(rows, cols, filename):
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    print(f"  Salvo: resultados/{filename}")


QUERIES = [
    (
        "01_pokemon_completo.csv",
        "Pokémons — visão geral",
        "SELECT id, name, generation, height AS height_dm, weight AS weight_hg, base_experience FROM pokemon ORDER BY id"
    ),
    (
        "02_pokemon_com_tipos.csv",
        "Pokémons com seus tipos (slot 1 = primário)",
        "SELECT p.id, p.name, t.name AS type_name, pt.slot FROM pokemon p JOIN pokemon_types pt ON pt.pokemon_id = p.id JOIN types t ON t.id = pt.type_id ORDER BY p.id, pt.slot"
    ),
    (
        "03_pokemon_com_abilities.csv",
        "Pokémons com habilidades",
        "SELECT p.id, p.name, a.name AS ability_name, pa.is_hidden, pa.slot FROM pokemon p JOIN pokemon_abilities pa ON pa.pokemon_id = p.id JOIN abilities a ON a.id = pa.ability_id ORDER BY p.id, pa.slot"
    ),
    (
        "04_pokemon_stats.csv",
        "Stats base por pokémon",
        "SELECT p.id, p.name, s.stat_name, s.base_stat, s.effort FROM pokemon p JOIN stats s ON s.pokemon_id = p.id ORDER BY p.id, s.stat_name"
    ),
    (
        "05_top10_maior_hp.csv",
        "Top 10 pokémons com maior HP base",
        "SELECT p.id, p.name, p.generation, s.base_stat AS hp FROM pokemon p JOIN stats s ON s.pokemon_id = p.id WHERE s.stat_name = 'hp' ORDER BY hp DESC LIMIT 10"
    ),
    (
        "06_contagem_por_geracao.csv",
        "Contagem de pokémons por geração",
        "SELECT generation, COUNT(*) AS total_pokemon FROM pokemon GROUP BY generation ORDER BY generation"
    ),
    (
        "07_tipos_mais_comuns.csv",
        "Tipos mais comuns",
        "SELECT t.name AS type_name, COUNT(*) AS total_pokemon FROM pokemon_types pt JOIN types t ON t.id = pt.type_id GROUP BY t.name ORDER BY total_pokemon DESC"
    ),
    (
        "08_moves_por_metodo.csv",
        "Moves por método de aprendizado",
        "SELECT learn_method, COUNT(DISTINCT move_id) AS total_moves FROM pokemon_moves GROUP BY learn_method ORDER BY total_moves DESC"
    ),
    (
        "09_resumo_banco.csv",
        "Resumo geral — contagem por tabela",
        """
        SELECT 'pokemon' AS tabela, COUNT(*) AS total FROM pokemon UNION ALL
        SELECT 'types',             COUNT(*)           FROM types  UNION ALL
        SELECT 'abilities',         COUNT(*)           FROM abilities UNION ALL
        SELECT 'moves',             COUNT(*)           FROM moves UNION ALL
        SELECT 'pokemon_types',     COUNT(*)           FROM pokemon_types UNION ALL
        SELECT 'pokemon_abilities', COUNT(*)           FROM pokemon_abilities UNION ALL
        SELECT 'pokemon_moves',     COUNT(*)           FROM pokemon_moves UNION ALL
        SELECT 'stats',             COUNT(*)           FROM stats
        ORDER BY tabela
        """
    ),
]


def main():
    print("\n")
    print_separator()
    print("  ANDRÔMEDA – PROBLEMA 2: RESULTADOS DA EXTRAÇÃO POKÉAPI")
    print_separator()
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    for filename, title, query in QUERIES:
        cur.execute(query)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print_table(rows, cols, title)
        save_csv(rows, cols, filename)
        print()

    cur.close()
    conn.close()

    print_separator()
    print("  Concluído! Todos os CSVs salvos em /resultados/")
    print_separator()
    print()


if __name__ == "__main__":
    main()