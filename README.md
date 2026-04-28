# Case Técnico — Andrômeda

Resolução do desafio técnico para a vaga de Engenheiro de Dados na Galaxies.

---

## Estrutura do Repositório

```
projeto_galaxies/
├── problema-01/        # Análise e correção de query SQL
├── problema-02/        # Extração da PokéAPI e modelagem no PostgreSQL
└── problema-03/        # Proposta de arquitetura de dados
```

---

## Problema 1 — Qualidade de Dados e SQL

Análise de uma query SQL com problemas de agrupamento, dados sujos na origem e erros de categorização. Foram identificados 7 problemas — 2 na query e 5 nos dados — e entregues a query corrigida, um script de comparação e o relatório detalhado.

## Problema 2 — Extração de Dados via API

Script Python que extrai todos os 1.350 Pokémons da PokéAPI com paginação, parsing completo e carga em banco PostgreSQL. O modelo relacional normalizado contempla 8 tabelas e mais de 618 mil registros na tabela de movimentos.

**Para executar:**
```bash
cd problema-02
pip install requests psycopg2-binary python-dotenv
cp .env.example .env   # preencha com suas credenciais
python3 codigos/pokeapi_etl.py
python3 codigos/gerar_resultados.py
```

## Problema 3 — Arquitetura de Dados

Proposta de arquitetura centralizada em camadas para a Andrômeda, utilizando Cloud Storage como landing zone, BigQuery para staging e analytics, Cloud Composer (Airflow) para orquestração e Looker Studio para consumo. Inclui relatório com justificativas e diagrama técnico no draw.io.

---

## Tecnologias Utilizadas

- Python 3, requests, psycopg2, python-dotenv
- PostgreSQL 18
- SQLite (ambiente de desenvolvimento)
- SQL (PostgreSQL / MySQL compatível)
- draw.io