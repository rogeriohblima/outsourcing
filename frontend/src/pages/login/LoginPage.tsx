/**
 * pages/login/LoginPage.tsx — Página de login via Active Directory.
 *
 * Formulário com username e password. Ao submeter, chama o AuthContext
 * que faz a requisição ao backend (que valida no AD) e armazena o JWT.
 */

import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Lock, User, Printer } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { getApiErrorMessage } from '@/api/client'
import { AlertMessage, Spinner } from '@/components/common'

const loginSchema = z.object({
  username: z.string().min(1, 'Informe o usuário de rede'),
  password: z.string().min(1, 'Informe a senha'),
})

type LoginFormData = z.infer<typeof loginSchema>

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [apiError, setApiError] = useState<string | null>(null)

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard'

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (data: LoginFormData) => {
    setApiError(null)
    try {
      await login(data.username, data.password)
      navigate(from, { replace: true })
    } catch (err) {
      setApiError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-fab-700 to-fab-900 p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <Printer className="w-8 h-8 text-fab-600" />
          </div>
          <h1 className="text-white text-2xl font-bold">SCI</h1>
          <p className="text-fab-300 text-sm mt-1">Sistema de Contratos de Impressoras</p>
          <p className="text-fab-400 text-xs mt-1">Organização Militar da Aeronáutica</p>
        </div>

        {/* Card de login */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-gray-800 font-semibold text-lg mb-1">Acesso ao Sistema</h2>
          <p className="text-gray-500 text-xs mb-6">Use seu login de rede (Active Directory)</p>

          {apiError && (
            <div className="mb-4">
              <AlertMessage
                type="error"
                message={apiError}
                onClose={() => setApiError(null)}
              />
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Usuário */}
            <div>
              <label className="label">Usuário de rede</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  {...register('username')}
                  type="text"
                  autoComplete="username"
                  placeholder="fulano.silva"
                  className={`input pl-9 ${errors.username ? 'input-error' : ''}`}
                />
              </div>
              {errors.username && <p className="field-error">{errors.username.message}</p>}
            </div>

            {/* Senha */}
            <div>
              <label className="label">Senha</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  {...register('password')}
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={`input pl-9 ${errors.password ? 'input-error' : ''}`}
                />
              </div>
              {errors.password && <p className="field-error">{errors.password.message}</p>}
            </div>

            {/* Botão */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full justify-center py-2.5"
            >
              {isSubmitting ? (
                <>
                  <Spinner className="h-4 w-4" />
                  Autenticando…
                </>
              ) : (
                'Entrar'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-gray-400">
            Em caso de problemas de acesso, contate o SETIC.
          </p>
        </div>
      </div>
    </div>
  )
}
