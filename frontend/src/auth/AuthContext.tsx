/**
 * auth/AuthContext.tsx — Contexto de autenticação global.
 *
 * Armazena o token JWT e as informações do usuário no localStorage.
 * Expõe as funções login() e logout() e o estado de autenticação.
 *
 * Uso:
 *   const { user, login, logout, isAuthenticated } = useAuth()
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { authApi } from '@/api/endpoints'
import type { UserInfo } from '@/types'

// ── Tipos do contexto ─────────────────────────────────────────────────────────

interface AuthContextValue {
  user: UserInfo | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true) // true até verificar token salvo

  /** Restaura sessão do localStorage ao carregar a página */
  useEffect(() => {
    const savedUser = localStorage.getItem('user_info')
    const token = localStorage.getItem('access_token')
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser))
      } catch {
        localStorage.removeItem('user_info')
        localStorage.removeItem('access_token')
      }
    }
    setIsLoading(false)
  }, [])

  /** Autentica o usuário via API e armazena o token */
  const login = useCallback(async (username: string, password: string) => {
    const tokenData = await authApi.login(username, password)
    localStorage.setItem('access_token', tokenData.access_token)

    // Busca dados completos do usuário com o token recém-obtido
    const userInfo = await authApi.me()
    localStorage.setItem('user_info', JSON.stringify(userInfo))
    setUser(userInfo)
  }, [])

  /** Remove a sessão e redireciona para login */
  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>')
  return ctx
}
