/**
 * pages/comissoes/ComissoesPage.tsx — CRUD de Comissões Fiscais.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Trash2, UserPlus, Upload } from 'lucide-react'
import { comissoesApi, membrosApi } from '@/api/endpoints'
import { AlertMessage, ConfirmDialog, EmptyState, FormField, Modal, PageHeader, PageSpinner, Spinner, formatDate } from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { ComissaoOut } from '@/types'

const schema = z.object({
  presidente_cpf:  z.string().min(11),
  documento_numero: z.string().min(1),
  documento_data:  z.string().min(1),
  fiscais_cpf:     z.array(z.object({ cpf: z.string().min(11) })),
})
type FormData = z.infer<typeof schema>

function ComissaoForm({ onSubmit, isLoading }: { onSubmit: (d: FormData) => void; isLoading: boolean }) {
  const { register, handleSubmit, control, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: { fiscais_cpf: [] },
  })
  const { fields, append, remove } = useFieldArray({ control, name: 'fiscais_cpf' })
  const { data: membros } = useQuery({ queryKey: ['membros'], queryFn: membrosApi.list })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField label="Presidente da Comissão" error={errors.presidente_cpf?.message} required>
        <select {...register('presidente_cpf')} className="input">
          <option value="">Selecione o presidente…</option>
          {membros?.map((m) => <option key={m.cpf} value={m.cpf}>{m.nome} ({m.cpf})</option>)}
        </select>
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Nº do Ato de Designação" error={errors.documento_numero?.message} required>
          <input {...register('documento_numero')} className="input" placeholder="BI 001/2025" />
        </FormField>
        <FormField label="Data do Ato" error={errors.documento_data?.message} required>
          <input {...register('documento_data')} type="date" className="input" />
        </FormField>
      </div>
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="label mb-0">Fiscais</label>
          <button type="button" onClick={() => append({ cpf: '' })} className="btn btn-secondary btn-sm">
            <UserPlus className="w-3.5 h-3.5" /> Adicionar Fiscal
          </button>
        </div>
        <div className="space-y-2">
          {fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2">
              <select {...register(`fiscais_cpf.${idx}.cpf`)} className="input flex-1">
                <option value="">Selecione…</option>
                {membros?.map((m) => <option key={m.cpf} value={m.cpf}>{m.nome} ({m.cpf})</option>)}
              </select>
              <button type="button" onClick={() => remove(idx)} className="btn btn-danger btn-sm px-2"><Trash2 className="w-3.5 h-3.5" /></button>
            </div>
          ))}
          {fields.length === 0 && <p className="text-xs text-gray-400">Nenhum fiscal adicionado.</p>}
        </div>
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? <Spinner className="h-4 w-4" /> : 'Cadastrar Comissão'}
        </button>
      </div>
    </form>
  )
}

export default function ComissoesPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteItem, setDeleteItem] = useState<ComissaoOut | null>(null)
  const [uploadId, setUploadId] = useState<number | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: comissoes, isLoading } = useQuery({ queryKey: ['comissoes'], queryFn: comissoesApi.list })

  const createM = useMutation({
    mutationFn: (d: FormData) => comissoesApi.create({ ...d, fiscais_cpf: d.fiscais_cpf.map((f) => f.cpf) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['comissoes'] }); setShowCreate(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const deleteM = useMutation({ mutationFn: comissoesApi.remove,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['comissoes'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)) })

  const handleUpload = async (id: number, file: File) => {
    try {
      await comissoesApi.uploadDocumento(id, file)
      qc.invalidateQueries({ queryKey: ['comissoes'] })
      setUploadId(null)
    } catch (e) { setApiError(getApiErrorMessage(e)) }
  }

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Comissões Fiscais" subtitle="Comissões designadas para fiscalização dos contratos"
        actions={<button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}><Plus className="w-4 h-4" /> Nova Comissão</button>} />
      {apiError && <div className="mb-4"><AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} /></div>}
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Ato</th><th>Data</th><th>Presidente</th><th>Fiscais</th><th>Documento</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(comissoes ?? []).length === 0 ? <tr><td colSpan={6}><EmptyState /></td></tr>
              : (comissoes ?? []).map((c) => (
                <tr key={c.id}>
                  <td className="font-medium">{c.documento_numero}</td>
                  <td className="text-xs">{formatDate(c.documento_data)}</td>
                  <td className="text-sm">{c.presidente.nome}</td>
                  <td className="text-xs text-gray-500">{c.fiscais.length > 0 ? c.fiscais.map((f) => f.nome).join(', ') : '—'}</td>
                  <td>
                    {c.documento_path
                      ? <span className="badge-green">Anexado</span>
                      : <button onClick={() => setUploadId(c.id)} className="btn btn-secondary btn-sm"><Upload className="w-3.5 h-3.5" /> Anexar</button>}
                  </td>
                  <td className="text-right">
                    <button onClick={() => setDeleteItem(c)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nova Comissão Fiscal" size="lg">
        <ComissaoForm onSubmit={(d) => createM.mutate(d)} isLoading={createM.isPending} />
      </Modal>
      {/* Upload de documento */}
      <Modal isOpen={uploadId !== null} onClose={() => setUploadId(null)} title="Anexar Documento PDF" size="sm">
        <div className="space-y-3">
          <p className="text-sm text-gray-600">Selecione o arquivo PDF do ato de designação da comissão.</p>
          <input type="file" accept="application/pdf" className="input"
            onChange={(e) => { const f = e.target.files?.[0]; if (f && uploadId) handleUpload(uploadId, f) }} />
        </div>
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteM.mutate(deleteItem.id)}
        message={`Excluir a comissão "${deleteItem?.documento_numero}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}
