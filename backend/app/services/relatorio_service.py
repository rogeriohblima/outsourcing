"""
services/relatorio_service.py — Lógica de negócio reutilizável para relatórios.

Separa os cálculos financeiros e de indicadores dos routers,
facilitando testes unitários e reuso em outros contextos.

Funções principais:
  calcular_paginas_periodo()  — calcula impressões entre dois contadores
  calcular_valor_impressao()  — aplica modelo de franquia + excedente
  calcular_indicadores()      — percentuais de tempo e orçamento do contrato
"""

from datetime import date
from decimal import Decimal
from typing import NamedTuple


# ── Tipos de retorno ──────────────────────────────────────────────────────────

class BreakdownImpressao(NamedTuple):
    """Resultado financeiro de um período de impressão."""
    paginas:              int
    dentro_franquia:      int
    excedente:            int
    valor_franquia:       Decimal
    valor_excedente:      Decimal
    valor_total:          Decimal
    pct_franquia_usada:   float   # percentual da franquia consumida (0–100+)


class IndicadoresContrato(NamedTuple):
    """Indicadores percentuais de tempo e orçamento do contrato."""
    dias_totais:          int
    dias_decorridos:      int
    dias_restantes:       int
    pct_tempo:            float   # 0–100
    pct_orcamento:        float   # 0–100 (pode ultrapassar 100 se excedido)
    vigente:              bool
    encerrado:            bool
    a_iniciar:            bool    # True se a data de início ainda não chegou
    saldo_orcamento:      Decimal


# ── Funções principais ────────────────────────────────────────────────────────

def calcular_paginas_periodo(contador_atual: int, contador_anterior: int) -> int:
    """
    Calcula o número de páginas impressas entre duas leituras de contador.

    O contador é cumulativo (totalizador), então a diferença entre duas
    leituras consecutivas representa as páginas do período.

    Garante que o resultado nunca seja negativo (em caso de troca de
    impressora ou erro de lançamento).

    Args:
        contador_atual    : valor do totalizador na leitura atual
        contador_anterior : valor do totalizador na leitura anterior (ou 0)

    Returns:
        número de páginas impressas no período (>= 0)
    """
    return max(0, contador_atual - contador_anterior)


def calcular_valor_impressao(
    paginas: int,
    franquia: int,
    valor_franquia: Decimal,
    valor_extra_franquia: Decimal,
) -> BreakdownImpressao:
    """
    Calcula o valor a pagar baseado no modelo de franquia + excedente.

    Modelo contratual:
      - Até 'franquia' páginas: paga-se apenas o valor_franquia (custo fixo)
      - Acima de 'franquia': paga-se valor_franquia + (excedente × valor_extra)

    Args:
        paginas               : total de páginas impressas no período
        franquia              : quantidade de páginas inclusas no custo fixo mensal
        valor_franquia        : custo fixo mensal em R$ (Decimal para precisão)
        valor_extra_franquia  : custo por página acima da franquia em R$ (Decimal)

    Returns:
        BreakdownImpressao com todos os valores calculados
    """
    dentro_franquia = min(paginas, franquia)
    excedente       = max(0, paginas - franquia)
    valor_excedente = Decimal(excedente) * valor_extra_franquia
    valor_total     = valor_franquia + valor_excedente

    pct_franquia = (
        float(dentro_franquia / franquia * 100) if franquia > 0 else 0.0
    )

    return BreakdownImpressao(
        paginas=paginas,
        dentro_franquia=dentro_franquia,
        excedente=excedente,
        valor_franquia=valor_franquia,
        valor_excedente=valor_excedente,
        valor_total=valor_total,
        pct_franquia_usada=round(pct_franquia, 2),
    )


def calcular_indicadores_contrato(
    data_inicio: date,
    data_termino: date,
    total_empenhado: Decimal,
    total_gasto: Decimal,
    data_referencia: date | None = None,
) -> IndicadoresContrato:
    """
    Calcula os indicadores percentuais de tempo e orçamento de um contrato.

    Indicadores calculados:
      - Percentual de tempo decorrido (dias passados / dias totais × 100)
      - Percentual de orçamento consumido (gasto / empenhado × 100)
      - Saldo de orçamento disponível
      - Status de vigência (vigente, encerrado, a iniciar)

    Args:
        data_inicio      : data de início da vigência do contrato
        data_termino     : data de término da vigência do contrato
        total_empenhado  : valor total empenhado/orçado (Decimal)
        total_gasto      : valor total consumido até o momento (Decimal)
        data_referencia  : data base para cálculo (padrão: hoje)

    Returns:
        IndicadoresContrato com todos os percentuais e status
    """
    hoje = data_referencia or date.today()

    dias_totais     = max(1, (data_termino - data_inicio).days)
    dias_decorridos = max(0, min(dias_totais, (hoje - data_inicio).days))
    dias_restantes  = max(0, (data_termino - hoje).days)

    pct_tempo      = round(dias_decorridos / dias_totais * 100, 2)
    pct_orcamento  = (
        round(float(total_gasto / total_empenhado * 100), 2)
        if total_empenhado > 0
        else 0.0
    )

    vigente   = data_inicio <= hoje <= data_termino
    encerrado = hoje > data_termino
    a_iniciar = hoje < data_inicio
    saldo     = total_empenhado - total_gasto

    return IndicadoresContrato(
        dias_totais=dias_totais,
        dias_decorridos=dias_decorridos,
        dias_restantes=dias_restantes,
        pct_tempo=pct_tempo,
        pct_orcamento=pct_orcamento,
        vigente=vigente,
        encerrado=encerrado,
        a_iniciar=a_iniciar,
        saldo_orcamento=saldo,
    )
