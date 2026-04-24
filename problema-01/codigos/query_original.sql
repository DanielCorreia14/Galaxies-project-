SELECT
            p.product_name,
            DATE(t.transaction_date) AS transaction_day,
            CASE 
                WHEN p.category = 'Electonics' THEN 'High'
                WHEN p.category = 'Books' THEN 'Medium'
                WHEN p.category = 'Furniture' THEN 'Low'
                WHEN p.category = 'Stationery' THEN 'Low'
                WHEN p.category = 'Clothing' THEN 'Low'
                WHEN p.category = 'toys' THEN 'Low'
                ELSE NULL
            END AS category_importance,
            SUM(t.quantity) AS total_quantity,
            SUM(t.price * t.quantity) AS total_value,
            SUM(t.price * t.quantity) / SUM(t.quantity) AS avg_ticket
FROM        transactions t
LEFT JOIN   products     p
ON          t.product_id = p.product_id
GROUP BY
    p.product_name,
    p.category,
    transaction_day,
    t.transaction_id;
