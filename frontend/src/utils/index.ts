/**
 * utils/index.ts — Utilitários gerais do frontend.
 *
 * Funções de formatação, validação e transformação usadas em
 * múltiplos componentes. Importar via:
 *   import { formatCPF, formatCNPJ, calcularPorcentagem } from '@/utils'
 */

// ── Formatação de documentos ──────────────────────────────────────────────────

/**
 * Formata um CPF numérico (11 dígitos) para o padrão visual 000.000.000-00.
 * Aceita CPF com ou sem formatação e retorna formatado ou o original se inválido.
 */
export function formatCPF(cpf: string): string {
  const digits = cpf.replace(/\D/g, '')
  if (digits.length !== 11) return cpf
  return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
}

/**
 * Formata um CNPJ numérico (14 dígitos) para o padrão 00.000.000/0001-00.
 */
export function formatCNPJ(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '')
  if (digits.length !== 14) return cnpj
  return digits.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
}

// ── Formatação numérica e financeira ─────────────────────────────────────────

/**
 * Formata um número como moeda brasileira (R$).
 * Exemplo: formatBRL(1234.5) → "R$ 1.234,50"
 */
export function formatBRL(value: number | string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return 'R$ —'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(num)
}

/**
 * Formata um número como inteiro com separador de milhar.
 * Exemplo: formatInt(12345) → "12.345"
 */
export function formatInt(value: number): string {
  return new Intl.NumberFormat('pt-BR').format(value)
}

/**
 * Formata um percentual com N casas decimais.
 * Exemplo: formatPct(87.5) → "87,5%"
 */
export function formatPct(value: number, decimals = 1): string {
  return `${value.toFixed(decimals).replace('.', ',')}%`
}

// ── Formatação de datas ───────────────────────────────────────────────────────

/**
 * Nomes dos meses em português (índice 1..12).
 */
export const MESES_PT = [
  '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

export const MESES_ABREV = [
  '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez',
]

/**
 * Formata uma data ISO (YYYY-MM-DD) para DD/MM/YYYY.
 * Garante que não ocorra o problema de fuso horário ao usar new Date().
 */
export function formatData(dateStr: string): string {
  if (!dateStr) return '—'
  const [y, m, d] = dateStr.split('-')
  return `${d}/${m}/${y}`
}

/**
 * Formata um datetime ISO completo para DD/MM/YYYY HH:MM.
 */
export function formatDataHora(dateStr: string): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

/**
 * Retorna uma label de mês/ano no formato "Jan/2025".
 */
export function labelMesAno(mes: number, ano: number): string {
  return `${MESES_ABREV[mes]}/${ano}`
}

// ── Cálculos financeiros de contratos ────────────────────────────────────────

/**
 * Calcula o valor a pagar dado o número de páginas, franquia e tarifas.
 *
 * Modelo de preço: custo fixo (franquia) + variável por excedente.
 *
 * @param paginas            - Total de páginas impressas no período
 * @param franquia           - Quantidade de páginas inclusas no custo fixo
 * @param valorFranquia      - Custo fixo mensal (R$)
 * @param valorExtraFranquia - Custo por página acima da franquia (R$)
 *
 * @returns objeto com breakdowns financeiros
 */
export function calcularValorImpressao(
  paginas: number,
  franquia: number,
  valorFranquia: number,
  valorExtraFranquia: number,
) {
  const dentroDaFranquia = Math.min(paginas, franquia)
  const excedente        = Math.max(0, paginas - franquia)
  const valorExcedente   = excedente * valorExtraFranquia
  const valorTotal       = valorFranquia + valorExcedente

  return {
    dentroDaFranquia,
    excedente,
    valorFranquia,
    valorExcedente,
    valorTotal,
    percentualFranquiaUsada: franquia > 0 ? (dentroDaFranquia / franquia) * 100 : 0,
  }
}

/**
 * Calcula percentuais de tempo decorrido e orçamento consumido de um contrato.
 *
 * @param dataInicio   - Data de início do contrato (YYYY-MM-DD)
 * @param dataTermino  - Data de término do contrato (YYYY-MM-DD)
 * @param valorGasto   - Total consumido até o momento (R$)
 * @param valorTotal   - Total empenhado/orçado do contrato (R$)
 *
 * @returns percentuais (0–100) e número de dias
 */
export function calcularIndicadoresContrato(
  dataInicio: string,
  dataTermino: string,
  valorGasto: number,
  valorTotal: number,
) {
  const inicio  = new Date(dataInicio  + 'T00:00:00')
  const termino = new Date(dataTermino + 'T00:00:00')
  const hoje    = new Date()

  const diasTotais     = Math.max(1, Math.round((termino.getTime() - inicio.getTime()) / 86_400_000))
  const diasDecorridos = Math.max(0, Math.min(diasTotais, Math.round((hoje.getTime() - inicio.getTime()) / 86_400_000)))
  const pctTempo       = (diasDecorridos / diasTotais) * 100

  const pctOrcamento = valorTotal > 0 ? (valorGasto / valorTotal) * 100 : 0

  const vigente  = inicio <= hoje && hoje <= termino
  const encerrado = hoje > termino

  return {
    diasTotais,
    diasDecorridos,
    diasRestantes: Math.max(0, diasTotais - diasDecorridos),
    pctTempo:      Math.min(100, pctTempo),
    pctOrcamento:  Math.min(100, pctOrcamento),
    vigente,
    encerrado,
    aIniciar: hoje < inicio,
    saldoOrcamento: valorTotal - valorGasto,
  }
}

// ── Validações ────────────────────────────────────────────────────────────────

/** Valida CPF usando algoritmo de dígitos verificadores. */
export function validarCPF(cpf: string): boolean {
  const digits = cpf.replace(/\D/g, '')
  if (digits.length !== 11 || /^(\d)\1+$/.test(digits)) return false

  let soma = 0
  for (let i = 0; i < 9; i++) soma += parseInt(digits[i]) * (10 - i)
  let resto = (soma * 10) % 11
  if (resto === 10 || resto === 11) resto = 0
  if (resto !== parseInt(digits[9])) return false

  soma = 0
  for (let i = 0; i < 10; i++) soma += parseInt(digits[i]) * (11 - i)
  resto = (soma * 10) % 11
  if (resto === 10 || resto === 11) resto = 0
  return resto === parseInt(digits[10])
}

/** Valida CNPJ usando algoritmo de dígitos verificadores. */
export function validarCNPJ(cnpj: string): boolean {
  const digits = cnpj.replace(/\D/g, '')
  if (digits.length !== 14 || /^(\d)\1+$/.test(digits)) return false

  const calc = (d: string, weights: number[]) =>
    weights.reduce((acc, w, i) => acc + parseInt(d[i]) * w, 0)

  const mod = (n: number) => {
    const r = n % 11
    return r < 2 ? 0 : 11 - r
  }

  const w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  const w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

  return (
    mod(calc(digits, w1)) === parseInt(digits[12]) &&
    mod(calc(digits, w2)) === parseInt(digits[13])
  )
}

/** Valida se uma string é um endereço IPv4 válido. */
export function validarIPv4(ip: string): boolean {
  return /^(\d{1,3}\.){3}\d{1,3}$/.test(ip) &&
    ip.split('.').every((n) => parseInt(n) >= 0 && parseInt(n) <= 255)
}

// ── Cores dinâmicas por percentual ───────────────────────────────────────────

/**
 * Retorna uma classe Tailwind de cor baseada no percentual.
 * Usado para barras de progresso e KPIs.
 *
 * verde  → até 70%
 * amarelo → 70–90%
 * vermelho → acima de 90%
 */
export function corPorcentagem(pct: number): string {
  if (pct >= 90) return 'text-red-600'
  if (pct >= 70) return 'text-amber-500'
  return 'text-emerald-600'
}

export function corBarraPorcentagem(pct: number): string {
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 70) return 'bg-amber-400'
  return 'bg-emerald-500'
}

// ── Máscaras de input ─────────────────────────────────────────────────────────

/** Aplica máscara de CPF ao digitar: 000.000.000-00 */
export function mascaraCPF(value: string): string {
  return value
    .replace(/\D/g, '')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
    .slice(0, 14)
}

/** Aplica máscara de CNPJ ao digitar: 00.000.000/0001-00 */
export function mascaraCNPJ(value: string): string {
  return value
    .replace(/\D/g, '')
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2')
    .slice(0, 18)
}

// ── Truncamento de texto ──────────────────────────────────────────────────────

/** Trunca texto longo adicionando reticências. */
export function truncar(text: string, maxLen = 40): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen - 1) + '…'
}

// ── Ordenação ─────────────────────────────────────────────────────────────────

/** Compara dois valores para ordenação crescente. */
export function comparar<T>(a: T, b: T): number {
  if (a < b) return -1
  if (a > b) return 1
  return 0
}

/** Ordena array de objetos por campo string, case-insensitive. */
export function ordenarPor<T>(arr: T[], campo: keyof T): T[] {
  return [...arr].sort((a, b) =>
    String(a[campo]).localeCompare(String(b[campo]), 'pt-BR', { sensitivity: 'base' })
  )
}
