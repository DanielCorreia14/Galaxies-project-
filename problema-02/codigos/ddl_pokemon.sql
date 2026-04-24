-- =============================================================
-- DDL – Modelo Relacional Normalizado | Andrômeda Pokémon ETL
-- Compatível com PostgreSQL e MySQL
-- Para PostgreSQL: trocar AUTOINCREMENT por SERIAL
-- Para MySQL: trocar TEXT por VARCHAR(255) onde necessário
-- =============================================================

-- Pokémon principal
CREATE TABLE IF NOT EXISTS pokemon (
    id              INT          PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    base_experience INT,
    height          INT,                      
    weight          INT,                      
    generation      VARCHAR(50)               
);

-- Tipos (grass, fire, water, poison…)
CREATE TABLE IF NOT EXISTS types (
    id   SERIAL       PRIMARY KEY,            -- MySQL: INT AUTO_INCREMENT
    name VARCHAR(50)  NOT NULL UNIQUE
);

-- Relação N:N pokémon ↔ tipo (slot 1 = tipo primário)
CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INT NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    type_id    INT NOT NULL REFERENCES types(id)   ON DELETE CASCADE,
    slot       INT,
    PRIMARY KEY (pokemon_id, type_id)
);

-- Habilidades
CREATE TABLE IF NOT EXISTS abilities (
    id   SERIAL        PRIMARY KEY,
    name VARCHAR(100)  NOT NULL UNIQUE
);

-- Relação N:N pokémon ↔ habilidade
CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id)   ON DELETE CASCADE,
    ability_id INTEGER NOT NULL REFERENCES abilities(id) ON DELETE CASCADE,
    is_hidden  BOOLEAN NOT NULL DEFAULT FALSE,
    slot       INTEGER,
    PRIMARY KEY (pokemon_id, ability_id)
);

-- Movimentos
CREATE TABLE IF NOT EXISTS moves (
    id   SERIAL        PRIMARY KEY,
    name VARCHAR(100)  NOT NULL UNIQUE
);

-- Relação N:N pokémon ↔ move (com contexto de aprendizado por versão)
CREATE TABLE IF NOT EXISTS pokemon_moves (
    id               SERIAL       PRIMARY KEY,
    pokemon_id       INT          NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    move_id          INT          NOT NULL REFERENCES moves(id)   ON DELETE CASCADE,
    learn_method     VARCHAR(50),              -- level-up, machine, egg, tutor
    level_learned_at INT,                      -- 0 = não aprendido por level-up
    version_group    VARCHAR(100)              -- ex: 'sword-shield'
);

-- Stats base (hp, attack, defense, special-attack, special-defense, speed)
CREATE TABLE IF NOT EXISTS stats (
    pokemon_id INT         NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    stat_name  VARCHAR(50) NOT NULL,
    base_stat  INT         NOT NULL,
    effort     INT         NOT NULL DEFAULT 0,
    PRIMARY KEY (pokemon_id, stat_name)
);

-- Índices recomendados para queries analíticas
CREATE INDEX IF NOT EXISTS idx_pokemon_generation   ON pokemon(generation);
CREATE INDEX IF NOT EXISTS idx_pokemon_types_type   ON pokemon_types(type_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_moves_move   ON pokemon_moves(move_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_moves_method ON pokemon_moves(learn_method);
CREATE INDEX IF NOT EXISTS idx_stats_stat_name      ON stats(stat_name);
