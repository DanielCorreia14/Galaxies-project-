-- =============================================================
-- QUERY CORRIGIDA – Andrômeda | Vendas por Dia e Categoria
-- =============================================================
-- Pré-requisito: antes de rodar, limpar os dados na origem.
-- Os scripts de limpeza estão documentados no relatório.
-- =============================================================

SELECT
    p.product_name,
    DATE(t.transaction_date)                        AS transaction_day,

    -- FIX 1: corrigidos os typos e espaços extras das categorias
    -- 'Electonics' → 'Electronics', 'toys' → 'Toys', 'Clothing' (sem trailing space)
    CASE
        WHEN TRIM(p.category) = 'Electronics' THEN 'High'
        WHEN TRIM(p.category) = 'Books'       THEN 'Medium'
        WHEN TRIM(p.category) = 'Furniture'   THEN 'Low'
        WHEN TRIM(p.category) = 'Stationery'  THEN 'Low'
        WHEN TRIM(p.category) = 'Clothing'    THEN 'Low'
        WHEN TRIM(p.category) = 'Toys'        THEN 'Low'
        ELSE NULL
    END                                             AS category_importance,

    SUM(t.quantity)                                 AS total_quantity,

    -- FIX 2: ignora linhas com price = 0 (dados sujos) para não distorcer total_value
    SUM(CASE WHEN t.price > 0 THEN t.price * t.quantity ELSE 0 END) AS total_value,

    -- FIX 2 (cont.): avg_ticket só sobre transações com valor real
    CASE
        WHEN SUM(CASE WHEN t.price > 0 THEN t.quantity ELSE 0 END) > 0
        THEN SUM(CASE WHEN t.price > 0 THEN t.price * t.quantity ELSE 0 END)
             / SUM(CASE WHEN t.price > 0 THEN t.quantity ELSE 0 END)
        ELSE 0
    END                                             AS avg_ticket

FROM        transactions t
LEFT JOIN   products     p
    ON      t.product_id = p.product_id

-- FIX 3: removido transaction_id do GROUP BY — ele impede qualquer agregação
-- FIX 4: quantidade 0 excluída para não gerar linhas fantasma
WHERE       t.quantity > 0

GROUP BY
    p.product_name,
    TRIM(p.category),
    transaction_day

ORDER BY
    transaction_day,
    category_importance;
