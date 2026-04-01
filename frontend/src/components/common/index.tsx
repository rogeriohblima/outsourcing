/**
 * components/common/index.tsx — Componentes UI reutilizáveis.
 *
 * Exporta: Modal, ConfirmDialog, Spinner, PageHeader, EmptyState,
 *          FormField, DataTable, Pagination, AlertMessage
 */

import React, { Fragment } from 'react'
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react'
import { clsx } from 'clsx'

// ── Spinner ───────────────────────────────────────────────────────────────────

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={clsx(
        'animate-spin rounded-full border-2 border-current border-t-transparent',
        className ?? 'h-5 w-5'
      )}
    />
  )
}

export function PageSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <Spinner className="h-8 w-8 text-fab-600" />
    </div>
  )
}

// ── PageHeader ────────────────────────────────────────────────────────────────

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 ml-4">{actions}</div>}
    </div>
  )
}

// ── EmptyState ────────────────────────────────────────────────────────────────

interface EmptyStateProps {
  message?: string
  action?: React.ReactNode
}

export function EmptyState({ message = 'Nenhum registro encontrado.', action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <Info className="w-8 h-8 text-gray-400" />
      </div>
      <p className="text-gray-500 text-sm">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

// ── AlertMessage ──────────────────────────────────────────────────────────────

type AlertType = 'error' | 'success' | 'warning' | 'info'

interface AlertMessageProps {
  type: AlertType
  message: string
  onClose?: () => void
}

const alertConfig: Record<AlertType, { icon: React.ComponentType<{ className?: string }>; classes: string }> = {
  error:   { icon: AlertCircle,   classes: 'bg-red-50 border-red-200 text-red-800' },
  success: { icon: CheckCircle,   classes: 'bg-green-50 border-green-200 text-green-800' },
  warning: { icon: AlertTriangle, classes: 'bg-yellow-50 border-yellow-200 text-yellow-800' },
  info:    { icon: Info,          classes: 'bg-blue-50 border-blue-200 text-blue-700' },
}

export function AlertMessage({ type, message, onClose }: AlertMessageProps) {
  const { icon: Icon, classes } = alertConfig[type]
  return (
    <div className={clsx('flex items-start gap-3 p-3 rounded-lg border text-sm', classes)}>
      <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" />
      <p className="flex-1">{message}</p>
      {onClose && (
        <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

// ── Modal ─────────────────────────────────────────────────────────────────────

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const modalSizes = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-lg', xl: 'max-w-2xl' }

export function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  if (!isOpen) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className={clsx('relative bg-white rounded-xl shadow-xl w-full', modalSizes[size])}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-base font-semibold text-gray-800">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  )
}

// ── ConfirmDialog ─────────────────────────────────────────────────────────────

interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  message: string
  confirmLabel?: string
  isLoading?: boolean
}

export function ConfirmDialog({
  isOpen, onClose, onConfirm,
  title = 'Confirmar exclusão',
  message,
  confirmLabel = 'Excluir',
  isLoading,
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <p className="text-sm text-gray-600 mb-5">{message}</p>
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="btn-secondary btn-sm">
          Cancelar
        </button>
        <button onClick={onConfirm} disabled={isLoading} className="btn-danger btn-sm">
          {isLoading ? <Spinner className="h-4 w-4" /> : confirmLabel}
        </button>
      </div>
    </Modal>
  )
}

// ── FormField ─────────────────────────────────────────────────────────────────

interface FormFieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
}

export function FormField({ label, error, required, children }: FormFieldProps) {
  return (
    <div>
      <label className="label">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
      {error && <p className="field-error">{error}</p>}
    </div>
  )
}

// ── StatusBadge ───────────────────────────────────────────────────────────────

export function StatusBadge({ ativo }: { ativo: boolean }) {
  return ativo
    ? <span className="badge-green">Ativa</span>
    : <span className="badge-red">Inativa</span>
}

// ── Formatters ─────────────────────────────────────────────────────────────────

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('pt-BR')
}

export function formatDateTime(dateStr: string): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('pt-BR')
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}
