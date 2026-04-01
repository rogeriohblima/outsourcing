/**
 * api/client.ts — Cliente HTTP centralizado (Axios).
 *
 * Responsabilidades:
 *  - Define a baseURL a partir da variável de ambiente VITE_API_URL
 *  - Interceptor de request: injeta o Bearer token JWT em toda requisição
 *  - Interceptor de response: trata 401 (redireciona para login) e
 *    normaliza mensagens de erro da API
 *
 * Uso:
 *   import api from '@/api/client'
 *   const data = await api.get('/membros/')
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000, // 30 segundos (SNMP pode demorar)
})

// ── Interceptor de Request: injeta JWT ───────────────────────────────────────

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Interceptor de Response: trata erros globais ─────────────────────────────

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expirado ou inválido — limpa storage e redireciona para login
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api

// ── Helpers de extração de mensagem de erro ───────────────────────────────────

/**
 * Extrai uma mensagem de erro legível de uma resposta da API.
 * A API pode retornar string simples ou array de erros Pydantic.
 */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((e) => e.msg || JSON.stringify(e)).join('; ')
    }
    if (error.message) return error.message
  }
  return 'Erro desconhecido. Tente novamente.'
}
