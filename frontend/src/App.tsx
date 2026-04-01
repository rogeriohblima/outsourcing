/**
 * App.tsx — Roteamento principal da aplicação.
 *
 * Estrutura de rotas:
 *   /login              → Página de login (pública)
 *   /                   → Layout principal (protegido)
 *     dashboard         → Dashboard / resumo
 *     membros           → CRUD de Membros
 *     empresas          → CRUD de Empresas
 *     comissoes         → CRUD de Comissões
 *     contratos         → CRUD de Contratos
 *     faturas           → CRUD de Faturas
 *     documentos        → CRUD de Documentos Contábeis
 *     impressoras       → CRUD de Impressoras
 *     leituras          → CRUD de Leituras
 *     tipos/*           → CRUD das tabelas de domínio
 *     relatorios        → Relatórios e gráficos
 */

import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './auth/ProtectedRoute'
import Layout from './components/layout/Layout'

// Páginas (lazy imports para code splitting)
import LoginPage from './pages/login/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import MembrosPage from './pages/membros/MembrosPage'
import EmpresasPage from './pages/empresas/EmpresasPage'
import ComissoesPage from './pages/comissoes/ComissoesPage'
import ContratosPage from './pages/contratos/ContratosPage'
import FaturasPage from './pages/faturas/FaturasPage'
import DocumentosPage from './pages/documentos/DocumentosPage'
import ImpressorasPage from './pages/impressoras/ImpressorasPage'
import LeiturasPage from './pages/leituras/LeiturasPage'
import RelatoriosPage from './pages/relatorios/RelatoriosPage'
import TiposPage from './pages/tipos/TiposPage'

export default function App() {
  return (
    <Routes>
      {/* Rota pública */}
      <Route path="/login" element={<LoginPage />} />

      {/* Rotas protegidas — envolvidas pelo Layout */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"    element={<DashboardPage />} />
          <Route path="membros"      element={<MembrosPage />} />
          <Route path="empresas"     element={<EmpresasPage />} />
          <Route path="comissoes"    element={<ComissoesPage />} />
          <Route path="contratos"    element={<ContratosPage />} />
          <Route path="faturas"      element={<FaturasPage />} />
          <Route path="documentos"   element={<DocumentosPage />} />
          <Route path="impressoras"  element={<ImpressorasPage />} />
          <Route path="leituras"     element={<LeiturasPage />} />
          <Route path="relatorios"   element={<RelatoriosPage />} />
          <Route path="tipos"        element={<TiposPage />} />
          {/* Redireciona rotas desconhecidas para dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Route>
    </Routes>
  )
}
