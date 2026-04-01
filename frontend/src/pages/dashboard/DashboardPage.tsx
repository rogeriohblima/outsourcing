/**
 * pages/dashboard/DashboardPage.tsx — Dashboard com resumo geral do sistema.
 *
 * Exibe cartões de resumo: contratos ativos, impressoras ativas,
 * leituras do mês corrente, e lista de contratos em vigência com
 * barra de progresso de tempo e orçamento.
 */

import { useQuery } from '@tanstack/react-query'
import { BarChart2, Building2, ClipboardList, Printer, Zap } from 'lucide-react'
import { contratosApi, impressorasApi, leiturasApi } from '@/api/endpoints'
import { PageHeader, PageSpinner, formatCurrency, formatDate } from '@/components/common'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  color: string
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  )
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  const pct = Math.min(100, Math.max(0, value))
  return (
    <div className="w-full bg-gray-100 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

export default function DashboardPage() {
  const now = new Date()
  const mes = now.getMonth() + 1
  const ano = now.getFullYear()

  const { data: contratos, isLoading: loadingContratos } = useQuery({
    queryKey: ['contratos'],
    queryFn: contratosApi.list,
  })

  const { data: impressoras, isLoading: loadingImp } = useQuery({
    queryKey: ['impressoras', { ativa: true }],
    queryFn: () => impressorasApi.list({ ativa: true }),
  })

  const { data: leiturasMes, isLoading: loadingLeituras } = useQuery({
    queryKey: ['leituras', mes, ano],
    queryFn: () => leiturasApi.list({ mes_referencia: mes, ano_referencia: ano }),
  })

  const isLoading = loadingContratos || loadingImp || loadingLeituras

  if (isLoading) return <PageSpinner />

  const hoje = new Date()
  const contratosAtivos = (contratos ?? []).filter(
    (c) => new Date(c.data_termino) >= hoje && new Date(c.data_inicio) <= hoje
  )

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={`${format(hoje, "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })}`}
      />

      {/* Cartões de resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={ClipboardList}
          label="Contratos Ativos"
          value={contratosAtivos.length}
          color="bg-fab-600"
        />
        <StatCard
          icon={Printer}
          label="Impressoras Ativas"
          value={impressoras?.length ?? 0}
          color="bg-emerald-500"
        />
        <StatCard
          icon={Zap}
          label={`Leituras ${format(hoje, 'MMM/yyyy', { locale: ptBR })}`}
          value={leiturasMes?.length ?? 0}
          color="bg-amber-500"
        />
        <StatCard
          icon={Building2}
          label="Total de Contratos"
          value={contratos?.length ?? 0}
          color="bg-violet-500"
        />
      </div>

      {/* Contratos em vigência */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-base font-semibold text-gray-700 flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-fab-600" />
            Contratos em Vigência
          </h2>
          <span className="badge-blue">{contratosAtivos.length} ativo(s)</span>
        </div>

        {contratosAtivos.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">
            Nenhum contrato em vigência no momento.
          </p>
        ) : (
          <div className="space-y-5">
            {contratosAtivos.map((c) => {
              const inicio = new Date(c.data_inicio)
              const termino = new Date(c.data_termino)
              const diasTotais = Math.max(1, (termino.getTime() - inicio.getTime()) / 86400000)
              const diasDecorridos = Math.max(0, (hoje.getTime() - inicio.getTime()) / 86400000)
              const pctTempo = Math.min(100, (diasDecorridos / diasTotais) * 100)

              return (
                <div key={c.id} className="border border-gray-100 rounded-xl p-4 hover:border-fab-200 transition-colors">
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div>
                      <p className="font-semibold text-gray-800 text-sm">{c.numero}</p>
                      <p className="text-xs text-gray-500">{c.empresa.nome}</p>
                    </div>
                    <span className="badge-green text-xs whitespace-nowrap">Vigente</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs text-gray-500 mb-3">
                    <div>
                      <span className="font-medium text-gray-600">Início:</span>{' '}
                      {formatDate(c.data_inicio)}
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Término:</span>{' '}
                      {formatDate(c.data_termino)}
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Tempo decorrido</span>
                      <span className="font-medium">{pctTempo.toFixed(1)}%</span>
                    </div>
                    <ProgressBar
                      value={pctTempo}
                      color={pctTempo > 90 ? 'bg-red-400' : pctTempo > 70 ? 'bg-amber-400' : 'bg-fab-500'}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
