/**
 * pages/contratos/FranquiasPage.tsx — Gestão de franquias e preços de um contrato.
 *
 * Exibido como modal/subpágina ao clicar em "Franquias" na listagem de contratos.
 * Permite:
 *  - Configurar franquia (total de páginas + custo fixo mensal) por tipo de impressão
 *  - Visualizar e registrar tabelas de preço com histórico de reajustes
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, RefreshCw, History, Trash2 } from 'lucide-react'
import { franquiasApi, tabelasPrecoApi, tiposImpressaoApi } from '@/api/endpoints'
import {
  AlertMessage, ConfirmDialog, EmptyState, FormField,
  Modal, PageSpinner, Spinner, formatCurrency, formatDate,
} from '@/components/common'
import { getApiErrorMessage } from '@/api/client'
import type { ContratoOut, FranquiaContratoOut, TabelaPrecoOut } from '@/types'

// ── Schemas ───────────────────────────────────────────────────────────────────

const franquiaSchema = z.object({
  tipo_impressao_id:    z.coerce.number().min(1, 'Selecione o tipo'),
  paginas_franquia:     z.coerce.number().min(1, 'Informe o total de páginas'),
  valor_mensal_franquia: z.coerce.number().min(0, 'Informe o valor mensal'),
})

const precoSchema = z.object({
  tipo_impressao_id:     z.coerce.number().min(1, 'Selecione o tipo'),
  valor_dentro_franquia: z.coerce.number().min(0),
  valor_fora_franquia:   z.coerce.number().min(0),
  vigente_de:            z.string().min(1, 'Informe a data de início'),
})

const reajusteSchema = z.object({
  tipo_impressao_id:     z.coerce.number().min(1, 'Selecione o tipo'),
  valor_dentro_franquia: z.coerce.number().min(0),
  valor_fora_franquia:   z.coerce.number().min(0),
  vigente_de:            z.string().min(1, 'Informe a data do reajuste'),
})

type FranquiaForm    = z.infer<typeof franquiaSchema>
type PrecoForm       = z.infer<typeof precoSchema>
type ReajusteForm    = z.infer<typeof reajusteSchema>

// ── Componente ────────────────────────────────────────────────────────────────

interface Props {
  contrato: ContratoOut
  onClose: () => void
}

export default function FranquiasPage({ contrato, onClose }: Props) {
  const qc = useQueryClient()
  const [showFranquia, setShowFranquia]   = useState(false)
  const [showPreco, setShowPreco]         = useState(false)
  const [showReajuste, setShowReajuste]   = useState(false)
  const [delFranquia, setDelFranquia]     = useState<FranquiaContratoOut | null>(null)
  const [apiError, setApiError]           = useState<string | null>(null)

  const { data: franquias, isLoading: loadF } = useQuery({
    queryKey: ['franquias', contrato.id],
    queryFn: () => franquiasApi.listByContrato(contrato.id),
  })
  const { data: tabelas, isLoading: loadT } = useQuery({
    queryKey: ['tabelas-preco', contrato.id],
    queryFn: () => tabelasPrecoApi.listByContrato(contrato.id),
  })
  const { data: tipos } = useQuery({
    queryKey: ['tipos-impressao'],
    queryFn: tiposImpressaoApi.list,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['franquias', contrato.id] })
    qc.invalidateQueries({ queryKey: ['tabelas-preco', contrato.id] })
  }

  const franquiaM = useMutation({
    mutationFn: (d: FranquiaForm) => franquiasApi.create({ ...d, contrato_id: contrato.id }),
    onSuccess: () => { invalidate(); setShowFranquia(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const delFranquiaM = useMutation({
    mutationFn: franquiasApi.remove,
    onSuccess: () => { invalidate(); setDelFranquia(null) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const precoM = useMutation({
    mutationFn: (d: PrecoForm) => tabelasPrecoApi.create({ ...d, contrato_id: contrato.id }),
    onSuccess: () => { invalidate(); setShowPreco(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })
  const reajusteM = useMutation({
    mutationFn: (d: ReajusteForm) => tabelasPrecoApi.reajustar(contrato.id, d),
    onSuccess: () => { invalidate(); setShowReajuste(false) },
    onError: (e) => setApiError(getApiErrorMessage(e)),
  })

  const { register: rF, handleSubmit: hsF, formState: { errors: eF } } =
    useForm<FranquiaForm>({ resolver: zodResolver(franquiaSchema) })
  const { register: rP, handleSubmit: hsP, formState: { errors: eP } } =
    useForm<PrecoForm>({ resolver: zodResolver(precoSchema) })
  const { register: rR, handleSubmit: hsR, formState: { errors: eR } } =
    useForm<ReajusteForm>({ resolver: zodResolver(reajusteSchema) })

  const precoAtual = (tabelas ?? []).filter(t => !t.vigente_ate)
  const historico  = (tabelas ?? []).filter(t => !!t.vigente_ate)

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Franquias e Preços</h2>
          <p className="text-sm text-gray-500">{contrato.numero} — {contrato.empresa.nome}</p>
        </div>
        <button onClick={onClose} className="btn-secondary btn-sm">Fechar</button>
      </div>

      {apiError && (
        <div className="mb-4">
          <AlertMessage type="error" message={apiError} onClose={() => setApiError(null)} />
        </div>
      )}

      {/* Info box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-800">
        <p className="font-semibold mb-1">Lógica de franquia contratual:</p>
        <ul className="space-y-1 list-disc list-inside text-blue-700">
          <li>A franquia é o <strong>total de páginas</strong> para toda a vigência ({contrato.data_inicio} → {contrato.data_termino})</li>
          <li>O custo fixo mensal é pago <strong>todo mês independente do uso</strong></li>
          <li>Páginas dentro da franquia: cobradas pelo valor unitário "dentro"</li>
          <li>Após esgotar a franquia: cobradas pelo valor unitário "fora" (maior)</li>
          <li>Reajustes criam novo registro preservando <strong>histórico imutável</strong></li>
        </ul>
      </div>

      {/* ── Franquias ── */}
      <div className="card mb-6">
        <div className="card-header">
          <h3 className="font-semibold text-gray-700">Franquias por Tipo de Impressão</h3>
          <button className="btn-primary btn-sm" onClick={() => { setApiError(null); setShowFranquia(true) }}>
            <Plus className="w-4 h-4" /> Configurar Franquia
          </button>
        </div>
        {loadF ? <PageSpinner /> : (franquias ?? []).length === 0 ? (
          <EmptyState message="Nenhuma franquia configurada para este contrato." />
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Tipo de Impressão</th>
                  <th className="text-right">Total de Páginas</th>
                  <th className="text-right">Custo Fixo Mensal</th>
                  <th className="text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(franquias ?? []).map(f => (
                  <tr key={f.id}>
                    <td className="font-medium">{f.tipo_impressao.descricao}</td>
                    <td className="text-right font-mono font-semibold text-fab-700">
                      {f.paginas_franquia.toLocaleString('pt-BR')} pág.
                    </td>
                    <td className="text-right font-semibold text-emerald-700">
                      {formatCurrency(f.valor_mensal_franquia)}/mês
                    </td>
                    <td className="text-right">
                      <button onClick={() => setDelFranquia(f)} className="btn btn-danger btn-sm">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Tabela de Preços Vigente ── */}
      <div className="card mb-4">
        <div className="card-header">
          <h3 className="font-semibold text-gray-700">Preços Vigentes</h3>
          <div className="flex gap-2">
            <button className="btn-secondary btn-sm" onClick={() => { setApiError(null); setShowPreco(true) }}>
              <Plus className="w-4 h-4" /> Preço Inicial
            </button>
            <button className="btn-primary btn-sm" onClick={() => { setApiError(null); setShowReajuste(true) }}>
              <RefreshCw className="w-4 h-4" /> Registrar Reajuste
            </button>
          </div>
        </div>
        {loadT ? <PageSpinner /> : precoAtual.length === 0 ? (
          <EmptyState message="Nenhum preço configurado. Clique em 'Preço Inicial' para configurar." />
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Tipo de Impressão</th>
                  <th className="text-right">Dentro da Franquia</th>
                  <th className="text-right">Fora da Franquia</th>
                  <th>Vigente desde</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {precoAtual.map(t => (
                  <tr key={t.id}>
                    <td className="font-medium">{t.tipo_impressao.descricao}</td>
                    <td className="text-right font-mono text-emerald-700">
                      {formatCurrency(t.valor_dentro_franquia)}/pág
                    </td>
                    <td className="text-right font-mono text-amber-600">
                      {formatCurrency(t.valor_fora_franquia)}/pág
                    </td>
                    <td><span className="badge-green">{formatDate(t.vigente_de)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Histórico de Preços ── */}
      {historico.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-gray-600 flex items-center gap-2">
              <History className="w-4 h-4" /> Histórico de Reajustes
            </h3>
            <span className="badge-gray">{historico.length} registro(s)</span>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th className="text-right">Dentro</th>
                  <th className="text-right">Fora</th>
                  <th>Vigência</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {historico.map(t => (
                  <tr key={t.id} className="opacity-70">
                    <td className="text-sm">{t.tipo_impressao.descricao}</td>
                    <td className="text-right font-mono text-sm">{formatCurrency(t.valor_dentro_franquia)}/pág</td>
                    <td className="text-right font-mono text-sm">{formatCurrency(t.valor_fora_franquia)}/pág</td>
                    <td className="text-xs text-gray-500">
                      {formatDate(t.vigente_de)} → {t.vigente_ate ? formatDate(t.vigente_ate) : 'atual'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal — Nova Franquia */}
      <Modal isOpen={showFranquia} onClose={() => setShowFranquia(false)}
        title="Configurar Franquia" size="md">
        <form onSubmit={hsF((d) => franquiaM.mutate(d))} className="space-y-4">
          <FormField label="Tipo de Impressão" error={eF.tipo_impressao_id?.message} required>
            <select {...rF('tipo_impressao_id')} className="input">
              <option value="">Selecione…</option>
              {tipos?.map(t => <option key={t.id} value={t.id}>{t.descricao}</option>)}
            </select>
          </FormField>
          <FormField label="Total de Páginas (vigência inteira do contrato)"
            error={eF.paginas_franquia?.message} required>
            <input {...rF('paginas_franquia')} type="number" min={1} className="input"
              placeholder="500000" />
          </FormField>
          <FormField label="Custo Fixo Mensal (R$)" error={eF.valor_mensal_franquia?.message} required>
            <input {...rF('valor_mensal_franquia')} type="number" step="0.01" min={0}
              className="input" placeholder="2000.00" />
          </FormField>
          <div className="flex justify-end pt-2">
            <button type="submit" disabled={franquiaM.isPending} className="btn-primary">
              {franquiaM.isPending ? <Spinner className="h-4 w-4" /> : 'Salvar'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal — Preço Inicial */}
      <Modal isOpen={showPreco} onClose={() => setShowPreco(false)}
        title="Cadastrar Preço Inicial" size="md">
        <form onSubmit={hsP((d) => precoM.mutate(d))} className="space-y-4">
          <FormField label="Tipo de Impressão" error={eP.tipo_impressao_id?.message} required>
            <select {...rP('tipo_impressao_id')} className="input">
              <option value="">Selecione…</option>
              {tipos?.map(t => <option key={t.id} value={t.id}>{t.descricao}</option>)}
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Valor dentro da franquia (R$/pág)" error={eP.valor_dentro_franquia?.message} required>
              <input {...rP('valor_dentro_franquia')} type="number" step="0.000001" min={0}
                className="input" placeholder="0.040" />
            </FormField>
            <FormField label="Valor fora da franquia (R$/pág)" error={eP.valor_fora_franquia?.message} required>
              <input {...rP('valor_fora_franquia')} type="number" step="0.000001" min={0}
                className="input" placeholder="0.080" />
            </FormField>
          </div>
          <FormField label="Vigente a partir de" error={eP.vigente_de?.message} required>
            <input {...rP('vigente_de')} type="date" className="input" />
          </FormField>
          <div className="flex justify-end pt-2">
            <button type="submit" disabled={precoM.isPending} className="btn-primary">
              {precoM.isPending ? <Spinner className="h-4 w-4" /> : 'Salvar'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal — Reajuste */}
      <Modal isOpen={showReajuste} onClose={() => setShowReajuste(false)}
        title="Registrar Reajuste de Preços" size="md">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-xs text-amber-800">
          O preço atual será fechado automaticamente. Cálculos anteriores ao reajuste
          continuarão usando o preço antigo (histórico imutável).
        </div>
        <form onSubmit={hsR((d) => reajusteM.mutate(d))} className="space-y-4">
          <FormField label="Tipo de Impressão" error={eR.tipo_impressao_id?.message} required>
            <select {...rR('tipo_impressao_id')} className="input">
              <option value="">Selecione…</option>
              {tipos?.map(t => <option key={t.id} value={t.id}>{t.descricao}</option>)}
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Novo valor dentro da franquia (R$/pág)" error={eR.valor_dentro_franquia?.message} required>
              <input {...rR('valor_dentro_franquia')} type="number" step="0.000001" min={0}
                className="input" placeholder="0.045" />
            </FormField>
            <FormField label="Novo valor fora da franquia (R$/pág)" error={eR.valor_fora_franquia?.message} required>
              <input {...rR('valor_fora_franquia')} type="number" step="0.000001" min={0}
                className="input" placeholder="0.090" />
            </FormField>
          </div>
          <FormField label="Data do reajuste (início da nova vigência)" error={eR.vigente_de?.message} required>
            <input {...rR('vigente_de')} type="date" className="input" />
          </FormField>
          <div className="flex justify-end pt-2">
            <button type="submit" disabled={reajusteM.isPending} className="btn-primary">
              {reajusteM.isPending ? <Spinner className="h-4 w-4" /> : 'Registrar Reajuste'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!delFranquia} onClose={() => setDelFranquia(null)}
        onConfirm={() => delFranquia && delFranquiaM.mutate(delFranquia.id)}
        message={`Excluir a franquia de "${delFranquia?.tipo_impressao.descricao}"? Isso afetará os cálculos dos relatórios.`}
        isLoading={delFranquiaM.isPending} />
    </div>
  )
}
