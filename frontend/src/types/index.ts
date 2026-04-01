/**
 * types/index.ts — Tipos TypeScript que espelham os schemas Pydantic do backend.
 *
 * Convenção de nomenclatura:
 *  - Interfaces com sufixo "Out" = dados retornados pela API
 *  - Tipos com sufixo "Form"    = dados dos formulários (antes de enviar)
 */

// ── Autenticação ─────────────────────────────────────────────────────────────

export interface LoginForm {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  username: string
  nome: string
  grupos: string[]
}

// ── Membro ────────────────────────────────────────────────────────────────────

export interface MembroOut {
  cpf: string
  nome: string
  criado_em: string
}

export interface MembroForm {
  cpf: string
  nome: string
}

// ── Empresa ───────────────────────────────────────────────────────────────────

export interface EmpresaOut {
  cnpj: string
  nome: string
  criado_em: string
}

export interface EmpresaForm {
  cnpj: string
  nome: string
}

// ── Comissão ──────────────────────────────────────────────────────────────────

export interface ComissaoOut {
  id: number
  presidente_cpf: string
  presidente: MembroOut
  fiscais: MembroOut[]
  documento_numero: string
  documento_data: string
  documento_path?: string
  criado_em: string
}

export interface ComissaoForm {
  presidente_cpf: string
  fiscais_cpf: string[]
  documento_numero: string
  documento_data: string
}

// ── Contrato ──────────────────────────────────────────────────────────────────

export interface ContratoResumo {
  id: number
  numero: string
  empresa: EmpresaOut
  data_inicio: string
  data_termino: string
}

export interface ContratoOut {
  id: number
  numero: string
  empresa_cnpj: string
  empresa: EmpresaOut
  data_inicio: string
  data_termino: string
  comissao_id: number
  comissao: ComissaoOut
  numero_processo: string
  criado_em: string
}

export interface ContratoForm {
  numero: string
  empresa_cnpj: string
  data_inicio: string
  data_termino: string
  comissao_id: number
  numero_processo: string
}

// ── Fatura ────────────────────────────────────────────────────────────────────

export interface FaturaOut {
  id: number
  numero: string
  data: string
  contrato_id: number
  contrato: ContratoResumo
  criado_em: string
}

export interface FaturaForm {
  numero: string
  data: string
  contrato_id: number
}

// ── Tipo de Documento ─────────────────────────────────────────────────────────

export interface TipoDocOut {
  id: number
  nome: string
}

export interface TipoDocForm {
  nome: string
}

// ── Documento Contábil ────────────────────────────────────────────────────────

export interface DocumentoContabilOut {
  id: number
  numero: string
  tipo_documento_id: number
  tipo_documento: TipoDocOut
  contrato_id: number
  contrato: ContratoResumo
  valor: number
  criado_em: string
}

export interface DocumentoContabilForm {
  numero: string
  tipo_documento_id: number
  contrato_id: number
  valor: number
}

// ── Tipo de Impressora ────────────────────────────────────────────────────────

export interface TipoImpressoraOut {
  id: number
  tipo: string
}

export interface TipoImpressoraForm {
  tipo: string
}

// ── Local de Impressora ───────────────────────────────────────────────────────

export interface LocalImpressoraOut {
  id: number
  setor: string
  descricao: string
}

export interface LocalImpressoraForm {
  setor: string
  descricao: string
}

// ── Impressora ────────────────────────────────────────────────────────────────

export interface ImpressoraOut {
  num_serie: string
  nome: string
  tipo_id: number
  tipo: TipoImpressoraOut
  local_id: number
  local: LocalImpressoraOut
  ip?: string
  ativa: boolean
  criado_em: string
}

export interface ImpressoraForm {
  num_serie: string
  nome: string
  tipo_id: number
  local_id: number
  ip?: string
  ativa: boolean
}

// ── Tipo de Impressão ─────────────────────────────────────────────────────────

export interface TipoImpressaoOut {
  id: number
  descricao: string
  franquia: number
  valor_franquia: number
  valor_extra_franquia: number
}

export interface TipoImpressaoForm {
  descricao: string
  franquia: number
  valor_franquia: number
  valor_extra_franquia: number
}

// ── Leitura ───────────────────────────────────────────────────────────────────

export interface LeituraOut {
  id: number
  impressora_num_serie: string
  impressora: ImpressoraOut
  tipo_impressao_id: number
  tipo_impressao: TipoImpressaoOut
  contador: number
  data: string
  mes_referencia: number
  ano_referencia: number
  manual: boolean
  observacao?: string
  criado_em: string
}

export interface LeituraManualForm {
  impressora_num_serie: string
  tipo_impressao_id: number
  contador: number
  data: string
  mes_referencia: number
  ano_referencia: number
  observacao?: string
}

export interface LeituraSNMPForm {
  impressora_num_serie: string
  tipo_impressao_id: number
  mes_referencia: number
  ano_referencia: number
}

export interface SNMPResultado {
  sucesso: boolean
  contador?: number
  oid_usado?: string
  erro?: string
}

// ── Relatórios ────────────────────────────────────────────────────────────────

export interface RelatorioMensalItem {
  impressora_num_serie: string
  impressora_nome: string
  setor: string
  tipo_impressao: string
  mes: number
  ano: number
  contador_inicial: number
  contador_final: number
  paginas_impressas: number
  franquia: number
  paginas_dentro_franquia: number
  paginas_excedente: number
  valor_franquia: number
  valor_excedente: number
  valor_total: number
}

export interface RelatorioMensal {
  contrato_numero: string
  empresa_nome: string
  mes: number
  ano: number
  itens: RelatorioMensalItem[]
  total_paginas: number
  total_valor: number
  percentual_orcamento?: number
  percentual_tempo?: number
}

export interface RelatorioTotalItem {
  tipo_impressao: string
  total_paginas: number
  total_valor: number
}

export interface RelatorioTotal {
  contrato_numero: string
  empresa_nome: string
  data_inicio: string
  data_termino: string
  numero_processo: string
  itens: RelatorioTotalItem[]
  total_geral_paginas: number
  total_geral_valor: number
  total_empenhado: number
  percentual_orcamento_consumido: number
  percentual_tempo_decorrido: number
  dias_decorridos: number
  dias_totais: number
  meses_com_leitura: number
  impressoras_ativas: number
}

export interface EvolucaoMensalItem {
  mes: number
  ano: number
  label: string
  total_paginas: number
  total_valor: number
}

export interface RankingImpressora {
  posicao: number
  num_serie: string
  nome: string
  setor: string
  total_paginas: number
  total_valor: number
}

// ── Utilitários ───────────────────────────────────────────────────────────────

/** Resposta de erro padrão da API */
export interface ApiError {
  detail: string | { msg: string; loc: string[] }[]
}

/** Parâmetros de paginação */
export interface PaginationParams {
  skip?: number
  limit?: number
}
