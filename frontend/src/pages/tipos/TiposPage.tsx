/**
 * pages/tipos/TiposPage.tsx — Tabelas de domínio em abas.
 *
 * Gerencia em uma única página (com abas):
 *  - Tipos de Documento (NE, OB, etc.)
 *  - Tipos de Impressora (Laser, Jato de tinta, etc.)
 *  - Locais de Impressora (Setor + Descrição)
 *  - Tipos de Impressão (com valores de franquia)
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Plus, Trash2 } from 'lucide-react'
import { tiposDocApi, tiposImpressoraApi, locaisImpressoraApi, tiposImpressaoApi } from '@/api/endpoints'
import { AlertMessage, ConfirmDialog, EmptyState, FormField, Modal, PageHeader, PageSpinner, Spinner, formatCurrency } from '@/components/common'
import { getApiErrorMessage } from '@/api/client'

// ── Tipo de Documento ─────────────────────────────────────────────────────────
function TiposDocTab() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false)
  const [del, setDel] = useState<{ id: number; nome: string } | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const { data, isLoading } = useQuery({ queryKey: ['tipos-doc'], queryFn: tiposDocApi.list })
  const { register, handleSubmit, reset } = useForm<{ nome: string }>()
  const createM = useMutation({ mutationFn: tiposDocApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tipos-doc'] }); setShow(false); reset() }, onError: (e) => setErr(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: tiposDocApi.remove, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tipos-doc'] }); setDel(null) }, onError: (e) => setErr(getApiErrorMessage(e)) })
  if (isLoading) return <PageSpinner />
  return (
    <div className="space-y-4">
      {err && <AlertMessage type="error" message={err} onClose={() => setErr(null)} />}
      <div className="flex justify-end"><button className="btn-primary" onClick={() => setShow(true)}><Plus className="w-4 h-4" /> Novo</button></div>
      <div className="table-wrapper">
        <table className="table"><thead><tr><th>#</th><th>Nome</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(data ?? []).length === 0 ? <tr><td colSpan={3}><EmptyState /></td></tr>
              : (data ?? []).map((t) => <tr key={t.id}><td>{t.id}</td><td className="font-medium">{t.nome}</td>
                <td className="text-right"><button onClick={() => setDel(t)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button></td></tr>)}
          </tbody>
        </table>
      </div>
      <Modal isOpen={show} onClose={() => setShow(false)} title="Novo Tipo de Documento" size="sm">
        <form onSubmit={handleSubmit((d) => createM.mutate(d))} className="space-y-4">
          <FormField label="Nome" required><input {...register('nome')} className="input" placeholder="NE, OB, RP…" /></FormField>
          <div className="flex justify-end"><button type="submit" disabled={createM.isPending} className="btn-primary">{createM.isPending ? <Spinner className="h-4 w-4" /> : 'Cadastrar'}</button></div>
        </form>
      </Modal>
      <ConfirmDialog isOpen={!!del} onClose={() => setDel(null)} onConfirm={() => del && deleteM.mutate(del.id)} message={`Excluir tipo "${del?.nome}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}

// ── Tipo de Impressora ─────────────────────────────────────────────────────────
function TiposImpressoraTab() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false)
  const [del, setDel] = useState<{ id: number; tipo: string } | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const { data, isLoading } = useQuery({ queryKey: ['tipos-impressora'], queryFn: tiposImpressoraApi.list })
  const { register, handleSubmit, reset } = useForm<{ tipo: string }>()
  const createM = useMutation({ mutationFn: tiposImpressoraApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tipos-impressora'] }); setShow(false); reset() }, onError: (e) => setErr(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: tiposImpressoraApi.remove, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tipos-impressora'] }); setDel(null) }, onError: (e) => setErr(getApiErrorMessage(e)) })
  if (isLoading) return <PageSpinner />
  return (
    <div className="space-y-4">
      {err && <AlertMessage type="error" message={err} onClose={() => setErr(null)} />}
      <div className="flex justify-end"><button className="btn-primary" onClick={() => setShow(true)}><Plus className="w-4 h-4" /> Novo</button></div>
      <div className="table-wrapper">
        <table className="table"><thead><tr><th>#</th><th>Tipo</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(data ?? []).length === 0 ? <tr><td colSpan={3}><EmptyState /></td></tr>
              : (data ?? []).map((t) => <tr key={t.id}><td>{t.id}</td><td className="font-medium">{t.tipo}</td>
                <td className="text-right"><button onClick={() => setDel(t)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button></td></tr>)}
          </tbody>
        </table>
      </div>
      <Modal isOpen={show} onClose={() => setShow(false)} title="Novo Tipo de Impressora" size="sm">
        <form onSubmit={handleSubmit((d) => createM.mutate(d))} className="space-y-4">
          <FormField label="Tipo" required><input {...register('tipo')} className="input" placeholder="Laser Monocromático A4" /></FormField>
          <div className="flex justify-end"><button type="submit" disabled={createM.isPending} className="btn-primary">{createM.isPending ? <Spinner className="h-4 w-4" /> : 'Cadastrar'}</button></div>
        </form>
      </Modal>
      <ConfirmDialog isOpen={!!del} onClose={() => setDel(null)} onConfirm={() => del && deleteM.mutate(del.id)} message={`Excluir tipo "${del?.tipo}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}

// ── Local de Impressora ───────────────────────────────────────────────────────
function LocaisTab() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false)
  const [del, setDel] = useState<{ id: number; setor: string } | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const { data, isLoading } = useQuery({ queryKey: ['locais-impressora'], queryFn: locaisImpressoraApi.list })
  const { register, handleSubmit, reset } = useForm<{ setor: string; descricao: string }>()
  const createM = useMutation({ mutationFn: locaisImpressoraApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['locais-impressora'] }); setShow(false); reset() }, onError: (e) => setErr(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: locaisImpressoraApi.remove, onSuccess: () => { qc.invalidateQueries({ queryKey: ['locais-impressora'] }); setDel(null) }, onError: (e) => setErr(getApiErrorMessage(e)) })
  if (isLoading) return <PageSpinner />
  return (
    <div className="space-y-4">
      {err && <AlertMessage type="error" message={err} onClose={() => setErr(null)} />}
      <div className="flex justify-end"><button className="btn-primary" onClick={() => setShow(true)}><Plus className="w-4 h-4" /> Novo</button></div>
      <div className="table-wrapper">
        <table className="table"><thead><tr><th>#</th><th>Setor</th><th>Descrição</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(data ?? []).length === 0 ? <tr><td colSpan={4}><EmptyState /></td></tr>
              : (data ?? []).map((l) => <tr key={l.id}><td>{l.id}</td><td className="font-medium">{l.setor}</td><td className="text-sm text-gray-600">{l.descricao}</td>
                <td className="text-right"><button onClick={() => setDel(l)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button></td></tr>)}
          </tbody>
        </table>
      </div>
      <Modal isOpen={show} onClose={() => setShow(false)} title="Novo Local" size="sm">
        <form onSubmit={handleSubmit((d) => createM.mutate(d))} className="space-y-4">
          <FormField label="Setor" required><input {...register('setor')} className="input" placeholder="SETIC" /></FormField>
          <FormField label="Descrição" required><input {...register('descricao')} className="input" placeholder="Sala de Servidores, 2º andar" /></FormField>
          <div className="flex justify-end"><button type="submit" disabled={createM.isPending} className="btn-primary">{createM.isPending ? <Spinner className="h-4 w-4" /> : 'Cadastrar'}</button></div>
        </form>
      </Modal>
      <ConfirmDialog isOpen={!!del} onClose={() => setDel(null)} onConfirm={() => del && deleteM.mutate(del.id)} message={`Excluir local "${del?.setor}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}

// ── Tipo de Impressão ─────────────────────────────────────────────────────────
function TiposImpressaoTab() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false)
  const [del, setDel] = useState<{ id: number; descricao: string } | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const { data, isLoading } = useQuery({ queryKey: ['tipos-impressao'], queryFn: tiposImpressaoApi.list })
  const { register, handleSubmit, reset } = useForm<{ descricao: string; franquia: number; valor_franquia: number; valor_extra_franquia: number }>()
  const createM = useMutation({ mutationFn: tiposImpressaoApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tipos-impressao'] }); setShow(false); reset() }, onError: (e) => setErr(getApiErrorMessage(e)) })
  const deleteM = useMutation({ mutationFn: tiposImpressaoApi.remove, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tipos-impressao'] }); setDel(null) }, onError: (e) => setErr(getApiErrorMessage(e)) })
  if (isLoading) return <PageSpinner />
  return (
    <div className="space-y-4">
      {err && <AlertMessage type="error" message={err} onClose={() => setErr(null)} />}
      <div className="flex justify-end"><button className="btn-primary" onClick={() => setShow(true)}><Plus className="w-4 h-4" /> Novo</button></div>
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Descrição</th><th className="text-right">Franquia (pág.)</th><th className="text-right">Valor Franquia</th><th className="text-right">Valor Extra</th><th className="text-right">Ações</th></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {(data ?? []).length === 0 ? <tr><td colSpan={5}><EmptyState /></td></tr>
              : (data ?? []).map((t) => <tr key={t.id}>
                <td className="font-medium">{t.descricao}</td>
                <td className="text-right font-mono">{t.franquia.toLocaleString('pt-BR')}</td>
                <td className="text-right text-emerald-700 font-semibold">{formatCurrency(t.valor_franquia)}</td>
                <td className="text-right text-amber-600">{formatCurrency(t.valor_extra_franquia)}/pág.</td>
                <td className="text-right"><button onClick={() => setDel(t)} className="btn btn-danger btn-sm"><Trash2 className="w-3.5 h-3.5" /></button></td>
              </tr>)}
          </tbody>
        </table>
      </div>
      <Modal isOpen={show} onClose={() => setShow(false)} title="Novo Tipo de Impressão" size="lg">
        <form onSubmit={handleSubmit((d) => createM.mutate(d))} className="space-y-4">
          <FormField label="Descrição" required><input {...register('descricao')} className="input" placeholder="Preto e Branco A4" /></FormField>
          <div className="grid grid-cols-3 gap-4">
            <FormField label="Franquia (páginas)" required><input {...register('franquia')} type="number" min={0} className="input" placeholder="5000" /></FormField>
            <FormField label="Valor Franquia (R$)" required><input {...register('valor_franquia')} type="number" step="0.01" min={0} className="input" placeholder="500.00" /></FormField>
            <FormField label="Valor Extra/pág. (R$)" required><input {...register('valor_extra_franquia')} type="number" step="0.0001" min={0} className="input" placeholder="0.05" /></FormField>
          </div>
          <div className="flex justify-end pt-2"><button type="submit" disabled={createM.isPending} className="btn-primary">{createM.isPending ? <Spinner className="h-4 w-4" /> : 'Cadastrar'}</button></div>
        </form>
      </Modal>
      <ConfirmDialog isOpen={!!del} onClose={() => setDel(null)} onConfirm={() => del && deleteM.mutate(del.id)} message={`Excluir tipo "${del?.descricao}"?`} isLoading={deleteM.isPending} />
    </div>
  )
}

// ── Página principal com abas ─────────────────────────────────────────────────
const ABAS = [
  { key: 'tipos-doc',        label: 'Tipos de Documento' },
  { key: 'tipos-impressora', label: 'Tipos de Impressora' },
  { key: 'locais',           label: 'Locais' },
  { key: 'tipos-impressao',  label: 'Tipos de Impressão' },
] as const

export default function TiposPage() {
  const [aba, setAba] = useState<typeof ABAS[number]['key']>('tipos-doc')
  return (
    <div>
      <PageHeader title="Tabelas de Domínio" subtitle="Configurações e tabelas auxiliares do sistema" />
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit flex-wrap">
        {ABAS.map(({ key, label }) => (
          <button key={key} onClick={() => setAba(key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${aba === key ? 'bg-white shadow text-fab-700' : 'text-gray-500 hover:text-gray-700'}`}>
            {label}
          </button>
        ))}
      </div>
      {aba === 'tipos-doc'        && <TiposDocTab />}
      {aba === 'tipos-impressora' && <TiposImpressoraTab />}
      {aba === 'locais'           && <LocaisTab />}
      {aba === 'tipos-impressao'  && <TiposImpressaoTab />}
    </div>
  )
}
