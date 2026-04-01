/**
 * pages/membros/MembrosPage.tsx — CRUD completo de Membros.
 *
 * Funcionalidades:
 *  - Listagem em tabela com busca local por nome/CPF
 *  - Criação via modal com validação Zod
 *  - Edição inline via modal
 *  - Exclusão com confirmação
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Search } from 'lucide-react'
import { membrosApi } from '@/api/endpoints'
import {
  AlertMessage, ConfirmDialog, EmptyState, FormField,
  Modal, PageHeader, PageSpinner, Spinner, formatDateTime,
} from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { MembroOut } from '@/types'

// ── Schema de validação ───────────────────────────────────────────────────────

const membroSchema = z.object({
  cpf:  z.string().min(11, 'CPF inválido').max(14, 'CPF inválido'),
  nome: z.string().min(3, 'Nome muito curto').max(200),
})
type MembroFormData = z.infer<typeof membroSchema>

// ── Formulário de Membro ──────────────────────────────────────────────────────

function MembroForm({
  defaultValues,
  onSubmit,
  isLoading,
  editMode,
}: {
  defaultValues?: Partial<MembroFormData>
  onSubmit: (data: MembroFormData) => void
  isLoading: boolean
  editMode: boolean
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<MembroFormData>({
    resolver: zodResolver(membroSchema),
    defaultValues,
  })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField label="CPF" error={errors.cpf?.message} required>
        <input
          {...register('cpf')}
          className={`input ${errors.cpf ? 'input-error' : ''}`}
          placeholder="000.000.000-00"
          disabled={editMode}
        />
      </FormField>
      <FormField label="Nome completo" error={errors.nome?.message} required>
        <input
          {...register('nome')}
          className={`input ${errors.nome ? 'input-error' : ''}`}
          placeholder="Cap João da Silva"
        />
      </FormField>
      <div className="flex justify-end gap-2 pt-2">
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? <Spinner className="h-4 w-4" /> : editMode ? 'Salvar' : 'Cadastrar'}
        </button>
      </div>
    </form>
  )
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function MembrosPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editItem, setEditItem] = useState<MembroOut | null>(null)
  const [deleteItem, setDeleteItem] = useState<MembroOut | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: membros, isLoading } = useQuery({
    queryKey: ['membros'],
    queryFn: membrosApi.list,
  })

  const createMutation = useMutation({
    mutationFn: membrosApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['membros'] }); setShowCreate(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ cpf, data }: { cpf: string; data: Partial<MembroFormData> }) =>
      membrosApi.update(cpf, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['membros'] }); setEditItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  const deleteMutation = useMutation({
    mutationFn: (cpf: string) => membrosApi.remove(cpf),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['membros'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  const filtered = (membros ?? []).filter(
    (m) =>
      m.nome.toLowerCase().includes(search.toLowerCase()) ||
      m.cpf.includes(search)
  )

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader
        title="Membros"
        subtitle="Integrantes disponíveis para composição de comissões fiscais"
        actions={
          <button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}>
            <Plus className="w-4 h-4" /> Novo Membro
          </button>
        }
      />

      {apiError && (
        <div className="mb-4">
          <AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} />
        </div>
      )}

      {/* Busca */}
      <div className="card mb-4">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-9"
            placeholder="Buscar por nome ou CPF…"
          />
        </div>
      </div>

      {/* Tabela */}
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>CPF</th>
              <th>Nome</th>
              <th>Cadastrado em</th>
              <th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.length === 0 ? (
              <tr><td colSpan={4}><EmptyState message="Nenhum membro encontrado." /></td></tr>
            ) : (
              filtered.map((m) => (
                <tr key={m.cpf}>
                  <td className="font-mono text-xs">{m.cpf}</td>
                  <td className="font-medium">{m.nome}</td>
                  <td className="text-gray-400 text-xs">{formatDateTime(m.criado_em)}</td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => { setApiError(null); setEditItem(m) }}
                        className="btn btn-secondary btn-sm"
                        title="Editar"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setDeleteItem(m)}
                        className="btn btn-danger btn-sm"
                        title="Excluir"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal — Criar */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Novo Membro">
        <MembroForm
          onSubmit={(d) => createMutation.mutate(d)}
          isLoading={createMutation.isPending}
          editMode={false}
        />
      </Modal>

      {/* Modal — Editar */}
      <Modal isOpen={!!editItem} onClose={() => setEditItem(null)} title="Editar Membro">
        {editItem && (
          <MembroForm
            defaultValues={editItem}
            onSubmit={(d) => updateMutation.mutate({ cpf: editItem.cpf, data: d })}
            isLoading={updateMutation.isPending}
            editMode
          />
        )}
      </Modal>

      {/* Confirmação — Excluir */}
      <ConfirmDialog
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteMutation.mutate(deleteItem.cpf)}
        message={`Deseja excluir o membro "${deleteItem?.nome}"? Esta ação não pode ser desfeita.`}
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
