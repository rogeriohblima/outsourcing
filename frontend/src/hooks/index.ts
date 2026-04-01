/**
 * hooks/index.ts — Custom hooks que encapsulam as queries e mutations
 * mais usadas da aplicação, evitando repetição nos componentes.
 *
 * Cada hook retorna os dados tipados e estados de loading/error,
 * seguindo o padrão do TanStack Query v5.
 *
 * Uso:
 *   const { contratos, isLoading } = useContratos()
 *   const { criarMembro, isCreating } = useMembrosMutations()
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  contratosApi, empresasApi, impressorasApi,
  leiturasApi, membrosApi, relatoriosApi, tiposImpressaoApi,
} from '@/api/endpoints'
import type { LeituraManualForm, LeituraSNMPForm } from '@/types'

// ── Chaves de query (evita strings soltas espalhadas no código) ───────────────

export const QUERY_KEYS = {
  membros:        ['membros']     as const,
  empresas:       ['empresas']    as const,
  contratos:      ['contratos']   as const,
  comissoes:      ['comissoes']   as const,
  faturas:        (cid?: number) => ['faturas', cid] as const,
  docsContabeis:  (cid?: number) => ['docs-contabeis', cid] as const,
  impressoras:    (params?: object) => ['impressoras', params] as const,
  tiposImpressao: ['tipos-impressao'] as const,
  tiposImpressora:['tipos-impressora'] as const,
  locais:         ['locais-impressora'] as const,
  tiposDoc:       ['tipos-doc'] as const,
  leituras:       (params?: object) => ['leituras', params] as const,
  relMensal:      (cid: number, m: number, a: number) => ['relatorio-mensal', cid, m, a] as const,
  relTotal:       (cid: number) => ['relatorio-total', cid] as const,
  evolucao:       (cid: number) => ['evolucao', cid] as const,
  ranking:        (cid: number) => ['ranking', cid] as const,
} as const

// ── Contratos ─────────────────────────────────────────────────────────────────

/**
 * Retorna todos os contratos e indica quais estão em vigência hoje.
 */
export function useContratos() {
  const hoje = new Date()
  const query = useQuery({
    queryKey: QUERY_KEYS.contratos,
    queryFn: contratosApi.list,
  })
  const contratosAtivos = (query.data ?? []).filter(
    (c) => new Date(c.data_inicio) <= hoje && new Date(c.data_termino) >= hoje
  )
  return { ...query, contratos: query.data ?? [], contratosAtivos }
}

// ── Impressoras ───────────────────────────────────────────────────────────────

/**
 * Retorna impressoras com filtros opcionais.
 * @param params.ativa  - filtra por status ativo/inativo
 * @param params.local_id - filtra por local
 */
export function useImpressoras(params?: { ativa?: boolean; local_id?: number }) {
  const query = useQuery({
    queryKey: QUERY_KEYS.impressoras(params),
    queryFn: () => impressorasApi.list(params),
  })
  return { ...query, impressoras: query.data ?? [] }
}

/**
 * Retorna apenas impressoras ativas (atalho comum).
 */
export function useImpressorasAtivas() {
  return useImpressoras({ ativa: true })
}

// ── Tipos de Impressão ────────────────────────────────────────────────────────

/**
 * Retorna todos os tipos de impressão cadastrados.
 */
export function useTiposImpressao() {
  const query = useQuery({
    queryKey: QUERY_KEYS.tiposImpressao,
    queryFn: tiposImpressaoApi.list,
  })
  return { ...query, tiposImpressao: query.data ?? [] }
}

// ── Leituras ──────────────────────────────────────────────────────────────────

/**
 * Retorna leituras filtradas por mês/ano de referência.
 */
export function useLeiturasMes(mes: number, ano: number) {
  const query = useQuery({
    queryKey: QUERY_KEYS.leituras({ mes_referencia: mes, ano_referencia: ano }),
    queryFn: () => leiturasApi.list({ mes_referencia: mes, ano_referencia: ano }),
  })
  return { ...query, leituras: query.data ?? [] }
}

/**
 * Mutations para criação de leituras (manual e SNMP).
 * Invalida automaticamente as queries de leituras após sucesso.
 */
export function useLeiturasCreate(options?: {
  onManualSuccess?: (data: ReturnType<typeof leiturasApi.createManual> extends Promise<infer T> ? T : never) => void
  onSNMPSuccess?:   (data: ReturnType<typeof leiturasApi.createSNMP>   extends Promise<infer T> ? T : never) => void
  onError?:         (err: unknown) => void
}) {
  const qc = useQueryClient()

  const invalidateLeituras = () => {
    qc.invalidateQueries({ queryKey: ['leituras'] })
  }

  const createManual = useMutation({
    mutationFn: (data: LeituraManualForm) => leiturasApi.createManual(data),
    onSuccess: (data) => {
      invalidateLeituras()
      options?.onManualSuccess?.(data as any)
    },
    onError: options?.onError,
  })

  const createSNMP = useMutation({
    mutationFn: (data: LeituraSNMPForm) => leiturasApi.createSNMP(data),
    onSuccess: (data) => {
      invalidateLeituras()
      options?.onSNMPSuccess?.(data as any)
    },
    onError: options?.onError,
  })

  return {
    createManual: createManual.mutate,
    createSNMP:   createSNMP.mutate,
    isCreatingManual: createManual.isPending,
    isCreatingSNMP:   createSNMP.isPending,
    isCreating: createManual.isPending || createSNMP.isPending,
  }
}

// ── Relatórios ────────────────────────────────────────────────────────────────

/**
 * Retorna o relatório mensal de um contrato.
 * A query só é executada quando contratoId, mes e ano são fornecidos.
 */
export function useRelatorioMensal(contratoId: number | null, mes: number, ano: number) {
  return useQuery({
    queryKey: QUERY_KEYS.relMensal(contratoId!, mes, ano),
    queryFn:  () => relatoriosApi.mensal(contratoId!, mes, ano),
    enabled:  !!contratoId,
  })
}

/**
 * Retorna o relatório total (consolidado) de um contrato.
 */
export function useRelatorioTotal(contratoId: number | null) {
  return useQuery({
    queryKey: QUERY_KEYS.relTotal(contratoId!),
    queryFn:  () => relatoriosApi.total(contratoId!),
    enabled:  !!contratoId,
  })
}

/**
 * Retorna a série de evolução mensal para gráficos.
 */
export function useEvolucaoMensal(contratoId: number | null) {
  return useQuery({
    queryKey: QUERY_KEYS.evolucao(contratoId!),
    queryFn:  () => relatoriosApi.evolucao(contratoId!),
    enabled:  !!contratoId,
  })
}

/**
 * Retorna o ranking de impressoras por volume.
 */
export function useRankingImpressoras(contratoId: number | null) {
  return useQuery({
    queryKey: QUERY_KEYS.ranking(contratoId!),
    queryFn:  () => relatoriosApi.ranking(contratoId!),
    enabled:  !!contratoId,
  })
}

// ── Membros e Empresas ────────────────────────────────────────────────────────

/** Retorna lista de membros (para selects de comissões). */
export function useMembros() {
  const query = useQuery({ queryKey: QUERY_KEYS.membros, queryFn: membrosApi.list })
  return { ...query, membros: query.data ?? [] }
}

/** Retorna lista de empresas (para selects de contratos). */
export function useEmpresas() {
  const query = useQuery({ queryKey: QUERY_KEYS.empresas, queryFn: empresasApi.list })
  return { ...query, empresas: query.data ?? [] }
}
