/**
 * api/client.ts — Cliente HTTP centralizado (Axios).
 *
 * Em Docker: VITE_API_URL e vazio — usa /api/v1 (relativo).
 *   O Nginx faz proxy de /api/* para http://backend:8000.
 *
 * Em desenvolvimento local: VITE_API_URL=http://localhost:8000
 *   O Vite dev server faz proxy de /api/* para o backend.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Se VITE_API_URL estiver definido, usa ele. Caso contrario, usa caminho
// relativo (funciona tanto com Nginx proxy quanto com Vite dev proxy).
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

// Injeta JWT em todas as requisicoes
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

// Trata 401 globalmente
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api

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