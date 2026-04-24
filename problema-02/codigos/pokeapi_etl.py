"""
=============================================================
Andrômeda – Problema 2: Extração da PokeAPI (PostgreSQL)
=============================================================
Extrai todos os Pokémon disponíveis na PokéAPI e persiste
em um banco PostgreSQL local.

Uso:
    pip install requests psycopg2-binary python-dotenv
    cp .env.example .env        # preencha com suas credenciais
    python3 pokeapi_etl.py
=============================================================
"""

import os
import time
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "pokemon"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

BASE_URL      = "https://pokeapi.co/api/v2"
PAGE_SIZE     = 100
REQUEST_DELAY = 0.3
HEADERS       = {"User-Agent": "andromeda-pokeapi-etl/1.0"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# =============================================================
# DDL
# =============================================================

DDL = """
CREATE TABLE IF NOT EXISTS pokemon (
    id              INT          PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    base_experience INT,
    height          INT,
    weight          INT,
    generation      VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS types (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(50)  NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INT NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    type_id    INT NOT NULL REFERENCES types(id)   ON DELETE CASCADE,
    slot       INT,
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE IF NOT EXISTS abilities (
    id   SERIAL        PRIMARY KEY,
    name VARCHAR(100)  NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INT     NOT NULL REFERENCES pokemon(id)   ON DELETE CASCADE,
    ability_id INT     NOT NULL REFERENCES abilities(id) ON DELETE CASCADE,
    is_hidden  BOOLEAN NOT NULL DEFAULT FALSE,
    slot       INT,
    PRIMARY KEY (pokemon_id, ability_id)
);

CREATE TABLE IF NOT EXISTS moves (
    id   SERIAL        PRIMARY KEY,
    name VARCHAR(100)  NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pokemon_moves (
    id               SERIAL       PRIMARY KEY,
    pokemon_id       INT          NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    move_id          INT          NOT NULL REFERENCES moves(id)   ON DELETE CASCADE,
    learn_method     VARCHAR(50),
    level_learned_at INT,
    version_group    VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS stats (
    pokemon_id INT         NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    stat_name  VARCHAR(50) NOT NULL,
    base_stat  INT         NOT NULL,
    effort     INT         NOT NULL DEFAULT 0,
    PRIMARY KEY (pokemon_id, stat_name)
);

CREATE INDEX IF NOT EXISTS idx_pokemon_generation   ON pokemon(generation);
CREATE INDEX IF NOT EXISTS idx_pokemon_types_type   ON pokemon_types(type_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_moves_move   ON pokemon_moves(move_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_moves_method ON pokemon_moves(learn_method);
CREATE INDEX IF NOT EXISTS idx_stats_stat_name      ON stats(stat_name);
"""


# =============================================================
# HELPERS DE REQUISIÇÃO
# =============================================================

def get(url: str, retries: int = 3) -> dict:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            log.warning("Tentativa %d/%d falhou para %s: %s", attempt, retries, url, exc)
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Falha após {retries} tentativas: {url}")


def upsert_type(cur, name: str) -> int:
    cur.execute("INSERT INTO types (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    cur.execute("SELECT id FROM types WHERE name = %s", (name,))
    return cur.fetchone()[0]


def upsert_ability(cur, name: str) -> int:
    cur.execute("INSERT INTO abilities (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    cur.execute("SELECT id FROM abilities WHERE name = %s", (name,))
    return cur.fetchone()[0]


def upsert_move(cur, name: str) -> int:
    cur.execute("INSERT INTO moves (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    cur.execute("SELECT id FROM moves WHERE name = %s", (name,))
    return cur.fetchone()[0]


def fetch_generation(species_url: str) -> str:
    try:
        species = get(species_url)
        return species.get("generation", {}).get("name", "unknown")
    except Exception as exc:
        log.warning("Não foi possível buscar geração: %s", exc)
        return "unknown"


# =============================================================
# PROCESSAMENTO DE UM POKÉMON
# =============================================================

def process_pokemon(cur, raw: dict) -> None:
    pokemon_id = raw["id"]

    cur.execute("SELECT 1 FROM pokemon WHERE id = %s", (pokemon_id,))
    if cur.fetchone():
        log.debug("Pokémon %d já existe, pulando.", pokemon_id)
        return

    generation = fetch_generation(raw["species"]["url"])
    time.sleep(REQUEST_DELAY)

    cur.execute(
        "INSERT INTO pokemon (id, name, base_experience, height, weight, generation) VALUES (%s, %s, %s, %s, %s, %s)",
        (pokemon_id, raw["name"], raw.get("base_experience"),
         raw.get("height"), raw.get("weight"), generation),
    )

    for entry in raw.get("types", []):
        type_id = upsert_type(cur, entry["type"]["name"])
        cur.execute(
            "INSERT INTO pokemon_types (pokemon_id, type_id, slot) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (pokemon_id, type_id, entry["slot"]),
        )

    for entry in raw.get("abilities", []):
        ability_id = upsert_ability(cur, entry["ability"]["name"])
        cur.execute(
            "INSERT INTO pokemon_abilities (pokemon_id, ability_id, is_hidden, slot) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (pokemon_id, ability_id, entry["is_hidden"], entry["slot"]),
        )

    moves_data = []
    for entry in raw.get("moves", []):
        move_id = upsert_move(cur, entry["move"]["name"])
        for vgd in entry.get("version_group_details", []):
            moves_data.append((
                pokemon_id, move_id,
                vgd["move_learn_method"]["name"],
                vgd["level_learned_at"],
                vgd["version_group"]["name"],
            ))
    if moves_data:
        execute_values(
            cur,
            "INSERT INTO pokemon_moves (pokemon_id, move_id, learn_method, level_learned_at, version_group) VALUES %s",
            moves_data,
        )

    stats_data = [
        (pokemon_id, e["stat"]["name"], e["base_stat"], e["effort"])
        for e in raw.get("stats", [])
    ]
    if stats_data:
        execute_values(
            cur,
            "INSERT INTO stats (pokemon_id, stat_name, base_stat, effort) VALUES %s ON CONFLICT DO NOTHING",
            stats_data,
        )


# =============================================================
# LOOP PRINCIPAL
# =============================================================

def run():
    log.info("Conectando ao banco PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    log.info("Criando tabelas...")
    cur.execute(DDL)
    conn.commit()

    offset    = 0
    total     = None
    processed = 0

    log.info("Iniciando extração da PokéAPI...")

    while True:
        page_url = f"{BASE_URL}/pokemon?limit={PAGE_SIZE}&offset={offset}"
        log.info("Buscando página: offset=%d (processados: %d)", offset, processed)

        page    = get(page_url)
        total   = total or page["count"]
        results = page.get("results", [])

        if not results:
            break

        for entry in results:
            try:
                raw = get(entry["url"])
                process_pokemon(cur, raw)
                conn.commit()
                processed += 1
                if processed % 50 == 0:
                    log.info("Progresso: %d/%d pokémons salvos", processed, total)
                time.sleep(REQUEST_DELAY)
            except Exception as exc:
                log.error("Erro ao processar %s: %s", entry["name"], exc)
                conn.rollback()

        offset += PAGE_SIZE

        if not page.get("next"):
            break

    cur.close()
    conn.close()
    log.info("Extração concluída! Total salvo: %d pokémons.", processed)


if __name__ == "__main__":
    run()