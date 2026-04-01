"""
tests/test_relatorio_service.py — Testes unitários da lógica de negócio
dos relatórios (sem banco de dados ou HTTP).

Cobre:
  - calcular_paginas_periodo: diferença entre contadores
  - calcular_valor_impressao: modelo de franquia + excedente
  - calcular_indicadores_contrato: percentuais de tempo e orçamento
  - Casos extremos: franquia zero, contador regressivo, orçamento esgotado
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.relatorio_service import (
    calcular_indicadores_contrato,
    calcular_paginas_periodo,
    calcular_valor_impressao,
)


# ── calcular_paginas_periodo ──────────────────────────────────────────────────

class TestCalcularPaginasPeriodo:
    """Testa o cálculo de páginas entre duas leituras de contador."""

    def test_diferenca_positiva_normal(self):
        """Diferença positiva normal: 11500 - 6000 = 5500."""
        assert calcular_paginas_periodo(11500, 6000) == 5500

    def test_primeira_leitura_sem_anterior(self):
        """Primeira leitura (sem leitura anterior): usa 0 como base."""
        assert calcular_paginas_periodo(5000, 0) == 5000

    def test_contador_identico_retorna_zero(self):
        """Se o contador não mudou, deve retornar 0 páginas."""
        assert calcular_paginas_periodo(1000, 1000) == 0

    def test_contador_regressivo_retorna_zero(self):
        """
        Se o contador atual for menor que o anterior (erro de lançamento
        ou troca de impressora), deve retornar 0, nunca negativo.
        """
        assert calcular_paginas_periodo(500, 1000) == 0

    def test_contador_zero_retorna_zero(self):
        """Ambos os contadores zero → zero páginas."""
        assert calcular_paginas_periodo(0, 0) == 0


# ── calcular_valor_impressao ──────────────────────────────────────────────────

class TestCalcularValorImpressao:
    """Testa o modelo financeiro de franquia + excedente."""

    def test_dentro_da_franquia_paga_apenas_franquia(self):
        """
        3000 páginas com franquia de 5000:
        → pagamento = apenas o valor_franquia (R$ 500).
        """
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
        """
        6000 páginas com franquia 5000:
        → excedente = 1000 págs × R$ 0,05 = R$ 50,00
        → total = R$ 500 + R$ 50 = R$ 550,00
        """
        r = calcular_valor_impressao(6000, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.excedente == 1000
        assert r.valor_excedente == Decimal("50.00")
        assert r.valor_total == Decimal("550.00")
        assert r.dentro_franquia == 5000

    def test_franquia_zero(self):
        """
        Franquia zero: todas as páginas são excedentes.
        Modelo de cobrança 100% por página.
        """
        r = calcular_valor_impressao(200, 0, Decimal("0.00"), Decimal("0.10"))
        assert r.dentro_franquia == 0
        assert r.excedente == 200
        assert r.valor_total == Decimal("20.00")

    def test_zero_paginas(self):
        """Zero páginas: paga apenas o custo fixo da franquia."""
        r = calcular_valor_impressao(0, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.paginas == 0
        assert r.valor_total == Decimal("500.00")

    def test_pct_franquia_usada(self):
        """Percentual da franquia usada deve ser calculado corretamente."""
        r = calcular_valor_impressao(2500, 5000, Decimal("500.00"), Decimal("0.05"))
        assert r.pct_franquia_usada == pytest.approx(50.0)

    def test_pct_franquia_zerada_sem_divisao_por_zero(self):
        """Franquia zero não deve causar ZeroDivisionError."""
        r = calcular_valor_impressao(100, 0, Decimal("0.00"), Decimal("0.10"))
        assert r.pct_franquia_usada == 0.0

    def test_grandes_volumes(self):
        """Deve funcionar com contadores de alto volume (10 milhões de páginas)."""
        r = calcular_valor_impressao(
            10_000_000, 5_000_000,
            Decimal("5000.00"), Decimal("0.02")
        )
        assert r.excedente == 5_000_000
        assert r.valor_total == Decimal("5000.00") + Decimal("100000.00")


# ── calcular_indicadores_contrato ─────────────────────────────────────────────

class TestCalcularIndicadoresContrato:
    """Testa o cálculo dos indicadores de tempo e orçamento do contrato."""

    def test_contrato_vigente_meio_ano(self):
        """
        Contrato de 365 dias, referência no dia 182:
        → ~50% do tempo decorrido.
        """
        inicio  = date(2025, 1, 1)
        termino = date(2025, 12, 31)
        ref     = date(2025, 7, 2)  # ~182 dias

        ind = calcular_indicadores_contrato(
            inicio, termino,
            Decimal("10000.00"), Decimal("5000.00"),
            data_referencia=ref,
        )

        assert ind.vigente is True
        assert ind.encerrado is False
        assert 45 <= ind.pct_tempo <= 55  # aproximadamente 50%

    def test_contrato_encerrado(self):
        """Referência após o término: encerrado=True, pct_tempo=100%."""
        inicio  = date(2024, 1, 1)
        termino = date(2024, 6, 30)
        ref     = date(2025, 1, 1)  # depois do término

        ind = calcular_indicadores_contrato(
            inicio, termino,
            Decimal("10000.00"), Decimal("0.00"),
            data_referencia=ref,
        )

        assert ind.encerrado is True
        assert ind.vigente is False
        assert ind.pct_tempo == 100.0

    def test_contrato_nao_iniciado(self):
        """Referência antes do início: a_iniciar=True, vigente=False, 0% do tempo."""
        inicio  = date(2026, 1, 1)
        termino = date(2026, 12, 31)
        ref     = date(2025, 6, 1)  # antes do início

        ind = calcular_indicadores_contrato(
            inicio, termino,
            Decimal("10000.00"), Decimal("0.00"),
            data_referencia=ref,
        )

        assert ind.a_iniciar is True
        assert ind.vigente is False
        assert ind.encerrado is False
        assert ind.dias_decorridos == 0

    def test_orcamento_consumido_parcialmente(self):
        """R$ 3.000 de R$ 10.000 → 30% do orçamento."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("10000.00"), Decimal("3000.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert ind.pct_orcamento == pytest.approx(30.0, rel=1e-2)
        assert ind.saldo_orcamento == Decimal("7000.00")

    def test_orcamento_sem_empenho(self):
        """Sem empenho: percentual deve ser 0, sem ZeroDivisionError."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("0.00"), Decimal("0.00"),
            data_referencia=date(2025, 6, 1),
        )
        assert ind.pct_orcamento == 0.0

    def test_saldo_negativo_possivel(self):
        """Gasto maior que empenhado → saldo negativo (sinaliza problema)."""
        ind = calcular_indicadores_contrato(
            date(2025, 1, 1), date(2025, 12, 31),
            Decimal("5000.00"), Decimal("6000.00"),
            data_referencia=date(2025, 10, 1),
        )
        assert ind.saldo_orcamento < Decimal("0")
        assert ind.pct_orcamento > 100.0

    def test_dias_restantes_zerado_apos_termino(self):
        """Após o término do contrato, dias_restantes deve ser 0."""
        ind = calcular_indicadores_contrato(
            date(2024, 1, 1), date(2024, 12, 31),
            Decimal("1000.00"), Decimal("500.00"),
            data_referencia=date(2025, 3, 1),
        )
        assert ind.dias_restantes == 0
