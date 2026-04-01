/**
 * pages/documentos/DocumentosPage.tsx — CRUD de Documentos Contábeis.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Trash2 } from 'lucide-react'
import { contratosApi, docsContabeisApi, tiposDocApi } from '@/api/endpoints'
import { AlertMessage, ConfirmDialog, EmptyState, FormField, Modal, PageHeader, PageSpinner, Spinner, formatCurrency } from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { DocumentoContabilOut } from '@/types'

const schema = z.object({
  numero: z.string().min(1), tipo_documento_id: z.coerce.number().min(1),
  contrato_id: z.coerce.number().min(1), valor: z.coerce.number().min(0),
})
type FormData = z.infer<typeof schema>

export default function DocumentosPage() {
  const qc = useQueryClient()
  const [filterContrato, setFilterContrato] = useState<number | undefined>()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteItem, setDeleteItem] = useState<DocumentoContabilOut | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: contratos } = useQuery({ queryKey: ['contratos'], queryFn: contratosApi.list })
  const { data: tiposDoc }  = useQuery({ queryKey: ['tipos-doc'], queryFn: tiposDocApi.list })
  const { data: docs, isLoading } = useQuery({ queryKey: ['docs-contabeis', filterContrato], queryFn: () => docsContabeisApi.list(filterContrato) })

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })
  const createM = useMutation({ mutationFn: docsContabeisApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['docs-contabeis'] }); setShowCreate(false); reset() },
    onError: (e) => setApiError(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: docsContabeisApi.remove,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['docs-contabeis'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)) })

  if (isLoading) return <PageSpinner />

  const totalEmpenhado = (docs ?? []).reduce((acc, d) => acc + Number(d.valor), 0)

  return (
    <div>
      <PageHeader title="Documentos Contábeis" subtitle="Notas de Empenho, Ordens Bancárias e outros documentos"
        actions={<button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}><Plus className="w-4 h-4" /> Novo Documento</button>} />
      {apiError && <div className="mb-4"><AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} /></div>}
      <div className="card mb-4 flex flex-wrap gap-4 items-center justify-between">
        <div>
          <label className="label">Filtrar por contrato</label>
          <select className="input w-72" value={filterContrato ?? ''} onChange={(e) => setFilterContrato(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">Todos os contratos</option>
            {contratos?.map((c) => <option key={c.id} value={c.id}>{c.numero} — {c.empresa.nome}</option>)}
          </select>
        </div>
        {filterContrato && <div className="text-right"><p className="text-sm text-gray-500">Total empenhado</p><p className="text-xl font-bold text-fab-700">{formatCurrency(totalEmpenhado)}</p></div>}
      </div>
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Número</th><th>Tipo</th><th>Contrato</th><th className="text-right">Valor</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(docs ?? []).length === 0 ? <tr><td colSpan={5}><EmptyState /></td></tr>
              : (docs ?? []).map((d) => (
                <tr key={d.id}>
                  <td className="font-medium font-mono text-sm">{d.numero}</td>
                  <td><span className="badge-blue">{d.tipo_documento.nome}</span></td>
                  <td className="text-fab-700 font-medium">{d.contrato.numero}</td>
                  <td className="text-right font-semibold text-emerald-700">{formatCurrency(Number(d.valor))}</td>
                  <td className="text-right"><button onClick={() => setDeleteItem(d)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button></td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Novo Documento Contábil" size="lg">
        <form onSubmit={handleSubmit((d) => createM.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Número do Documento" error={errors.numero?.message} required>
              <input {...register('numero')} className="input" placeholder="2025NE000001" />
            </FormField>
            <FormField label="Valor (R$)" error={errors.valor?.message} required>
              <input {...register('valor')} type="number" step="0.01" min={0} className="input" placeholder="10000.00" />
            </FormField>
          </div>
          <FormField label="Tipo de Documento" error={errors.tipo_documento_id?.message} required>
            <select {...register('tipo_documento_id')} className="input">
              <option value="">Selecione…</option>
              {tiposDoc?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
            </select>
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
        message={`Excluir o documento "${deleteItem?.numero}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}
