/**
 * components/layout/Layout.tsx — Layout principal com sidebar e header.
 *
 * Inclui:
 *  - Sidebar com menu de navegação agrupado por seção
 *  - Header com nome do usuário e botão de logout
 *  - Área de conteúdo principal (Outlet do React Router)
 *  - Responsivo: sidebar colapsável em mobile
 */

import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  BarChart2,
  BookOpen,
  Building2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  FileText,
  Home,
  LogOut,
  Menu,
  Printer,
  Settings,
  Shield,
  Users,
  X,
  Zap,
} from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { clsx } from 'clsx'

// ── Definição do menu ─────────────────────────────────────────────────────────

const menuGroups = [
  {
    label: 'Visão Geral',
    items: [
      { to: '/dashboard',   label: 'Dashboard',    icon: Home },
      { to: '/relatorios',  label: 'Relatórios',   icon: BarChart2 },
    ],
  },
  {
    label: 'Contrato',
    items: [
      { to: '/contratos',   label: 'Contratos',    icon: ClipboardList },
      { to: '/empresas',    label: 'Empresas',     icon: Building2 },
      { to: '/comissoes',   label: 'Comissões',    icon: Shield },
      { to: '/membros',     label: 'Membros',      icon: Users },
      { to: '/faturas',     label: 'Faturas',      icon: FileText },
      { to: '/documentos',  label: 'Doc. Contábeis', icon: BookOpen },
    ],
  },
  {
    label: 'Impressoras',
    items: [
      { to: '/impressoras', label: 'Impressoras',  icon: Printer },
      { to: '/leituras',    label: 'Leituras',     icon: Zap },
    ],
  },
  {
    label: 'Configurações',
    items: [
      { to: '/tipos',       label: 'Tabelas',      icon: Settings },
    ],
  },
]

// ── Componente ────────────────────────────────────────────────────────────────

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo / Título */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-fab-700">
        <div className="flex-shrink-0 w-8 h-8 bg-white rounded-lg flex items-center justify-center">
          <Printer className="w-5 h-5 text-fab-600" />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <p className="text-white font-bold text-sm">SCI</p>
            <p className="text-fab-300 text-xs">Contratos de Impressoras</p>
          </div>
        )}
      </div>

      {/* Navegação */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
        {menuGroups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="px-2 mb-1 text-fab-400 text-xs font-semibold uppercase tracking-wider">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map(({ to, label, icon: Icon }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      clsx(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                        isActive
                          ? 'bg-fab-700 text-white font-medium'
                          : 'text-fab-200 hover:bg-fab-700/50 hover:text-white',
                        collapsed && 'justify-center'
                      )
                    }
                    title={collapsed ? label : undefined}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {!collapsed && <span>{label}</span>}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer do sidebar: usuário e logout */}
      <div className="border-t border-fab-700 p-3">
        {!collapsed && (
          <div className="px-2 py-1 mb-2">
            <p className="text-white text-sm font-medium truncate">{user?.nome}</p>
            <p className="text-fab-400 text-xs truncate">{user?.username}</p>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={clsx(
            'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-fab-300',
            'hover:bg-red-700/30 hover:text-red-300 transition-colors text-sm',
            collapsed && 'justify-center'
          )}
          title="Sair"
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!collapsed && 'Sair'}
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar — Desktop */}
      <aside
        className={clsx(
          'hidden lg:flex flex-col bg-fab-600 transition-all duration-300',
          collapsed ? 'w-16' : 'w-60'
        )}
      >
        <SidebarContent />
        {/* Botão colapsar */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute left-0 top-1/2 -translate-y-1/2 bg-fab-700 text-white
                     rounded-r-full p-1.5 shadow-md hover:bg-fab-800 transition-colors z-10"
          style={{ left: collapsed ? '52px' : '228px' }}
          title={collapsed ? 'Expandir menu' : 'Recolher menu'}
        >
          {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
        </button>
      </aside>

      {/* Overlay + Sidebar — Mobile */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative z-50 w-64 bg-fab-600 flex flex-col">
            <button
              className="absolute top-3 right-3 text-fab-300 hover:text-white"
              onClick={() => setMobileOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Conteúdo principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header mobile */}
        <header className="lg:hidden flex items-center gap-3 bg-white border-b border-gray-200 px-4 py-3">
          <button
            onClick={() => setMobileOpen(true)}
            className="text-gray-500 hover:text-gray-700"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-bold text-fab-600 text-sm">SCI — Contratos de Impressoras</span>
        </header>

        {/* Área de página */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
