# Relatório de Extração – PokéAPI
**Case Técnico Andrômeda | Problema 2**

---

## Contexto

A Andrômeda quer integrar dados de Pokémon para uma campanha do **Dia das Crianças**. O objetivo é extrair todos os Pokémons disponíveis na PokéAPI, incluindo habilidades, moveset e dados complementares, e armazená-los em um banco relacional para análises futuras.

---

## Solução

### Extração

O script `pokeapi_etl.py` consome a PokéAPI em duas etapas por Pokémon:

1. **Listagem paginada** — endpoint `/pokemon?limit=100&offset=N` retorna blocos de 100 Pokémons por vez, com um campo `next` indicando se há mais páginas.
2. **Detalhe individual** — para cada Pokémon, uma chamada ao endpoint `/pokemon/{id}` retorna abilities, moves, types e stats. Uma segunda chamada a `/pokemon-species/{id}` retorna a geração.

No total foram realizadas **~2.700 requisições** para cobrir os 1.350 Pokémons. O script adiciona um delay de 0.3s entre chamadas para respeitar o rate limit da API. A extração completa levou aproximadamente **17 minutos**.

### Resiliência

- **Retry com backoff exponencial** — se uma requisição falha, tenta até 3 vezes com espera crescente (2s, 4s, 8s).
- **Idempotente** — se a execução for interrompida, pode ser retomada sem duplicar dados (`ON CONFLICT DO NOTHING` + checagem de existência antes de inserir).
- **Commit por Pokémon** — cada Pokémon é commitado individualmente, garantindo que uma falha não desfaça o progresso anterior.

### Credenciais

As credenciais do banco são lidas de um arquivo `.env` (não versionado). O repositório contém um `.env.example` como referência:

```
DB_HOST=172.30.96.1
DB_PORT=5432
DB_NAME=pokemon
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
```

---

## Modelo de Dados

### Por que relacional normalizado?

O modelo **relacional normalizado** foi escolhido porque:

- **Moves e abilities são entidades compartilhadas** — o mesmo `tackle` é aprendido por centenas de Pokémons. Desnormalizar criaria centenas de milhares de strings repetidas.
- **Facilita queries analíticas** — filtrar por tipo, habilidade ou geração é simples com JOINs e índices.
- **Integridade referencial** — chaves estrangeiras garantem consistência entre as tabelas.
- **Extensível** — novos atributos podem ser adicionados como novas tabelas sem alterar as existentes.

### Diagrama

```
pokemon
├── id (PK)
├── name
├── base_experience
├── height              (em decímetros)
├── weight              (em hectogramas)
└── generation          (ex: 'generation-i')

pokemon_types (N:N)           types
├── pokemon_id (FK) ────────► ├── id (PK)
├── type_id    (FK)           └── name
└── slot

pokemon_abilities (N:N)       abilities
├── pokemon_id (FK) ────────► ├── id (PK)
├── ability_id (FK)           └── name
├── is_hidden
└── slot

pokemon_moves (N:N)           moves
├── pokemon_id   (FK) ──────► ├── id (PK)
├── move_id      (FK)         └── name
├── learn_method
├── level_learned_at
└── version_group

stats
├── pokemon_id (FK, PK)
├── stat_name  (PK)
├── base_stat
└── effort
```

---

## Resultado da Extração

Extração executada em **23/04/2026**. Números reais carregados no banco PostgreSQL:

| Tabela | Total de registros |
|---|---|
| `pokemon` | 1.350 |
| `types` | 18 |
| `abilities` | 310 |
| `moves` | 833 |
| `pokemon_types` | 2.115 |
| `pokemon_abilities` | 2.926 |
| `pokemon_moves` | 618.519 |
| `stats` | 8.100 |

### Destaques dos dados

**Pokémons com maior HP base:**

| # | Nome | Geração | HP |
|---|---|---|---|
| 1 | blissey | generation-ii | 255 |
| 2 | eternatus-eternamax | generation-viii | 255 |
| 3 | chansey | generation-i | 250 |
| 4 | guzzlord | generation-vii | 223 |
| 5 | zygarde-complete | generation-vi | 216 |

**Pokémons por geração:**

| Geração | Total |
|---|---|
| generation-i | 238 |
| generation-v | 185 |
| generation-iii | 167 |
| generation-ix | 149 |
| generation-viii | 133 |
| generation-vii | 131 |
| generation-iv | 129 |
| generation-vi | 103 |
| generation-ii | 115 |

**Tipos mais comuns:**

| Tipo | Total de Pokémons |
|---|---|
| water | 192 |
| normal | 160 |
| grass | 156 |
| flying | 154 |
| psychic | 141 |

**Moves por método de aprendizado:**

| Método | Total de moves distintos |
|---|---|
| level-up | 789 |
| egg | 499 |
| machine | 340 |
| tutor | 193 |

> A tabela `pokemon_moves` possui **618.519 registros** porque um mesmo move pode ser aprendido de formas diferentes em versões diferentes do jogo — cada combinação pokémon + move + método + versão é uma linha, preservando o histórico completo do moveset.

---

## Como Executar

```bash
# 1. Instala dependências
pip install requests psycopg2-binary python-dotenv

# 2. Cria e preenche o arquivo de credenciais
cp .env.example .env
# edite o .env com sua senha do Postgres

# 3. Roda o ETL (~17 minutos para 1.350 pokémons)
python3 codigos/pokeapi_etl.py

# 4. Gera os CSVs de resultado
python3 codigos/gerar_resultados.py
```

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `codigos/pokeapi_etl.py` | Script de extração e carga no banco |
| `codigos/ddl_pokemon.sql` | DDL das tabelas (referência para Postgres/MySQL) |
| `codigos/gerar_resultados.py` | Gera CSVs de análise e resumo no terminal |
| `.env.example` | Modelo de configuração de credenciais |
| `.gitignore` | Exclui `.env`, `*.db` e `resultados/` do versionamento |
| `resultados/01_pokemon_completo.csv` | Todos os pokémons com dados principais |
| `resultados/02_pokemon_com_tipos.csv` | Pokémons com seus tipos |
| `resultados/03_pokemon_com_abilities.csv` | Pokémons com habilidades |
| `resultados/04_pokemon_stats.csv` | Stats base de todos os pokémons |
| `resultados/05_top10_maior_hp.csv` | Top 10 por HP base |
| `resultados/06_contagem_por_geracao.csv` | Pokémons agrupados por geração |
| `resultados/07_tipos_mais_comuns.csv` | Ranking de tipos |
| `resultados/08_moves_por_metodo.csv` | Moves por método de aprendizado |
| `resultados/09_resumo_banco.csv` | Contagem de registros por tabela |