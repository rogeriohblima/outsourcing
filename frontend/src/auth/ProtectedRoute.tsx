/**
 * auth/ProtectedRoute.tsx — HOC que protege rotas autenticadas.
 *
 * Redireciona para /login se o usuário não estiver autenticado.
 * Exibe um spinner enquanto o estado de autenticação é verificado.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="spinner h-8 w-8 border-3 text-fab-600" />
          <p className="text-sm text-gray-500">Verificando autenticação…</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Salva a rota tentada para redirecionar após login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}
