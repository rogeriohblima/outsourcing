"""
tests/test_relatorio_service.py — Testes unitários da lógica de negócio.

Testa as funções puras de relatorio_service.py sem banco de dados ou HTTP.

Nova lógica de franquia:
  - calcular_paginas_periodo: inalterada
  - calcular_valor_impressao: mantida para compatibilidade (modelo mensal antigo)
  - _calcular_valor_periodo: nova lógica (franquia total do contrato)
    testada indiretamente via test_relatorios.py
  - calcular_indicadores_contrato: inalterada
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.relatorio_service import (
    BreakdownImpressao,
    IndicadoresContrato,
    calcular_indicadores_contrato,
    calcular_paginas_periodo,
    calcular_valor_impressao,
)


# ── calcular_paginas_periodo ──────────────────────────────────────────────────

class TestCalcularPaginasPeriodo:
    """Calcula páginas entre dois contadores consecutivos."""

    def test_diferenca_positiva_normal(self):
        assert calcular_paginas_periodo(11500, 6000) == 5500

    def test_primeira_leitura_contador_zero(self):
        assert calcular_paginas_periodo(5000, 0) == 5000

    def test_contador_identico_retorna_zero(self):
        assert calcular_paginas_periodo(1000, 1000) == 0

    def test_contador_regressivo_retorna_zero(self):
        """Troca de impressora ou erro de lançamento: nunca retorna negativo."""
        assert calcular_paginas_periodo(500, 1000) == 0

    def test_ambos_zero(self):
        assert calcular_paginas_periodo(0, 0) == 0

    def test_grandes_volumes(self):
        assert calcular_paginas_periodo(10_000_000, 9_500_000) == 500_000


# ── calcular_valor_impressao (lógica de franquia mensal — mantida) ────────────

class TestCalcularValorImpressao:
    """
    Testa o modelo financeiro de franquia mensal + excedente.

    Nota: este é o modelo ANTIGO (franquia por mês).
    O novo modelo usa franquia total do contrato e é testado
    via endpoints em TestRelatorioMensal.
    """

    def test_dentro_da_franquia_paga_apenas_custo_fixo(self):
        """3.000 pág com franquia 5.000 → só custo fixo R$500."""
        r = calcular_valor_impressao(3000, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.excedente == 0
        assert r.valor_excedente == Decimal("0.00")
        assert r.valor_total == Decimal("500.00")
        assert r.dentro_franquia == 3000

    def test_exatamente_na_franquia(self):
        """Exatamente na franquia: sem excedente."""
        r = calcular_valor_impressao(5000, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.excedente == 0
        assert r.valor_total == Decimal("500.00")

    def test_excede_franquia(self):
        """6.000 pág, franquia 5.000 → 1.000 excedentes × R$0,05 = R$50."""
        r = calcular_valor_impressao(6000, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.excedente == 1000
        assert r.valor_excedente == Decimal("50.00")
        assert r.valor_total == Decimal("550.00")
        assert r.dentro_franquia == 5000

    def test_franquia_zero_cobra_tudo_por_pagina(self):
        """Franquia zero: todas as páginas são excedentes."""
        r = calcular_valor_impressao(200, 0, Decimal("0.00"), Decimal("0.10"))
        assert r.dentro_franquia == 0
        assert r.excedente == 200
        assert r.valor_total == Decimal("20.00")

    def test_zero_paginas_paga_custo_fixo(self):
        """Zero páginas: paga apenas o custo fixo da franquia."""
        r = calcular_valor_impressao(0, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.paginas == 0
        assert r.valor_total == Decimal("500.00")

    def test_percentual_franquia_usada(self):
        """2.500 de 5.000 = 50% da franquia usada."""
        r = calcular_valor_impressao(2500, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.pct_franquia_usada == pytest.approx(50.0)

    def test_franquia_zero_nao_divide_por_zero(self):
        """Franquia zero não deve causar ZeroDivisionError."""
        r = calcular_valor_impressao(100, 0, Decimal("0.00"), Decimal("0.10"))
        assert r.pct_franquia_usada == 0.0

    def test_grandes_volumes(self):
        """Funciona com contadores de alto volume."""
        r = calcular_valor_impressao(
            10_000_000, 5_000_000, Decimal("5000.00"), Decimal("0.02")
        )
        assert r.excedente == 5_000_000
        assert r.valor_total == Decimal("5000.00") + Decimal("100000.00")

    def test_retorna_breakdownimpressao(self):
        """Deve retornar instância de BreakdownImpressao."""
        r = calcular_valor_impressao(100, 500, Decimal("50.00"), Decimal("0.01"))
        assert isinstance(r, BreakdownImpressao)


# ── calcular_indicadores_contrato ─────────────────────────────────────────────

class TestCalcularIndicadoresContrato:
    """Testa os indicadores de tempo e orçamento do contrato."""

    def test_contrato_vigente_meio_prazo(self):
        """Contrato de 365 dias, referência no dia 182 → ~50% do tempo."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("10000.00"), Decimal("5000.00"),
            data_referencia=date(2025, 7, 2),
        )
        assert ind.vigente is True
        assert ind.encerrado is False
        assert ind.a_iniciar is False
        assert 45 <= ind.pct_tempo <= 55

    def test_contrato_encerrado(self):
        """Referência após término: encerrado=True, pct_tempo=100%."""
        ind = calcular_indicadores_contrato(
            date(2024, 1, 1), date(2024, 6, 30),
            Decimal("10000.00"), Decimal("0.00"),
            data_referencia=date(2025, 1, 1),
        )
        assert ind.encerrado is True
        assert ind.vigente is False
        assert ind.pct_tempo == 100.0
        assert ind.dias_restantes == 0

    def test_contrato_nao_iniciado(self):
        """Referência antes do início: a_iniciar=True, dias_decorridos=0."""
        ind = calcular_indicadores_contrato(
            date(2026, 1, 1), date(2026, 12, 31),
            Decimal("10000.00"), Decimal("0.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert ind.a_iniciar is True
        assert ind.vigente is False
        assert ind.encerrado is False
        assert ind.dias_decorridos == 0

    def test_percentual_orcamento_parcial(self):
        """R$3.000 de R$10.000 → exatamente 30%."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("10000.00"), Decimal("3000.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert ind.pct_orcamento == pytest.approx(30.0, rel=1e-2)
        assert ind.saldo_orcamento == Decimal("7000.00")

    def test_sem_empenho_nao_divide_por_zero(self):
        """Total empenhado zero: percentual de orçamento deve ser 0."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("0.00"), Decimal("0.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert ind.pct_orcamento == 0.0

    def test_saldo_negativo_quando_excede(self):
        """Gasto > empenhado → saldo negativo e pct > 100%."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("5000.00"), Decimal("6000.00"),
            data_referencia=date(2025, 10, 1),
        )
        assert ind.saldo_orcamento < Decimal("0")
        assert ind.pct_orcamento > 100.0

    def test_dias_restantes_zero_apos_termino(self):
        """Após o término, dias_restantes deve ser 0."""
        ind = calcular_indicadores_contrato(
            date(2024, 1, 1), date(2024, 12, 31),
            Decimal("1000.00"), Decimal("500.00"),
            data_referencia=date(2025, 3, 1),
        )
        assert ind.dias_restantes == 0

    def test_retorna_indicadores_contrato(self):
        """Deve retornar instância de IndicadoresContrato."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("1000.00"), Decimal("0.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert isinstance(ind, IndicadoresContrato)

    def test_dias_totais_positivo(self):
        """dias_totais deve sempre ser >= 1 para evitar divisão por zero."""
        ind = calcular_indicadores_contrato(
            date(2025, 6, 1), date(2025, 6, 1),  # mesmo dia
            Decimal("1000.00"), Decimal("0.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert ind.dias_totais >= 1
        assert 0 <= ind.pct_tempo <= 100
