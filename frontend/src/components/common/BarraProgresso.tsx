/**
 * components/common/BarraProgresso.tsx — Componente de barra de progresso reutilizável.
 *
 * Suporta variantes de cor automáticas baseadas no valor percentual:
 *   - Verde   : 0–69%
 *   - Amarelo : 70–89%
 *   - Vermelho: 90–100%+
 *
 * Uso:
 *   <BarraProgresso valor={75} label="Orçamento consumido" />
 *   <BarraProgresso valor={45} label="Tempo decorrido" cor="azul" />
 */

import { clsx } from 'clsx'

type CorVariante = 'auto' | 'azul' | 'verde' | 'amarelo' | 'vermelho' | 'cinza'

interface BarraProgressoProps {
  /** Valor percentual de 0 a 100 (valores acima de 100 são exibidos em vermelho). */
  valor: number
  /** Label exibida acima da barra à esquerda. */
  label?: string
  /** Label exibida acima da barra à direita (padrão: percentual). */
  labelDireita?: string
  /** Variante de cor. 'auto' usa cor baseada no valor. */
  cor?: CorVariante
  /** Altura da barra em pixels. */
  altura?: number
  /** Exibe o valor percentual no label direito. */
  mostrarPorcentagem?: boolean
  className?: string
}

const coresClasses: Record<CorVariante, string> = {
  auto:     '',   // definido dinamicamente
  azul:     'bg-fab-500',
  verde:    'bg-emerald-500',
  amarelo:  'bg-amber-400',
  vermelho: 'bg-red-500',
  cinza:    'bg-gray-400',
}

function corAutomatica(valor: number): string {
  if (valor >= 90) return 'bg-red-500'
  if (valor >= 70) return 'bg-amber-400'
  return 'bg-emerald-500'
}

export function BarraProgresso({
  valor,
  label,
  labelDireita,
  cor = 'auto',
  altura = 8,
  mostrarPorcentagem = true,
  className,
}: BarraProgressoProps) {
  const pct = Math.min(100, Math.max(0, valor))
  const corClasse = cor === 'auto' ? corAutomatica(valor) : coresClasses[cor]
  const textoDir = labelDireita ?? (mostrarPorcentagem ? `${valor.toFixed(1)}%` : undefined)

  return (
    <div className={clsx('w-full', className)}>
      {(label || textoDir) && (
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1.5">
          {label && <span>{label}</span>}
          {textoDir && (
            <span className={clsx(
              'font-semibold',
              valor >= 90 ? 'text-red-600' : valor >= 70 ? 'text-amber-600' : 'text-gray-700'
            )}>
              {textoDir}
            </span>
          )}
        </div>
      )}
      <div
        className="w-full bg-gray-100 rounded-full overflow-hidden"
        style={{ height: `${altura}px` }}
        role="progressbar"
        aria-valuenow={valor}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={clsx('h-full rounded-full transition-all duration-500', corClasse)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ── KpiCard ─────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string
  valor: string | number
  subLabel?: string
  icone?: React.ReactNode
  cor?: string
  tendencia?: 'alta' | 'baixa' | 'neutro'
}

/**
 * Cartão de indicador-chave de performance (KPI) para o dashboard e relatórios.
 */
export function KpiCard({ label, valor, subLabel, icone, cor = 'bg-fab-600' }: KpiCardProps) {
  return (
    <div className="card flex items-start gap-4">
      {icone && (
        <div className={clsx('p-3 rounded-xl text-white flex-shrink-0', cor)}>
          {icone}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-sm text-gray-500 truncate">{label}</p>
        <p className="text-2xl font-bold text-gray-800 mt-0.5">{valor}</p>
        {subLabel && <p className="text-xs text-gray-400 mt-0.5 truncate">{subLabel}</p>}
      </div>
    </div>
  )
}
