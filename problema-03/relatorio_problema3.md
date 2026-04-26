# Proposta de Arquitetura de Dados
**Case Técnico Andrômeda | Problema 3**

---

## Contexto

A Andrômeda opera com quatro fontes de dados distintas e sem integração entre si: transações armazenadas em MongoDB, catálogo de produtos em arquivos CSV, logs de navegação em JSON e dados de parceiros consumidos via APIs externas. A ausência de uma camada centralizada compromete a capacidade analítica da empresa e dificulta a tomada de decisão baseada em dados.

O objetivo é definir uma arquitetura moderna que centralize essas fontes, garanta qualidade e rastreabilidade dos dados e suporte o crescimento do negócio.

---

## Arquitetura Recomendada

Das três opções apresentadas, a recomendação é a **Opção 3 — Pipeline Estruturado em Camadas**, composta por Cloud Storage como landing zone, BigQuery com camadas de staging e analytics, Cloud Composer (Airflow) como orquestrador e Looker Studio como camada de consumo.

---

## Análise das Opções

**Opção 1 — Data Lake puro no Cloud Storage**

Centraliza o armazenamento, mas transfere toda a complexidade de transformação e interpretação para o analista no momento da consulta. Sem uma camada de transformação estruturada, os dados brutos tendem a acumular inconsistências ao longo do tempo, tornando as análises cada vez mais custosas e sujeitas a erros. O modelo não escala bem à medida que o volume e a variedade de fontes crescem.

**Opção 2 — ETL manual com scripts Python agendados**

Funciona bem em estágios iniciais, mas apresenta limitações críticas de operação: ausência de retry nativo em caso de falha, falta de visibilidade sobre o estado dos pipelines, dependências implícitas entre scripts e dificuldade de manutenção conforme o número de fontes aumenta. O custo operacional cresce de forma desproporcional ao volume de dados.

**Opção 3 — Pipeline estruturado**

Endereça as limitações das duas anteriores. A separação em camadas garante rastreabilidade e qualidade progressiva dos dados. A orquestração centralizada reduz o risco operacional. A escolha de serviços gerenciados (BigQuery, Cloud Composer) elimina a necessidade de gerenciar infraestrutura e permite que o time de dados foque em geração de valor.

---

## Justificativa por Critério

**Governança**

O modelo em camadas — raw, staging e analytics — estabelece um contrato claro sobre o estado dos dados em cada etapa. A camada raw preserva os dados brutos sem modificação, garantindo que qualquer reprocessamento parta da fonte original. O BigQuery oferece controle de acesso granular por dataset e projeto. O Airflow registra cada execução com logs auditáveis, possibilitando rastreabilidade completa de origem a consumo.

**Escalabilidade**

O Cloud Storage suporta qualquer volume de dados sem necessidade de provisionamento. O BigQuery é serverless e escala automaticamente para queries sobre terabytes de dados. A adição de uma nova fonte de dados representa a criação de uma nova DAG no Airflow, sem impacto nas pipelines existentes.

**Manutenção**

A centralização da orquestração no Airflow elimina scripts dispersos e sem monitoramento. Falhas são detectadas automaticamente, retry é configurado por tarefa e alertas podem ser enviados ao time responsável. O histórico de execuções facilita a identificação de padrões de falha e a análise de SLA.

**Custos**

Os serviços propostos operam no modelo pay-per-use. O BigQuery cobra por volume de dados processado em queries e por armazenamento, sem custo de infraestrutura ociosa. Para um e-commerce em expansão, esse modelo é mais previsível e eficiente do que manter servidores dedicados com capacidade provisionada para picos.

---

## Arquitetura em Camadas

### Camada Raw — Cloud Storage

Ponto de entrada de todos os dados. Cada fonte grava em um prefixo particionado por data, preservando o dado original sem transformação.

| Fonte | Caminho no Storage | Frequência |
|---|---|---|
| MongoDB — Transações | /raw/transactions/YYYY-MM-DD/ | Diária |
| CSV — Produtos | /raw/products/YYYY-MM-DD/ | Sob demanda |
| JSON — Logs de Navegação | /raw/logs/YYYY-MM-DD/ | Near real-time |
| APIs Externas | /raw/api/YYYY-MM-DD/ | Conforme disponibilidade |

### Camada Staging — BigQuery

Responsável pela limpeza, tipagem e padronização dos dados brutos. Nenhum dado desta camada é exposto diretamente para consumo analítico.

| Tabela | Transformações aplicadas |
|---|---|
| stg_transactions | Limpeza de nulos, conversão de tipos, deduplicação |
| stg_products | Normalização de categorias, deduplicação por SKU |
| stg_logs | Parsing de campos JSON, enriquecimento com session_id |
| stg_api | Normalização de schema, tratamento de campos opcionais |

### Camada Analytics — BigQuery

Modelos de negócio prontos para consumo. Os dados desta camada são estáveis, documentados e acessíveis para times de produto, marketing e operações.

| Tabela | Descrição |
|---|---|
| fct_vendas | Fato de vendas com granularidade por transação |
| dim_produtos | Dimensão de produtos com hierarquia de categorias |
| dim_usuarios | Dimensão de usuários com perfil comportamental |
| agg_navegacao | Agregação de logs para análise de funil de conversão |

### Orquestração — Cloud Composer (Airflow)

Responsável por coordenar todas as etapas do pipeline: ingestão das fontes, transformação na camada staging e materialização na camada analytics. Cada pipeline é definido como uma DAG independente, com agendamento, retry configurável e alertas em caso de falha.

### Consumo — Looker Studio

Interface de visualização conectada diretamente à camada analytics do BigQuery. Dashboards principais previstos: acompanhamento de vendas por período e categoria, análise de desempenho de produtos e funil de conversão com base nos logs de navegação.

---

## Comparativo das Opções

| Critério | Opção 1 — Data Lake puro | Opção 2 — ETL manual | Opção 3 — Pipeline estruturado |
|---|---|---|---|
| Governança | Baixa | Média | Alta |
| Escalabilidade | Média | Baixa | Alta |
| Manutenção | Complexa | Complexa | Centralizada |
| Monitoramento | Manual | Manual | Nativo via Airflow |
| Rastreabilidade | Nenhuma | Parcial | Completa |
| Custo inicial | Baixo | Baixo | Médio |
| Custo no longo prazo | Alto | Alto | Eficiente |

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `relatorio_problema3.md` | Este documento |
| `drawio arquitetura.png` | Driagrama técnico da arquitetura para visualização em modo foto |
| `arquitetura_drawio.xml` | Diagrama técnico da arquitetura para importação no draw.io |
