/**
 * pages/empresas/EmpresasPage.tsx — CRUD completo de Empresas contratadas.
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Search } from 'lucide-react'
import { empresasApi } from '@/api/endpoints'
import {
  AlertMessage, ConfirmDialog, EmptyState, FormField,
  Modal, PageHeader, PageSpinner, Spinner, formatDateTime,
} from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { EmpresaOut } from '@/types'

const schema = z.object({
  cnpj: z.string().min(14, 'CNPJ inválido').max(18),
  nome: z.string().min(2, 'Nome muito curto').max(300),
})
type FormData = z.infer<typeof schema>

function EmpresaForm({ defaultValues, onSubmit, isLoading, editMode }: {
  defaultValues?: Partial<FormData>; onSubmit: (d: FormData) => void
  isLoading: boolean; editMode: boolean
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues,
  })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField label="CNPJ" error={errors.cnpj?.message} required>
        <input {...register('cnpj')} className={`input ${errors.cnpj ? 'input-error' : ''}`}
          placeholder="00.000.000/0001-00" disabled={editMode} />
      </FormField>
      <FormField label="Razão Social" error={errors.nome?.message} required>
        <input {...register('nome')} className={`input ${errors.nome ? 'input-error' : ''}`}
          placeholder="Empresa de Tecnologia LTDA" />
      </FormField>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? <Spinner className="h-4 w-4" /> : editMode ? 'Salvar' : 'Cadastrar'}
        </button>
      </div>
    </form>
  )
}

export default function EmpresasPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editItem, setEditItem] = useState<EmpresaOut | null>(null)
  const [deleteItem, setDeleteItem] = useState<EmpresaOut | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: empresas, isLoading } = useQuery({ queryKey: ['empresas'], queryFn: empresasApi.list })

  const createM = useMutation({
    mutationFn: empresasApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['empresas'] }); setShowCreate(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const updateM = useMutation({
    mutationFn: ({ cnpj, data }: { cnpj: string; data: Partial<FormData> }) => empresasApi.update(cnpj, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['empresas'] }); setEditItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const deleteM = useMutation({
    mutationFn: (cnpj: string) => empresasApi.remove(cnpj),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['empresas'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  const filtered = (empresas ?? []).filter(
    (e) => e.nome.toLowerCase().includes(search.toLowerCase()) || e.cnpj.includes(search)
  )

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Empresas" subtitle="Empresas contratadas para fornecimento de impressoras"
        actions={<button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}>
          <Plus className="w-4 h-4" /> Nova Empresa
        </button>} />

      {apiError && <div className="mb-4"><AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} /></div>}

      <div className="card mb-4">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input pl-9" placeholder="Buscar por nome ou CNPJ…" />
        </div>
      </div>

      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>CNPJ</th><th>Razão Social</th><th>Cadastrado em</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.length === 0
              ? <tr><td colSpan={4}><EmptyState /></td></tr>
              : filtered.map((e) => (
                <tr key={e.cnpj}>
                  <td className="font-mono text-xs">{e.cnpj}</td>
                  <td className="font-medium">{e.nome}</td>
                  <td className="text-gray-400 text-xs">{formatDateTime(e.criado_em)}</td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      <button onClick={() => { setApiError(null); setEditItem(e) }} className="btn btn-secondary btn-sm"><Pencil className="w-3.5 h-3.5" /></button>
                      <button onClick={() => setDeleteItem(e)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nova Empresa">
        <EmpresaForm onSubmit={(d) => createM.mutate(d)} isLoading={createM.isPending} editMode={false} />
      </Modal>
      <Modal isOpen={!!editItem} onClose={() => setEditItem(null)} title="Editar Empresa">
        {editItem && <EmpresaForm defaultValues={editItem} onSubmit={(d) => updateM.mutate({ cnpj: editItem.cnpj, data: d })} isLoading={updateM.isPending} editMode />}
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteM.mutate(deleteItem.cnpj)}
        message={`Deseja excluir a empresa "${deleteItem?.nome}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}
