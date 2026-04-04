/**
 * pages/impressoras/ImpressorasPage.tsx — CRUD de Impressoras.
 *
 * Funcionalidades:
 *  - Listagem com filtro por status ativo/inativo e busca por nome/série
 *  - Criação e edição com seleção de Tipo e Local
 *  - Botão "Testar SNMP" para verificar conectividade sem salvar leitura
 *  - Ativação/desativação rápida
 *  - Exclusão com confirmação
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Activity, Pencil, Plus, Search, Trash2, Wifi, WifiOff } from 'lucide-react'
import { impressorasApi, locaisImpressoraApi, modelosImpressoraApi, tiposImpressoraApi } from '@/api/endpoints'
import {
  AlertMessage, ConfirmDialog, EmptyState, FormField,
  Modal, PageHeader, PageSpinner, Spinner, StatusBadge, formatDateTime,
} from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { ImpressoraOut } from '@/types'

const schema = z.object({
  num_serie:  z.string().min(1, 'Obrigatório').max(100),
  modelo_id:  z.coerce.number().optional(),
  tipo_id:    z.coerce.number().min(1, 'Selecione o tipo'),
  local_id:   z.coerce.number().min(1, 'Selecione o local'),
  ip:        z.string().max(45).optional().or(z.literal('')),
  ativa:     z.boolean(),
})
type FormData = z.infer<typeof schema>

function ImpressoraForm({ defaultValues, onSubmit, isLoading, editMode }: {
  defaultValues?: Partial<FormData>; onSubmit: (d: FormData) => void
  isLoading: boolean; editMode: boolean
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { ativa: true, ...defaultValues },
  })
  const { data: modelos } = useQuery({ queryKey: ['modelos-impressora'], queryFn: () => modelosImpressoraApi.list() })
  const { data: tipos } = useQuery({ queryKey: ['tipos-impressora'], queryFn: tiposImpressoraApi.list })
  const { data: locais } = useQuery({ queryKey: ['locais-impressora'], queryFn: locaisImpressoraApi.list })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField label="Nº de Série" error={errors.num_serie?.message} required>
        <input {...register('num_serie')} className={`input ${errors.num_serie ? 'input-error' : ''}`}
          placeholder="SN-XXXXXXXX" disabled={editMode} />
      </FormField>
      <FormField label="Modelo" error={errors.modelo_id?.message}>
        <select {...register('modelo_id')} className="input">
          <option value="">Selecione o modelo (opcional)...</option>
          {modelos && Object.entries(
            modelos.reduce((acc, m) => {
              if (!acc[m.fabricante]) acc[m.fabricante] = []
              acc[m.fabricante].push(m)
              return acc
            }, {} as Record<string, typeof modelos>
          )).map(([fab, lista]) => (
            <optgroup key={fab} label={fab}>
              {lista.map(m => (
                <option key={m.id} value={m.id}>{m.modelo}{m.descricao ? ` — ${m.descricao}` : ''}</option>
              ))}
            </optgroup>
          ))}
        </select>
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Tipo" error={errors.tipo_id?.message} required>
          <select {...register('tipo_id')} className={`input ${errors.tipo_id ? 'input-error' : ''}`}>
            <option value="">Selecione…</option>
            {tipos?.map((t) => <option key={t.id} value={t.id}>{t.tipo}</option>)}
          </select>
        </FormField>
        <FormField label="Local / Setor" error={errors.local_id?.message} required>
          <select {...register('local_id')} className={`input ${errors.local_id ? 'input-error' : ''}`}>
            <option value="">Selecione…</option>
            {locais?.map((l) => <option key={l.id} value={l.id}>{l.setor} — {l.descricao}</option>)}
          </select>
        </FormField>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Endereço IP (SNMP)" error={errors.ip?.message}>
          <input {...register('ip')} className="input" placeholder="192.168.1.100" />
        </FormField>
        <FormField label="Status">
          <label className="flex items-center gap-2 mt-2 cursor-pointer">
            <input {...register('ativa')} type="checkbox" className="w-4 h-4 accent-fab-600" />
            <span className="text-sm text-gray-600">Impressora ativa</span>
          </label>
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

export default function ImpressorasPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [filterAtiva, setFilterAtiva] = useState<boolean | undefined>(undefined)
  const [showCreate, setShowCreate] = useState(false)
  const [editItem, setEditItem] = useState<ImpressoraOut | null>(null)
  const [deleteItem, setDeleteItem] = useState<ImpressoraOut | null>(null)
  const [snmpResult, setSnmpResult] = useState<{ numSerie: string; msg: string; ok: boolean } | null>(null)
  const [testingSnmp, setTestingSnmp] = useState<string | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: impressoras, isLoading } = useQuery({
    queryKey: ['impressoras', { ativa: filterAtiva }],
    queryFn: () => impressorasApi.list({ ativa: filterAtiva }),
  })

  const createM = useMutation({
    mutationFn: impressorasApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['impressoras'] }); setShowCreate(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const updateM = useMutation({
    mutationFn: ({ ns, data }: { ns: string; data: Partial<FormData> }) => impressorasApi.update(ns, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['impressoras'] }); setEditItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const deleteM = useMutation({
    mutationFn: impressorasApi.remove,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['impressoras'] }); setDeleteItem(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  const testarSnmp = async (imp: ImpressoraOut) => {
    if (!imp.ip) { setSnmpResult({ numSerie: imp.num_serie, msg: 'IP não configurado.', ok: false }); return }
    setTestingSnmp(imp.num_serie)
    try {
      const r = await impressorasApi.lerSNMP(imp.num_serie)
      setSnmpResult({
        numSerie: imp.num_serie,
        msg: r.sucesso ? `Contador: ${r.contador?.toLocaleString('pt-BR')} páginas (OID: ${r.oid_usado})` : (r.erro ?? 'Falha desconhecida'),
        ok: !!r.sucesso,
      })
    } catch (e) {
      setSnmpResult({ numSerie: imp.num_serie, msg: getApiErrorMessage(e), ok: false })
    } finally {
      setTestingSnmp(null)
    }
  }

  const filtered = (impressoras ?? []).filter(
    (i) => {
      const nomeModelo = i.modelo ? `${i.modelo.fabricante} ${i.modelo.modelo}` : ''
      return nomeModelo.toLowerCase().includes(search.toLowerCase()) ||
             i.num_serie.toLowerCase().includes(search.toLowerCase())
    }
  )

  if (isLoading) return <PageSpinner />

  return (
    <div>
      <PageHeader title="Impressoras" subtitle="Impressoras monitoradas no contrato"
        actions={<button className="btn-primary" onClick={() => { setApiError(null); setShowCreate(true) }}>
          <Plus className="w-4 h-4" /> Nova Impressora
        </button>} />

      {apiError && <div className="mb-4"><AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} /></div>}
      {snmpResult && (
        <div className="mb-4">
          <AlertMessage type={snmpResult.ok ? 'success' : 'error'}
            message={`[${snmpResult.numSerie}] ${snmpResult.msg}`}
            onClose={() => setSnmpResult(null)} />
        </div>
      )}

      {/* Filtros */}
      <div className="card mb-4 flex flex-wrap gap-3 items-center">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="input pl-9 w-60" placeholder="Buscar por modelo ou série…" />
        </div>
        <div className="flex gap-2">
          {[undefined, true, false].map((v) => (
            <button key={String(v)} onClick={() => setFilterAtiva(v)}
              className={`btn btn-sm ${filterAtiva === v ? 'btn-primary' : 'btn-secondary'}`}>
              {v === undefined ? 'Todas' : v ? 'Ativas' : 'Inativas'}
            </button>
          ))}
        </div>
      </div>

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>Nº Série</th><th>Modelo</th><th>Tipo</th>
              <th>Setor</th><th>IP</th><th>Status</th><th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.length === 0
              ? <tr><td colSpan={7}><EmptyState /></td></tr>
              : filtered.map((imp) => (
                <tr key={imp.num_serie}>
                  <td className="font-mono text-xs">{imp.num_serie}</td>
                  <td className="text-xs">{imp.modelo ? <span className="badge-gray">{imp.modelo.fabricante} {imp.modelo.modelo}</span> : <span className="text-gray-300">—</span>}</td>
                  <td><span className="badge-blue">{imp.tipo.tipo}</span></td>
                  <td className="text-gray-600">{imp.local.setor}</td>
                  <td className="font-mono text-xs text-gray-500">{imp.ip ?? '—'}</td>
                  <td><StatusBadge ativo={imp.ativa} /></td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      <button onClick={() => testarSnmp(imp)} disabled={testingSnmp === imp.num_serie}
                        className="btn btn-secondary btn-sm" title="Testar SNMP">
                        {testingSnmp === imp.num_serie ? <Spinner className="h-3.5 w-3.5" /> : <Activity className="w-3.5 h-3.5" />}
                      </button>
                      <button onClick={() => { setApiError(null); setEditItem(imp) }} className="btn btn-secondary btn-sm" title="Editar">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setDeleteItem(imp)} className="btn btn-danger btn-sm" title="Excluir">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nova Impressora" size="lg">
        <ImpressoraForm onSubmit={(d) => createM.mutate(d)} isLoading={createM.isPending} editMode={false} />
      </Modal>
      <Modal isOpen={!!editItem} onClose={() => setEditItem(null)} title="Editar Impressora" size="lg">
        {editItem && (
          <ImpressoraForm
            defaultValues={{ num_serie: editItem.num_serie, modelo_id: editItem.modelo_id, tipo_id: editItem.tipo_id, local_id: editItem.local_id, ip: editItem.ip ?? '', ativa: editItem.ativa }}
            onSubmit={(d) => updateM.mutate({ ns: editItem.num_serie, data: d })}
            isLoading={updateM.isPending} editMode />
        )}
      </Modal>
      <ConfirmDialog isOpen={!!deleteItem} onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteM.mutate(deleteItem.num_serie)}
        message={`Excluir a impressora "${deleteItem?.modelo ? `${deleteItem.modelo.fabricante} ${deleteItem.modelo.modelo}` : deleteItem?.num_serie}" e todas as suas leituras?`}
        isLoading={deleteM.isPending} />
    </div>
  )
}
