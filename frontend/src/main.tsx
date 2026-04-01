/**
 * main.tsx — Ponto de entrada da aplicação React.
 *
 * Configura:
 *  - QueryClientProvider (TanStack Query) para cache e gerenciamento de estado remoto
 *  - AuthProvider para contexto de autenticação JWT
 *  - BrowserRouter para roteamento SPA
 *  - Estilos globais do Tailwind
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import { AuthProvider } from './auth/AuthContext'
import './index.css'

/** Cliente global do TanStack Query com configurações padrão */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60 * 5, // 5 minutos em cache
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>,
)
