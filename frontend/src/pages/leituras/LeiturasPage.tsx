/**
 * pages/leituras/LeiturasPage.tsx — Lançamento e listagem de leituras.
 *
 * Duas modalidades de registro:
 *  1. SNMP automático: dispara leitura no endpoint /leituras/snmp
 *  2. Manual: formulário completo com contador, data e observação
 *
 * Filtros: impressora, mês/ano de referência, origem (manual/automático).
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Zap, ClipboardEdit } from 'lucide-react'
import { impressorasApi, leiturasApi, tiposImpressaoApi } from '@/api/endpoints'
import {
  AlertMessage, ConfirmDialog, EmptyState, FormField,
  Modal, PageHeader, PageSpinner, Spinner, formatDate, formatDateTime,
} from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { LeituraOut } from '@/types'

// ── Schemas ───────────────────────────────────────────────────────────────────

const manualSchema = z.object({
  impressora_num_serie: z.string().min(1),
  tipo_impressao_id:   z.coerce.number().min(1),
  contador:            z.coerce.number().min(0),
  data:                z.string().min(1),
  mes_referencia:      z.coerce.number().min(1).max(12),
  ano_referencia:      z.coerce.number().min(2000).max(2100),
  observacao:          z.string().optional(),
})
const snmpSchema = z.object({
  impressora_num_serie: z.string().min(1),
  tipo_impressao_id:   z.coerce.number().min(1),
  mes_referencia:      z.coerce.number().min(1).max(12),
  ano_referencia:      z.coerce.number().min(2000).max(2100),
})
type ManualFormData = z.infer<typeof manualSchema>
type SNMPFormData   = z.infer<typeof snmpSchema>

// ── Seletor de impressora + tipo (compartilhado) ──────────────────────────────

function ImpressoraTipoFields({ register, errors }: { register: any; errors: any }) {
  const { data: impressoras } = useQuery({ queryKey: ['impressoras'], queryFn: () => impressorasApi.list({ ativa: true }) })
  const { data: tipos }       = useQuery({ queryKey: ['tipos-impressao'], queryFn: tiposImpressaoApi.list })
  return (
    <>
      <FormField label="Impressora" error={errors.impressora_num_serie?.message} required>
        <select {...register('impressora_num_serie')} className={`input ${errors.impressora_num_serie ? 'input-error' : ''}`}>
          <option value="">Selecione…</option>
          {impressoras?.map((i) => (
            <option key={i.num_serie} value={i.num_serie}>{i.nome} ({i.local.setor})</option>
          ))}
        </select>
      </FormField>
      <FormField label="Tipo de Impressão" error={errors.tipo_impressao_id?.message} required>
        <select {...register('tipo_impressao_id')} className={`input ${errors.tipo_impressao_id ? 'input-error' : ''}`}>
          <option value="">Selecione…</option>
          {tipos?.map((t) => (
            <option key={t.id} value={t.id}>{t.descricao} (franquia: {t.franquia.toLocaleString('pt-BR')} pág.)</option>
          ))}
        </select>
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Mês de referência" error={errors.mes_referencia?.message} required>
          <select {...register('mes_referencia')} className="input">
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>{m.toString().padStart(2, '0')}</option>
            ))}
          </select>
        </FormField>
        <FormField label="Ano de referência" error={errors.ano_referencia?.message} required>
          <input {...register('ano_referencia')} type="number" className="input"
            defaultValue={new Date().getFullYear()} min={2000} max={2100} />
        </FormField>
      </div>
    </>
  )
}

// ── Formulário Manual ─────────────────────────────────────────────────────────

function ManualForm({ onSubmit, isLoading }: { onSubmit: (d: ManualFormData) => void; isLoading: boolean }) {
  const { register, handleSubmit, formState: { errors } } = useForm<ManualFormData>({
    resolver: zodResolver(manualSchema),
    defaultValues: { mes_referencia: new Date().getMonth() + 1, ano_referencia: new Date().getFullYear() },
  })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <ImpressoraTipoFields register={register} errors={errors} />
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Contador (total acumulado)" error={errors.contador?.message} required>
          <input {...register('contador')} type="number" min={0} className={`input ${errors.contador ? 'input-error' : ''}`} placeholder="98765" />
        </FormField>
        <FormField label="Data da leitura" error={errors.data?.message} required>
          <input {...register('data')} type="date" className="input" defaultValue={new Date().toISOString().slice(0, 10)} />
        </FormField>
      </div>
      <FormField label="Observação" error={errors.observacao?.message}>
        <textarea {...register('observacao')} rows={2} className="input" placeholder="SNMP indisponível — leitura manual no painel…" />
      </FormField>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? <Spinner className="h-4 w-4" /> : 'Registrar Leitura'}
        </button>
      </div>
    </form>
  )
}

// ── Formulário SNMP ───────────────────────────────────────────────────────────

function SNMPForm({ onSubmit, isLoading }: { onSubmit: (d: SNMPFormData) => void; isLoading: boolean }) {
  const { register, handleSubmit, formState: { errors } } = useForm<SNMPFormData>({
    resolver: zodResolver(snmpSchema),
    defaultValues: { mes_referencia: new Date().getMonth() + 1, ano_referencia: new Date().getFullYear() },
  })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700 mb-2">
        O sistema tentará ler o contador diretamente na impressora via SNMP.
        Se falhar, use o lançamento manual.
      </div>
      <ImpressoraTipoFields register={register} errors={errors} />
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? <><Spinner className="h-4 w-4" /> Lendo via SNMP…</> : <><Zap className="w-4 h-4" /> Ler via SNMP</>}
        </button>
      </div>
    </form>
  )
}

// ── Página Principal ──────────────────────────────────────────────────────────

const MESES = ['', 'Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

export default function LeiturasPage() {
  const qc = useQueryClient()
  const now = new Date()
  const [filterMes, setFilterMes] = useState(now.getMonth() + 1)
  const [filterAno, setFilterAno] = useState(now.getFullYear())
  const [showManual, setShowManual] = useState(false)
  const [showSNMP, setShowSNMP] = useState(false)
  const [deleteItem, setDeleteItem] = useState<LeituraOut | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const { data: leituras, isLoading } = useQuery({
    queryKey: ['leituras', filterMes, filterAno],
    queryFn: () => leiturasApi.list({ mes_referencia: filterMes, ano_referencia: filterAno }),
  })

  const manualM = useMutation({
    mutationFn: leiturasApi.createManual,
    onSuccess: (l) => {
      qc.invalidateQueries({ queryKey: ['leituras'] })
      setShowManual(false)
      setSuccessMsg(`Leitura manual registrada — contador: ${l.contador.toLocaleString('pt-BR')}`)
    },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const snmpM = useMutation({
    mutationFn: leiturasApi.createSNMP,
    onSuccess: (l) => {
      qc.invalidateQueries({ queryKey: ['leituras'] })
      setShowSNMP(false)
      setSuccessMsg(`Leitura SNMP registrada — contador: ${l.contador.toLocaleString('pt-BR')}`)
    },
    onError: (e) => { setApiError(getApiErrorMessage(e)); setShowSNMP(false) },
  })
  const deleteM = useMutation({
    mutationFn: leiturasApi.remove,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leituras'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Leituras de Contadores" subtitle="Registros de contadores mensais das impressoras"
        actions={
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => { setApiError(null); setShowSNMP(true) }}>
              <Zap className="w-4 h-4" /> Leitura SNMP
            </button>
            <button className="btn-primary" onClick={() => { setApiError(null); setShowManual(true) }}>
              <ClipboardEdit className="w-4 h-4" /> Lançamento Manual
            </button>
          </div>
        } />

      {apiError  && <div className="mb-4"><AlertMessage type="error"   message={apiError}   onClose={() => setApiError(null)}   /></div>}
      {successMsg && <div className="mb-4"><AlertMessage type="success" message={successMsg} onClose={() => setSuccessMsg(null)} /></div>}

      {/* Filtro de período */}
      <div className="card mb-4 flex flex-wrap gap-3 items-center">
        <span className="text-sm text-gray-600 font-medium">Período de referência:</span>
        <select value={filterMes} onChange={(e) => setFilterMes(Number(e.target.value))} className="input w-32">
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
            <option key={m} value={m}>{MESES[m]}</option>
          ))}
        </select>
        <input type="number" value={filterAno} onChange={(e) => setFilterAno(Number(e.target.value))}
          className="input w-28" min={2000} max={2100} />
        <span className="badge-blue">{leituras?.length ?? 0} leitura(s)</span>
      </div>

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>Impressora</th><th>Setor</th><th>Tipo de Impressão</th>
              <th>Contador</th><th>Data</th><th>Origem</th><th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(leituras ?? []).length === 0
              ? <tr><td colSpan={7}><EmptyState message="Nenhuma leitura encontrada para este período." /></td></tr>
              : (leituras ?? []).map((l) => (
                <tr key={l.id}>
                  <td><div className="font-medium text-sm">{l.impressora.nome}</div>
                    <div className="text-xs text-gray-400 font-mono">{l.impressora_num_serie}</div></td>
                  <td>{l.impressora.local.setor}</td>
                  <td className="text-xs">{l.tipo_impressao.descricao}</td>
                  <td className="font-mono font-semibold text-fab-700">{l.contador.toLocaleString('pt-BR')}</td>
                  <td className="text-xs">{formatDate(l.data)}</td>
                  <td>
                    {l.manual
                      ? <span className="badge-yellow">Manual</span>
                      : <span className="badge-green">SNMP</span>}
                  </td>
                  <td className="text-right">
                    <button onClick={() => setDeleteItem(l)} className="btn btn-danger btn-sm" title="Excluir">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <Modal isOpen={showManual} onClose={() => setShowManual(false)} title="Lançamento Manual de Leitura" size="lg">
        <ManualForm onSubmit={(d) => manualM.mutate(d)} isLoading={manualM.isPending} />
      </Modal>
      <Modal isOpen={showSNMP} onClose={() => setShowSNMP(false)} title="Leitura Automática via SNMP" size="lg">
        <SNMPForm onSubmit={(d) => snmpM.mutate(d)} isLoading={snmpM.isPending} />
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteM.mutate(deleteItem.id)}
        message={`Excluir a leitura do contador ${deleteItem?.contador?.toLocaleString('pt-BR')} de "${deleteItem?.impressora?.nome}"?`}
        isLoading={deleteM.isPending} />
    </div>
  )
}
