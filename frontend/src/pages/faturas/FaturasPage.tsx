/**
 * pages/faturas/FaturasPage.tsx — CRUD de Faturas.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Trash2 } from 'lucide-react'
import { contratosApi, faturasApi } from '@/api/endpoints'
import { AlertMessage, ConfirmDialog, EmptyState, FormField, Modal, PageHeader, PageSpinner, Spinner, formatDate } from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { FaturaOut } from '@/types'

const schema = z.object({ numero: z.string().min(1), data: z.string().min(1), contrato_id: z.coerce.number().min(1) })
type FormData = z.infer<typeof schema>

export default function FaturasPage() {
  const qc = useQueryClient()
  const [filterContrato, setFilterContrato] = useState<number | undefined>()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteItem, setDeleteItem] = useState<FaturaOut | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: contratos } = useQuery({ queryKey: ['contratos'], queryFn: contratosApi.list })
  const { data: faturas, isLoading } = useQuery({ queryKey: ['faturas', filterContrato], queryFn: () => faturasApi.list(filterContrato) })

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  const createM = useMutation({ mutationFn: faturasApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['faturas'] }); setShowCreate(false); reset() },
    onError: (e) => setApiError(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: (id: number) => faturasApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['faturas'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)) })

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Faturas" subtitle="Faturas emitidas pelas empresas contratadas"
        actions={<button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}><Plus className="w-4 h-4" /> Nova Fatura</button>} />
      {apiError && <div className="mb-4"><AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} /></div>}
      <div className="card mb-4 flex gap-3 items-end">
        <div>
          <label className="label">Filtrar por contrato</label>
          <select className="input w-72" value={filterContrato ?? ''} onChange={(e) => setFilterContrato(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">Todos os contratos</option>
            {contratos?.map((c) => <option key={c.id} value={c.id}>{c.numero} — {c.empresa.nome}</option>)}
          </select>
        </div>
      </div>
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Número</th><th>Data</th><th>Contrato</th><th>Empresa</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(faturas ?? []).length === 0 ? <tr><td colSpan={5}><EmptyState /></td></tr>
              : (faturas ?? []).map((f) => (
                <tr key={f.id}>
                  <td className="font-medium">{f.numero}</td>
                  <td>{formatDate(f.data)}</td>
                  <td className="text-fab-700 font-medium">{f.contrato.numero}</td>
                  <td className="text-sm text-gray-600">{f.contrato.empresa.nome}</td>
                  <td className="text-right"><button onClick={() => setDeleteItem(f)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button></td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nova Fatura">
        <form onSubmit={handleSubmit((d) => createM.mutate(d))} className="space-y-4">
          <FormField label="Número da Fatura" error={errors.numero?.message} required>
            <input {...register('numero')} className="input" placeholder="NF-000001" />
          </FormField>
          <FormField label="Data" error={errors.data?.message} required>
            <input {...register('data')} type="date" className="input" />
          </FormField>
          <FormField label="Contrato" error={errors.contrato_id?.message} required>
            <select {...register('contrato_id')} className="input">
              <option value="">Selecione…</option>
              {contratos?.map((c) => <option key={c.id} value={c.id}>{c.numero} — {c.empresa.nome}</option>)}
            </select>
          </FormField>
          <div className="flex justify-end pt-2">
            <button type="submit" disabled={createM.isPending} className="btn-primary">
              {createM.isPending ? <Spinner className="h-4 w-4" /> : 'Cadastrar'}
            </button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteM.mutate(deleteItem.id)}
        message={`Excluir a fatura "${deleteItem?.numero}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}
