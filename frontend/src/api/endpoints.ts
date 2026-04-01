/**
 * api/endpoints.ts — Funções de chamada para cada endpoint da API.
 *
 * Organizado por entidade. Cada função corresponde a um endpoint REST.
 * Retornam os dados tipados diretamente (sem o envelope Axios).
 */

import api from './client'
import type {
  ComissaoForm, ComissaoOut,
  ContratoForm, ContratoOut,
  DocumentoContabilForm, DocumentoContabilOut,
  EmpresaForm, EmpresaOut,
  EvolucaoMensalItem,
  FaturaForm, FaturaOut,
  ImpressoraForm, ImpressoraOut,
  LeituraManualForm, LeituraOut, LeituraSNMPForm,
  LocalImpressoraForm, LocalImpressoraOut,
  MembroForm, MembroOut,
  RankingImpressora,
  RelatorioMensal, RelatorioTotal,
  SNMPResultado,
  TipoDocForm, TipoDocOut,
  TipoImpressaoForm, TipoImpressaoOut,
  TipoImpressoraForm, TipoImpressoraOut,
  TokenResponse, UserInfo,
} from '@/types'

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { username, password }).then(r => r.data),
  me: () =>
    api.get<UserInfo>('/auth/me').then(r => r.data),
}

// ── Membros ───────────────────────────────────────────────────────────────────

export const membrosApi = {
  list:   ()           => api.get<MembroOut[]>('/membros/').then(r => r.data),
  get:    (cpf: string) => api.get<MembroOut>(`/membros/${cpf}`).then(r => r.data),
  create: (d: MembroForm) => api.post<MembroOut>('/membros/', d).then(r => r.data),
  update: (cpf: string, d: Partial<MembroForm>) =>
    api.patch<MembroOut>(`/membros/${cpf}`, d).then(r => r.data),
  remove: (cpf: string) => api.delete(`/membros/${cpf}`),
}

// ── Empresas ──────────────────────────────────────────────────────────────────

export const empresasApi = {
  list:   ()             => api.get<EmpresaOut[]>('/empresas/').then(r => r.data),
  get:    (cnpj: string) => api.get<EmpresaOut>(`/empresas/${cnpj}`).then(r => r.data),
  create: (d: EmpresaForm) => api.post<EmpresaOut>('/empresas/', d).then(r => r.data),
  update: (cnpj: string, d: Partial<EmpresaForm>) =>
    api.patch<EmpresaOut>(`/empresas/${cnpj}`, d).then(r => r.data),
  remove: (cnpj: string) => api.delete(`/empresas/${cnpj}`),
}

// ── Comissões ─────────────────────────────────────────────────────────────────

export const comissoesApi = {
  list:   ()            => api.get<ComissaoOut[]>('/comissoes/').then(r => r.data),
  get:    (id: number)  => api.get<ComissaoOut>(`/comissoes/${id}`).then(r => r.data),
  create: (d: ComissaoForm) => api.post<ComissaoOut>('/comissoes/', d).then(r => r.data),
  update: (id: number, d: Partial<ComissaoForm>) =>
    api.patch<ComissaoOut>(`/comissoes/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/comissoes/${id}`),
  uploadDocumento: (id: number, file: File) => {
    const fd = new FormData()
    fd.append('arquivo', file)
    return api.post<ComissaoOut>(`/comissoes/${id}/documento`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}

// ── Contratos ─────────────────────────────────────────────────────────────────

export const contratosApi = {
  list:   ()           => api.get<ContratoOut[]>('/contratos/').then(r => r.data),
  get:    (id: number) => api.get<ContratoOut>(`/contratos/${id}`).then(r => r.data),
  create: (d: ContratoForm) => api.post<ContratoOut>('/contratos/', d).then(r => r.data),
  update: (id: number, d: Partial<ContratoForm>) =>
    api.patch<ContratoOut>(`/contratos/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/contratos/${id}`),
}

// ── Faturas ───────────────────────────────────────────────────────────────────

export const faturasApi = {
  list:   (contratoId?: number) =>
    api.get<FaturaOut[]>('/faturas/', { params: { contrato_id: contratoId } }).then(r => r.data),
  get:    (id: number) => api.get<FaturaOut>(`/faturas/${id}`).then(r => r.data),
  create: (d: FaturaForm) => api.post<FaturaOut>('/faturas/', d).then(r => r.data),
  update: (id: number, d: Partial<FaturaForm>) =>
    api.patch<FaturaOut>(`/faturas/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/faturas/${id}`),
}

// ── Tipos de Documento ────────────────────────────────────────────────────────

export const tiposDocApi = {
  list:   ()           => api.get<TipoDocOut[]>('/tipos-doc/').then(r => r.data),
  get:    (id: number) => api.get<TipoDocOut>(`/tipos-doc/${id}`).then(r => r.data),
  create: (d: TipoDocForm) => api.post<TipoDocOut>('/tipos-doc/', d).then(r => r.data),
  update: (id: number, d: Partial<TipoDocForm>) =>
    api.patch<TipoDocOut>(`/tipos-doc/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/tipos-doc/${id}`),
}

// ── Documentos Contábeis ──────────────────────────────────────────────────────

export const docsContabeisApi = {
  list:   (contratoId?: number) =>
    api.get<DocumentoContabilOut[]>('/documentos-contabeis/', { params: { contrato_id: contratoId } }).then(r => r.data),
  get:    (id: number) => api.get<DocumentoContabilOut>(`/documentos-contabeis/${id}`).then(r => r.data),
  create: (d: DocumentoContabilForm) => api.post<DocumentoContabilOut>('/documentos-contabeis/', d).then(r => r.data),
  update: (id: number, d: Partial<DocumentoContabilForm>) =>
    api.patch<DocumentoContabilOut>(`/documentos-contabeis/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/documentos-contabeis/${id}`),
}

// ── Tipos de Impressora ───────────────────────────────────────────────────────

export const tiposImpressoraApi = {
  list:   () => api.get<TipoImpressoraOut[]>('/tipos-impressora/').then(r => r.data),
  create: (d: TipoImpressoraForm) => api.post<TipoImpressoraOut>('/tipos-impressora/', d).then(r => r.data),
  update: (id: number, d: Partial<TipoImpressoraForm>) =>
    api.patch<TipoImpressoraOut>(`/tipos-impressora/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/tipos-impressora/${id}`),
}

// ── Locais de Impressora ──────────────────────────────────────────────────────

export const locaisImpressoraApi = {
  list:   () => api.get<LocalImpressoraOut[]>('/locais-impressora/').then(r => r.data),
  create: (d: LocalImpressoraForm) => api.post<LocalImpressoraOut>('/locais-impressora/', d).then(r => r.data),
  update: (id: number, d: Partial<LocalImpressoraForm>) =>
    api.patch<LocalImpressoraOut>(`/locais-impressora/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/locais-impressora/${id}`),
}

// ── Impressoras ───────────────────────────────────────────────────────────────

export const impressorasApi = {
  list:   (params?: { ativa?: boolean; local_id?: number }) =>
    api.get<ImpressoraOut[]>('/impressoras/', { params }).then(r => r.data),
  get:    (numSerie: string) => api.get<ImpressoraOut>(`/impressoras/${numSerie}`).then(r => r.data),
  create: (d: ImpressoraForm) => api.post<ImpressoraOut>('/impressoras/', d).then(r => r.data),
  update: (numSerie: string, d: Partial<ImpressoraForm>) =>
    api.patch<ImpressoraOut>(`/impressoras/${numSerie}`, d).then(r => r.data),
  remove: (numSerie: string) => api.delete(`/impressoras/${numSerie}`),
  lerSNMP: (numSerie: string) =>
    api.get<SNMPResultado>(`/impressoras/${numSerie}/snmp`).then(r => r.data),
}

// ── Tipos de Impressão ────────────────────────────────────────────────────────

export const tiposImpressaoApi = {
  list:   () => api.get<TipoImpressaoOut[]>('/tipos-impressao/').then(r => r.data),
  create: (d: TipoImpressaoForm) => api.post<TipoImpressaoOut>('/tipos-impressao/', d).then(r => r.data),
  update: (id: number, d: Partial<TipoImpressaoForm>) =>
    api.patch<TipoImpressaoOut>(`/tipos-impressao/${id}`, d).then(r => r.data),
  remove: (id: number) => api.delete(`/tipos-impressao/${id}`),
}

// ── Leituras ──────────────────────────────────────────────────────────────────

export const leiturasApi = {
  list: (params?: { impressora_num_serie?: string; mes_referencia?: number; ano_referencia?: number; manual?: boolean }) =>
    api.get<LeituraOut[]>('/leituras/', { params }).then(r => r.data),
  listByImpressora: (numSerie: string) =>
    api.get<LeituraOut[]>(`/leituras/impressora/${numSerie}`).then(r => r.data),
  get:          (id: number) => api.get<LeituraOut>(`/leituras/${id}`).then(r => r.data),
  createManual: (d: LeituraManualForm) => api.post<LeituraOut>('/leituras/', d).then(r => r.data),
  createSNMP:   (d: LeituraSNMPForm)   => api.post<LeituraOut>('/leituras/snmp', d).then(r => r.data),
  update:       (id: number, d: Partial<LeituraManualForm>) =>
    api.patch<LeituraOut>(`/leituras/${id}`, d).then(r => r.data),
  remove:       (id: number) => api.delete(`/leituras/${id}`),
}

// ── Relatórios ────────────────────────────────────────────────────────────────

export const relatoriosApi = {
  mensal: (contratoId: number, mes: number, ano: number) =>
    api.get<RelatorioMensal>(`/relatorios/mensal/${contratoId}`, { params: { mes, ano } }).then(r => r.data),
  total:    (contratoId: number) =>
    api.get<RelatorioTotal>(`/relatorios/total/${contratoId}`).then(r => r.data),
  evolucao: (contratoId: number) =>
    api.get<EvolucaoMensalItem[]>(`/relatorios/evolucao/${contratoId}`).then(r => r.data),
  ranking:  (contratoId: number) =>
    api.get<RankingImpressora[]>(`/relatorios/ranking/${contratoId}`).then(r => r.data),
  testarSNMP: (numSerie: string) =>
    api.get<{ acessivel: boolean; descricao?: string; erro?: string }>(
      `/relatorios/snmp-teste/${numSerie}`
    ).then(r => r.data),
}
