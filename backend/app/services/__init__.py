"""
app/services/__init__.py — Exportações dos serviços da aplicação.

Serviços disponíveis:
  - snmp_service     : leitura de contadores via SNMP
  - relatorio_service: lógica de negócio dos relatórios (cálculos financeiros)
"""

from app.services.snmp_service import (  # noqa: F401
    ler_contador_snmp,
    testar_conectividade_snmp,
    SNMPResultado,
    OIDS_CONTADOR_TOTAL,
)

from app.services.relatorio_service import (  # noqa: F401
    calcular_paginas_periodo,
    calcular_valor_impressao,
    calcular_indicadores_contrato,
    BreakdownImpressao,
    IndicadoresContrato,
)
