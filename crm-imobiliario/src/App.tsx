import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import { PrivateRoute } from './components/PrivateRoute'
import { AppLayout } from './components/AppLayout'

// Auth pages
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage'

// App pages
import { ProfilePage } from './pages/profile/ProfilePage'
import { UsersPage } from './pages/admin/UsersPage'
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { KanbanPage } from './pages/kanban/KanbanPage'
import { PesquisaPage } from './pages/pesquisa/PesquisaPage'
import { ContatosPage } from './pages/contatos/ContatosPage'
import { AutomacoesPage } from './pages/automacoes/AutomacoesPage'

// Placeholder pages (serão implementados nos próximos módulos)
const ComingSoon = ({ title }: { title: string }) => (
  <div style={{ padding: '2rem', textAlign: 'center' }}>
    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚧</div>
    <h2 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>{title}</h2>
    <p style={{ color: 'var(--text-muted)' }}>Este módulo será implementado em breve</p>
  </div>
)

function HomeRedirect() {
  return <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              fontFamily: 'Inter, sans-serif',
              fontSize: '0.9rem',
            },
          }}
        />
        <Routes>
          {/* ── Rotas públicas ── */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          {/* ── Rotas protegidas ── */}
          <Route path="/" element={
            <PrivateRoute>
              <AppLayout>
                <HomeRedirect />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/dashboard" element={
            <PrivateRoute>
              <AppLayout>
                <DashboardPage />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/kanban" element={
            <PrivateRoute>
              <AppLayout>
                <KanbanPage />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/pesquisa" element={
            <PrivateRoute>
              <AppLayout>
                <PesquisaPage />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/contatos" element={
            <PrivateRoute>
              <AppLayout>
                <ContatosPage />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/mapa" element={
            <PrivateRoute>
              <AppLayout>
                <ComingSoon title="Mapa de Imóveis" />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/automacoes" element={
            <PrivateRoute>
              <AppLayout>
                <AutomacoesPage />
              </AppLayout>
            </PrivateRoute>
          } />

          <Route path="/profile" element={
            <PrivateRoute>
              <AppLayout>
                <ProfilePage />
              </AppLayout>
            </PrivateRoute>
          } />

          {/* ── Admin only ── */}
          <Route path="/admin/users" element={
            <PrivateRoute allowedRoles={['admin']}>
              <AppLayout>
                <UsersPage />
              </AppLayout>
            </PrivateRoute>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
