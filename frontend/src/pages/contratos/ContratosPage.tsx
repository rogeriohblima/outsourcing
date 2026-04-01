/**
 * pages/contratos/ContratosPage.tsx — CRUD de Contratos.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { comissoesApi, contratosApi, empresasApi } from '@/api/endpoints'
import {
  AlertMessage, ConfirmDialog, EmptyState, FormField,
  Modal, PageHeader, PageSpinner, Spinner, formatDate, formatDateTime,
} from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { ContratoOut } from '@/types'

const schema = z.object({
  numero:         z.string().min(1),
  empresa_cnpj:   z.string().min(14),
  data_inicio:    z.string().min(1),
  data_termino:   z.string().min(1),
  comissao_id:    z.coerce.number().min(1),
  numero_processo: z.string().min(1),
})
type FormData = z.infer<typeof schema>

function ContratoForm({ defaultValues, onSubmit, isLoading, editMode }: {
  defaultValues?: Partial<FormData>; onSubmit: (d: FormData) => void
  isLoading: boolean; editMode: boolean
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues,
  })
  const { data: empresas }  = useQuery({ queryKey: ['empresas'],  queryFn: empresasApi.list })
  const { data: comissoes } = useQuery({ queryKey: ['comissoes'], queryFn: comissoesApi.list })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Número do Contrato" error={errors.numero?.message} required>
          <input {...register('numero')} className="input" placeholder="2025CT001" />
        </FormField>
        <FormField label="Nº do Processo" error={errors.numero_processo?.message} required>
          <input {...register('numero_processo')} className="input" placeholder="NUP-2025-000001" />
        </FormField>
      </div>
      <FormField label="Empresa" error={errors.empresa_cnpj?.message} required>
        <select {...register('empresa_cnpj')} className="input">
          <option value="">Selecione…</option>
          {empresas?.map((e) => <option key={e.cnpj} value={e.cnpj}>{e.nome} ({e.cnpj})</option>)}
        </select>
      </FormField>
      <FormField label="Comissão Fiscal" error={errors.comissao_id?.message} required>
        <select {...register('comissao_id')} className="input">
          <option value="">Selecione…</option>
          {comissoes?.map((c) => <option key={c.id} value={c.id}>{c.documento_numero} — {c.presidente.nome}</option>)}
        </select>
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Início de Vigência" error={errors.data_inicio?.message} required>
          <input {...register('data_inicio')} type="date" className="input" />
        </FormField>
        <FormField label="Término de Vigência" error={errors.data_termino?.message} required>
          <input {...register('data_termino')} type="date" className="input" />
        </FormField>
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? <Spinner className="h-4 w-4" /> : editMode ? 'Salvar' : 'Cadastrar'}
        </button>
      </div>
    </form>
  )
}

export default function ContratosPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editItem, setEditItem] = useState<ContratoOut | null>(null)
  const [deleteItem, setDeleteItem] = useState<ContratoOut | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: contratos, isLoading } = useQuery({ queryKey: ['contratos'], queryFn: contratosApi.list })
  const createM = useMutation({ mutationFn: contratosApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['contratos'] }); setShowCreate(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)) })
  const updateM = useMutation({ mutationFn: ({ id, data }: { id: number; data: Partial<FormData> }) => contratosApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['contratos'] }); setEditItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: (id: number) => contratosApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['contratos'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)) })

  const hoje = new Date()
  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Contratos" subtitle="Contratos de fornecimento de impressoras"
        actions={<button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}>
          <Plus className="w-4 h-4" /> Novo Contrato
        </button>} />
      {apiError && <div className="mb-4"><AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} /></div>}
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Número</th><th>Empresa</th><th>Início</th><th>Término</th><th>Processo</th><th>Status</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(contratos ?? []).length === 0
              ? <tr><td colSpan={7}><EmptyState /></td></tr>
              : (contratos ?? []).map((c) => {
                const vigente = new Date(c.data_inicio) <= hoje && new Date(c.data_termino) >= hoje
                return (
                  <tr key={c.id}>
                    <td className="font-semibold text-fab-700">{c.numero}</td>
                    <td className="text-sm">{c.empresa.nome}</td>
                    <td className="text-xs">{formatDate(c.data_inicio)}</td>
                    <td className="text-xs">{formatDate(c.data_termino)}</td>
                    <td className="text-xs text-gray-500">{c.numero_processo}</td>
                    <td>{vigente ? <span className="badge-green">Vigente</span> : new Date(c.data_termino) < hoje ? <span className="badge-red">Encerrado</span> : <span className="badge-yellow">A iniciar</span>}</td>
                    <td className="text-right">
                      <div className="flex justify-end gap-1">
                        <button onClick={() => { setApiError(null); setEditItem(c) }} className="btn btn-secondary btn-sm"><Pencil className="w-3.5 h-3.5" /></button>
                        <button onClick={() => setDeleteItem(c)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                )
              })}
          </tbody>
        </table>
      </div>
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Novo Contrato" size="lg">
        <ContratoForm onSubmit={(d) => createM.mutate(d)} isLoading={createM.isPending} editMode={false} />
      </Modal>
      <Modal isOpen={!!editItem} onClose={() => setEditItem(null)} title="Editar Contrato" size="lg">
        {editItem && <ContratoForm defaultValues={{ ...editItem, comissao_id: editItem.comissao_id }}
          onSubmit={(d) => updateM.mutate({ id: editItem.id, data: d })} isLoading={updateM.isPending} editMode />}
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteM.mutate(deleteItem.id)}
        message={`Excluir o contrato "${deleteItem?.numero}"? Faturas e documentos vinculados também serão removidos.`}
        isLoading={deleteM.isPending} />
    </div>
  )
}
