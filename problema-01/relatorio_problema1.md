# Relatório de Análise – Query de Vendas por Dia
**Case Técnico Andrômeda | Problema 1**

---

## Contexto

A equipe de dados da Andrômeda utiliza uma query SQL para consolidar vendas diárias por produto, exibindo quantidade total vendida, valor total e ticket médio, classificados por importância de categoria. Foram relatados quatro problemas: `category_importance` nula em alguns casos, `total_value` incorreto, duplicação de usuários no agrupamento e a query parando de funcionar após o dia 03/08/2025.

A análise foi feita diretamente nos dados (`transactions.csv` e `products.csv`) e na query fornecida. Foram encontrados **7 problemas no total** — 2 na query e 5 nos dados de origem.

---

## Problemas Encontrados

### 1. `GROUP BY` incluindo `transaction_id` — agrupamento quebrado

**Tipo:** Bug na query  
**Impacto:** Duplicação de linhas — nunca havia agregação real

O `GROUP BY` original incluía `t.transaction_id`, que é uma chave única por transação. Como nenhuma linha compartilha o mesmo `transaction_id`, o `SUM()` nunca somava nada — cada transação virava uma linha isolada no resultado. Isso causava a "duplicação de usuários" relatada.

```sql
-- ORIGINAL (errado)
GROUP BY p.product_name, p.category, transaction_day, t.transaction_id

-- CORRIGIDO
GROUP BY p.product_name, TRIM(p.category), transaction_day
```

**Evidência no resultado:** a query original retornava **12 linhas** (uma por transação). A corrigida retorna **10 linhas**, com as transações do mesmo produto/dia corretamente somadas. O Notebook em 02/08, por exemplo, tinha duas transações (5 e 10 unidades) que apareciam separadas na original e foram consolidadas em 15 unidades na corrigida.

---

### 2. Typo `'Electonics'` no `CASE WHEN` — categoria sempre nula

**Tipo:** Bug na query  
**Impacto:** `category_importance` nula para todos os produtos Electronics

A query original testava `p.category = 'Electonics'` (faltava o segundo `'r'`), então nenhum produto do tipo Electronics batia com a condição e caía no `ELSE NULL`.

```sql
-- ORIGINAL (errado)
WHEN p.category = 'Electonics' THEN 'High'

-- CORRIGIDO
WHEN TRIM(p.category) = 'Electronics' THEN 'High'
```

---

### 3. Trailing space em `'Electronics '` no `products.csv` — Laptop sem importância

**Tipo:** Dado sujo na origem  
**Impacto:** `category_importance` nula para o Laptop (product_id = 1)

O `product_id = 1` (Laptop) estava cadastrado com `category = 'Electronics '` — um espaço extra no final. Mesmo corrigindo o typo da query, esse produto continuaria sem bater com o `CASE WHEN`. Corrigido com `TRIM()` na query e recomendação de `UPDATE` na tabela de origem.

**Correção recomendada na origem:**
```sql
UPDATE products SET category = TRIM(category);
```

---

### 4. Typo `'Clothng'` no `products.csv` — T-Shirt sem importância

**Tipo:** Dado sujo na origem  
**Impacto:** `category_importance` sempre nula para o T-Shirt (product_id = 6)

A categoria estava grafada como `'Clothng'` (faltava o `'i'`). Nenhuma condição do `CASE WHEN` cobria esse valor.

**Correção recomendada na origem:**
```sql
UPDATE products SET category = 'Clothing' WHERE category = 'Clothng';
```

---

### 5. `'toys'` vs `'Toys'` — Action Figure sem importância

**Tipo:** Dado sujo na origem  
**Impacto:** `category_importance` nula para Action Figure (product_id = 7)

A query testava `'toys'` (minúsculo), mas o valor no CSV era `'Toys'`. A query corrigida padroniza para `'Toys'` com `TRIM()`.

---

### 6. `price = 0` na transação id=9 — `total_value` incorreto para Book

**Tipo:** Dado sujo na origem  
**Impacto:** Book (3 unidades vendidas) aparecia com `total_value = 0.0`

A transação do produto Book (product_id = 5) estava com `price = 0.0`, zerando completamente o valor mesmo com 3 unidades vendidas. A query corrigida exclui preços zerados do cálculo. A investigação da origem desse dado na fonte é recomendada (possível falha no sistema de PDV ou importação incorreta).

```sql
-- CORRIGIDO
SUM(CASE WHEN t.price > 0 THEN t.price * t.quantity ELSE 0 END) AS total_value
```

---

### 7. `quantity = 0` na transação id=11 — linha fantasma com `avg_ticket = NULL`

**Tipo:** Dado sujo na origem  
**Impacto:** Action Figure aparecia no resultado com quantidade 0 e `avg_ticket = NULL`

A transação do Action Figure tinha `quantity = 0` com `price = 120.0` — uma venda inválida que gerava uma linha no resultado com divisão por zero no `avg_ticket`. A query corrigida filtra com `WHERE t.quantity > 0`.

---

## Resultado

A tabela abaixo compara o output das duas queries rodando sobre os mesmos dados:

### Query Original — 12 linhas (com problemas)

| product_name  | transaction_day | category_importance | total_quantity | total_value | avg_ticket |
|---------------|-----------------|---------------------|----------------|-------------|------------|
| Laptop        | 2025-08-01      | **NULL** ⚠          | 1              | 2500.0      | 2500.0     |
| Headphones    | 2025-08-01      | **NULL** ⚠          | 2              | 400.0       | 200.0      |
| Office Chair  | 2025-08-01      | Low                 | 1              | 450.0       | 450.0      |
| Notebook      | 2025-08-02      | Low                 | 5              | 50.0        | 10.0       |
| Laptop        | 2025-08-02      | **NULL** ⚠          | 1              | 2500.0      | 2500.0     |
| Headphones    | 2025-08-02      | **NULL** ⚠          | 1              | 200.0       | 200.0      |
| Notebook      | 2025-08-02      | Low                 | **10** ⚠       | 100.0       | 10.0       |
| Office Chair  | 2025-08-02      | Low                 | 1              | 450.0       | 450.0      |
| Book          | 2025-08-03      | Medium              | 3              | **0.0** ⚠   | 0.0        |
| T-Shirt       | 2025-08-03      | **NULL** ⚠          | 2              | 100.0       | 50.0       |
| Action Figure | 2025-08-03      | **NULL** ⚠          | **0** ⚠        | **0.0** ⚠   | **NULL** ⚠ |
| Gift Card     | 2025-08-03      | **NULL** ⚠          | 1              | 100.0       | 100.0      |

---

### Query Corrigida — 10 linhas (resultado esperado)

| product_name | transaction_day | category_importance | total_quantity | total_value | avg_ticket |
|--------------|-----------------|---------------------|----------------|-------------|------------|
| Headphones   | 2025-08-01      | High                | 2              | 400.0       | 200.0      |
| Laptop       | 2025-08-01      | High                | 1              | 2500.0      | 2500.0     |
| Office Chair | 2025-08-01      | Low                 | 1              | 450.0       | 450.0      |
| Headphones   | 2025-08-02      | High                | 1              | 200.0       | 200.0      |
| Laptop       | 2025-08-02      | High                | 1              | 2500.0      | 2500.0     |
| Notebook     | 2025-08-02      | Low                 | **15** ✓       | 150.0       | 10.0       |
| Office Chair | 2025-08-02      | Low                 | 1              | 450.0       | 450.0      |
| T-Shirt      | 2025-08-03      | Low ✓               | 2              | 100.0       | 50.0       |
| Gift Card    | 2025-08-03      | High                | 1              | 100.0       | 100.0      |
| Book         | 2025-08-03      | Medium              | 3              | 0**         | 0          |

> **Book permanece com `total_value = 0` pois o `price = 0` está na transação de origem. Investigação e correção na fonte são recomendadas.

---

## Resumo das Correções

| # | Onde | Problema | Correção |
|---|------|----------|----------|
| 1 | Query | `transaction_id` no `GROUP BY` impedia agregação | Removido do `GROUP BY` |
| 2 | Query | Typo `'Electonics'` no `CASE WHEN` | Corrigido + `TRIM()` aplicado |
| 3 | Dados | Trailing space em `'Electronics '` (product_id=1) | `TRIM()` na query + `UPDATE` recomendado |
| 4 | Dados | Typo `'Clothng'` (product_id=6) | `UPDATE` aplicado na origem — `category_importance` corrigida para `Low` |
| 5 | Dados | `'toys'` com case errado (product_id=7) | Padronizado para `'Toys'` na query |
| 6 | Dados | `price = 0` na transação id=9 | Excluído do cálculo via `CASE WHEN price > 0` |
| 7 | Dados | `quantity = 0` na transação id=11 | Filtrado via `WHERE t.quantity > 0` |

---

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `codigos/query_original.sql` | Query original com os bugs |
| `codigos/query_corrigida.sql` | Query com todas as correções aplicadas |
| `codigos/comparar_queries.py` | Script Python que roda as duas queries e exibe as diferenças |
| `resultados/resultado_query_original.csv` | Output da query original |
| `resultados/resultado_query_corrigida.csv` | Output da query corrigida |