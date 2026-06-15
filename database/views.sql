DROP MATERIALIZED VIEW IF EXISTS vw_kpi_vendas;
CREATE MATERIALIZED VIEW vw_kpi_vendas AS
SELECT
    date_trunc('month', pagamento)::date AS mes,
    SUM(valor)::numeric(14,2) AS faturamento_mensal,
    COUNT(DISTINCT contrato_id) AS contratos_pagos
FROM contas_receber
WHERE status = 'PAGO'
GROUP BY date_trunc('month', pagamento)
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vw_kpi_vendas_mes ON vw_kpi_vendas(mes);

CREATE OR REPLACE FUNCTION refresh_kpi_vendas()
RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = public AS
$$ REFRESH MATERIALIZED VIEW vw_kpi_vendas; $$;
