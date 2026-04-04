/**
 * pages/relatorios/RelatoriosPage.tsx — Relatórios mensais, totais e gráficos.
 *
 * Seções:
 *  1. Seletor de contrato + período
 *  2. Cards de indicadores: páginas, valor, %orçamento, %tempo
 *  3. Gráfico de evolução mensal (Recharts BarChart)
 *  4. Tabela de consumo por tipo de impressão
 *  5. Ranking de impressoras
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts'
import { BarChart2, FileText, Printer, TrendingUp } from 'lucide-react'
import { contratosApi, relatoriosApi } from '@/api/endpoints'
import {
  EmptyState, PageHeader, PageSpinner, formatCurrency, formatDate, formatPercent,
} from '@/components/common'

// ── Card de Indicador ─────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className={`rounded-xl p-4 text-white ${color}`}>
      <p className="text-sm opacity-80">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

// ── Barra de progresso ────────────────────────────────────────────────────────

function ProgressBar({ value, label }: { value: number; label: string }) {
  const pct = Math.min(100, Math.max(0, value))
  const color = pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-amber-400' : 'bg-emerald-500'
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{label}</span>
        <span className="font-semibold">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// ── Página Principal ──────────────────────────────────────────────────────────

const MESES = ['','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

export default function RelatoriosPage() {
  const now = new Date()
  const [contratoId, setContratoId] = useState<number | null>(null)
  const [mes, setMes] = useState(now.getMonth() + 1)
  const [ano, setAno] = useState(now.getFullYear())
  const [aba, setAba] = useState<'mensal' | 'total' | 'evolucao' | 'ranking'>('mensal')

  const { data: contratos } = useQuery({ queryKey: ['contratos'], queryFn: contratosApi.list })

  const { data: relMensal, isLoading: loadMensal } = useQuery({
    queryKey: ['relatorio-mensal', contratoId, mes, ano],
    queryFn: () => relatoriosApi.mensal(contratoId!, mes, ano),
    enabled: !!contratoId && aba === 'mensal',
  })
  const { data: relTotal, isLoading: loadTotal } = useQuery({
    queryKey: ['relatorio-total', contratoId],
    queryFn: () => relatoriosApi.total(contratoId!),
    enabled: !!contratoId && aba === 'total',
  })
  const { data: evolucao, isLoading: loadEvolucao } = useQuery({
    queryKey: ['evolucao', contratoId],
    queryFn: () => relatoriosApi.evolucao(contratoId!),
    enabled: !!contratoId && aba === 'evolucao',
  })
  const { data: ranking, isLoading: loadRanking } = useQuery({
    queryKey: ['ranking', contratoId],
    queryFn: () => relatoriosApi.ranking(contratoId!),
    enabled: !!contratoId && aba === 'ranking',
  })

  const isLoading = loadMensal || loadTotal || loadEvolucao || loadRanking

  const ABAS = [
    { key: 'mensal',   label: 'Mensal',    icon: FileText },
    { key: 'total',    label: 'Total',     icon: BarChart2 },
    { key: 'evolucao', label: 'Evolução',  icon: TrendingUp },
    { key: 'ranking',  label: 'Ranking',   icon: Printer },
  ] as const

  return (
    <div>
      <PageHeader title="Relatórios" subtitle="Consumo, valores e indicadores de desempenho do contrato" />

      {/* Seletor de contrato e período */}
      <div className="card mb-6 flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-48">
          <label className="label">Contrato</label>
          <select className="input" value={contratoId ?? ''} onChange={(e) => setContratoId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">Selecione um contrato…</option>
            {contratos?.map((c) => (
              <option key={c.id} value={c.id}>{c.numero} — {c.empresa.nome}</option>
            ))}
          </select>
        </div>
        {aba === 'mensal' && (
          <>
            <div>
              <label className="label">Mês</label>
              <select className="input w-28" value={mes} onChange={(e) => setMes(Number(e.target.value))}>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>{MESES[m]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Ano</label>
              <input type="number" className="input w-24" value={ano}
                onChange={(e) => setAno(Number(e.target.value))} min={2000} max={2100} />
            </div>
          </>
        )}
      </div>

      {!contratoId ? (
        <EmptyState message="Selecione um contrato acima para visualizar os relatórios." />
      ) : (
        <>
          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
            {ABAS.map(({ key, label, icon: Icon }) => (
              <button key={key} onClick={() => setAba(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${aba === key ? 'bg-white shadow text-fab-700' : 'text-gray-500 hover:text-gray-700'}`}>
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>

          {isLoading && <PageSpinner />}

          {/* ── ABA: Mensal ── */}
          {aba === 'mensal' && relMensal && !loadMensal && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <KpiCard label="Total de Páginas" value={relMensal.total_paginas.toLocaleString('pt-BR')}
                  sub={`${MESES[relMensal.mes]}/${relMensal.ano}`} color="bg-fab-600" />
                <KpiCard label="Valor Total" value={formatCurrency(relMensal.total_valor)}
                  sub="Franquia + Excedente" color="bg-emerald-600" />
                <KpiCard label="% Orçamento" value={formatPercent(relMensal.percentual_orcamento ?? 0)}
                  sub="Consumido do total empenhado" color={
                    (relMensal.percentual_orcamento ?? 0) > 90 ? 'bg-red-600' : 'bg-amber-500'} />
                <KpiCard label="% Tempo" value={formatPercent(relMensal.percentual_tempo ?? 0)}
                  sub="Do prazo do contrato" color="bg-violet-600" />
              </div>

              <div className="card">
                <h3 className="font-semibold text-gray-700 mb-4">Consumo por Impressora — {MESES[mes]}/{ano}</h3>
                {relMensal.itens.length === 0
                  ? <EmptyState message="Sem leituras para este período." />
                  : (
                    <div className="table-wrapper">
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Impressora</th><th>Setor</th><th>Tipo</th>
                            <th className="text-right">Páginas</th>
                            <th className="text-right">Dentro Franquia</th>
                            <th className="text-right">Fora Franquia</th>
                            <th className="text-right">Fixo</th>
                            <th className="text-right">Variável</th>
                            <th className="text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {relMensal.itens.map((item, idx) => (
                            <tr key={idx}>
                              <td className="font-medium text-sm">{item.impressora_nome}</td>
                              <td>{item.setor}</td>
                              <td className="text-xs">{item.tipo_impressao}</td>
                              <td className="text-right font-mono">{item.paginas_impressas.toLocaleString('pt-BR')}</td>
                              <td className="text-right font-mono text-emerald-600">{item.paginas_dentro_franquia.toLocaleString('pt-BR')}</td>
                              <td className="text-right font-mono text-amber-600">{item.paginas_fora_franquia.toLocaleString('pt-BR')}</td>
                              <td className="text-right font-mono text-gray-600">{formatCurrency(item.valor_mensal_franquia)}</td>
                              <td className="text-right font-mono">{formatCurrency(Number(item.valor_dentro_franquia) + Number(item.valor_fora_franquia))}</td>
                              <td className="text-right font-semibold text-fab-700">{formatCurrency(item.valor_total)}</td>
                            </tr>
                          ))}
                          <tr className="bg-gray-50 font-semibold">
                            <td colSpan={3} className="text-right">TOTAL</td>
                            <td className="text-right font-mono">{relMensal.total_paginas.toLocaleString('pt-BR')}</td>
                            <td colSpan={2}></td>
                            <td className="text-right text-gray-600">{formatCurrency(relMensal.total_custo_fixo)}</td>
                            <td className="text-right">{formatCurrency(relMensal.total_variavel)}</td>
                            <td className="text-right text-fab-700">{formatCurrency(relMensal.total_valor)}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
              </div>
            </div>
          )}

          {/* ── ABA: Total ── */}
          {aba === 'total' && relTotal && !loadTotal && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="card space-y-4">
                  <h3 className="font-semibold text-gray-700">Indicadores Globais</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="text-gray-500">Contrato:</span> <span className="font-medium">{relTotal.contrato_numero}</span></div>
                    <div><span className="text-gray-500">Empresa:</span> <span className="font-medium">{relTotal.empresa_nome}</span></div>
                    <div><span className="text-gray-500">Início:</span> <span className="font-medium">{formatDate(relTotal.data_inicio)}</span></div>
                    <div><span className="text-gray-500">Término:</span> <span className="font-medium">{formatDate(relTotal.data_termino)}</span></div>
                    <div><span className="text-gray-500">Processo:</span> <span className="font-medium">{relTotal.numero_processo}</span></div>
                    <div><span className="text-gray-500">Impressoras:</span> <span className="font-medium">{relTotal.impressoras_ativas}</span></div>
                    <div><span className="text-gray-500">Meses com leitura:</span> <span className="font-medium">{relTotal.meses_com_leitura}</span></div>
                    <div><span className="text-gray-500">Dias decorridos:</span> <span className="font-medium">{relTotal.dias_decorridos}/{relTotal.dias_totais}</span></div>
                  </div>
                  <div className="space-y-3 mt-2">
                    <ProgressBar value={relTotal.percentual_orcamento_consumido} label="Orçamento consumido" />
                    <ProgressBar value={relTotal.percentual_tempo_decorrido} label="Tempo decorrido" />
                  </div>
                </div>
                <div className="card space-y-3">
                  <h3 className="font-semibold text-gray-700">Resumo Financeiro</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm"><span className="text-gray-500">Valor estimado:</span> <span className="font-semibold">{formatCurrency(relTotal.valor_estimado)}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-gray-500">Total empenhado:</span> <span className="font-semibold">{formatCurrency(relTotal.total_empenhado)}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-gray-500">Total consumido:</span> <span className="font-semibold text-fab-700">{formatCurrency(relTotal.total_geral_valor)}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-gray-500">Saldo disponível:</span> <span className={`font-semibold ${relTotal.total_empenhado - relTotal.total_geral_valor < 0 ? 'text-red-600' : 'text-emerald-600'}`}>{formatCurrency(relTotal.total_empenhado - relTotal.total_geral_valor)}</span></div>
                    <hr />
                    <div className="flex justify-between text-sm"><span className="text-gray-500">Total de páginas:</span> <span className="font-semibold">{relTotal.total_geral_paginas.toLocaleString('pt-BR')}</span></div>
                  </div>
                </div>
              </div>
              <div className="card">
                <h3 className="font-semibold text-gray-700 mb-4">Totais por Tipo de Impressão</h3>
                <div className="table-wrapper">
                  <table className="table">
                    <thead><tr><th>Tipo de Impressão</th><th className="text-right">Total Páginas</th><th className="text-right">Total Valor</th></tr></thead>
                    <tbody className="divide-y divide-gray-100">
                      {relTotal.itens.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.tipo_impressao}</td>
                          <td className="text-right font-mono">{item.total_paginas.toLocaleString('pt-BR')}</td>
                          <td className="text-right font-semibold text-fab-700">{formatCurrency(item.total_valor)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── ABA: Evolução ── */}
          {aba === 'evolucao' && evolucao && !loadEvolucao && (
            <div className="card">
              <h3 className="font-semibold text-gray-700 mb-6">Evolução Mensal de Consumo</h3>
              {evolucao.length === 0
                ? <EmptyState message="Sem dados de evolução disponíveis." />
                : (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={evolucao} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                      <YAxis yAxisId="left" tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString('pt-BR')} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }}
                        tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`} />
                      <Tooltip
                        formatter={(value: number, name: string) =>
                          name === 'total_paginas'
                            ? [value.toLocaleString('pt-BR') + ' pág.', 'Páginas']
                            : [formatCurrency(value), 'Valor']}
                      />
                      <Legend formatter={(v) => v === 'total_paginas' ? 'Páginas' : 'Valor (R$)'} />
                      <Bar yAxisId="left" dataKey="total_paginas" fill="#2c6ab8" radius={[4,4,0,0]} />
                      <Bar yAxisId="right" dataKey="total_valor" fill="#10b981" radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
            </div>
          )}

          {/* ── ABA: Ranking ── */}
          {aba === 'ranking' && ranking && !loadRanking && (
            <div className="card">
              <h3 className="font-semibold text-gray-700 mb-4">Ranking de Impressoras por Volume</h3>
              {ranking.length === 0
                ? <EmptyState message="Sem dados de ranking disponíveis." />
                : (
                  <div className="table-wrapper">
                    <table className="table">
                      <thead>
                        <tr><th>#</th><th>Impressora</th><th>Setor</th><th className="text-right">Total Páginas</th><th className="text-right">Total Valor</th></tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {ranking.map((r) => (
                          <tr key={r.num_serie}>
                            <td>
                              <span className={`badge ${r.posicao === 1 ? 'bg-yellow-100 text-yellow-700' : r.posicao === 2 ? 'bg-gray-100 text-gray-600' : r.posicao === 3 ? 'bg-orange-100 text-orange-600' : 'badge-gray'}`}>
                                #{r.posicao}
                              </span>
                            </td>
                            <td><div className="font-medium">{r.nome}</div><div className="text-xs text-gray-400 font-mono">{r.num_serie}</div></td>
                            <td>{r.setor}</td>
                            <td className="text-right font-mono font-semibold">{r.total_paginas.toLocaleString('pt-BR')}</td>
                            <td className="text-right font-semibold text-fab-700">{formatCurrency(r.total_valor)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
