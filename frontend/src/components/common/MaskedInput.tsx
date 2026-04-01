/**
 * components/common/MaskedInput.tsx — Inputs com máscara para CPF e CNPJ.
 *
 * Componentes controlados que aplicam máscaras automaticamente
 * enquanto o usuário digita, facilitando o preenchimento correto.
 *
 * Uso:
 *   <CPFInput value={cpf} onChange={setCpf} />
 *   <CNPJInput value={cnpj} onChange={setCnpj} />
 *
 * Compatíveis com react-hook-form via ref forwarding.
 */

import React, { forwardRef, useCallback } from 'react'
import { mascaraCNPJ, mascaraCPF } from '@/utils'
import { clsx } from 'clsx'

interface MaskedInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  mascara: (value: string) => string
}

/**
 * Input genérico com máscara aplicada ao digitar.
 * Encaminha a ref para compatibilidade com react-hook-form.
 */
const MaskedInput = forwardRef<HTMLInputElement, MaskedInputProps>(
  ({ error, mascara, onChange, className, ...props }, ref) => {
    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const mascarado = mascara(e.target.value)
        // Cria evento sintético com valor mascarado
        const syntheticEvent = {
          ...e,
          target: { ...e.target, value: mascarado },
        } as React.ChangeEvent<HTMLInputElement>
        onChange?.(syntheticEvent)
      },
      [mascara, onChange],
    )

    return (
      <input
        ref={ref}
        className={clsx('input', error && 'input-error', className)}
        onChange={handleChange}
        {...props}
      />
    )
  },
)

MaskedInput.displayName = 'MaskedInput'

// ── CPFInput ──────────────────────────────────────────────────────────────────

interface CPFInputProps extends Omit<MaskedInputProps, 'mascara'> {}

/**
 * Input para CPF com máscara automática: 000.000.000-00
 */
export const CPFInput = forwardRef<HTMLInputElement, CPFInputProps>(
  (props, ref) => (
    <MaskedInput
      ref={ref}
      mascara={mascaraCPF}
      placeholder="000.000.000-00"
      maxLength={14}
      inputMode="numeric"
      autoComplete="off"
      {...props}
    />
  ),
)

CPFInput.displayName = 'CPFInput'

// ── CNPJInput ─────────────────────────────────────────────────────────────────

interface CNPJInputProps extends Omit<MaskedInputProps, 'mascara'> {}

/**
 * Input para CNPJ com máscara automática: 00.000.000/0001-00
 */
export const CNPJInput = forwardRef<HTMLInputElement, CNPJInputProps>(
  (props, ref) => (
    <MaskedInput
      ref={ref}
      mascara={mascaraCNPJ}
      placeholder="00.000.000/0001-00"
      maxLength={18}
      inputMode="numeric"
      autoComplete="off"
      {...props}
    />
  ),
)

CNPJInput.displayName = 'CNPJInput'

// ── ProgressRing ──────────────────────────────────────────────────────────────

interface ProgressRingProps {
  percent: number
  size?: number
  strokeWidth?: number
  label?: string
  color?: string
}

/**
 * Indicador circular de progresso (SVG).
 * Usado nos cards de KPI do dashboard e relatórios.
 */
export function ProgressRing({
  percent,
  size = 64,
  strokeWidth = 6,
  label,
  color,
}: ProgressRingProps) {
  const pct = Math.min(100, Math.max(0, percent))
  const r = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * r
  const offset = circumference - (pct / 100) * circumference

  const ringColor =
    color ?? (pct >= 90 ? '#ef4444' : pct >= 70 ? '#f59e0b' : '#10b981')

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={ringColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      <span className="absolute text-xs font-bold text-gray-700">
        {label ?? `${Math.round(pct)}%`}
      </span>
    </div>
  )
}
