import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/layout/ProtectedRoute'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import Teams from './pages/Teams'
import TeamDetail from './pages/TeamDetail'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import Library from './pages/Library'
import TemplateDetail from './pages/TemplateDetail'
import TermsOfService from './pages/TermsOfService'
import PrivacyPolicy from './pages/PrivacyPolicy'
import ProfileSettings from './pages/ProfileSettings'
import CookieBanner from './components/common/CookieBanner'
import { Toaster } from '@/components/ui/sonner'

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <Router>
        <AuthProvider>
          <Toaster />
          <CookieBanner />
          <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/terms-of-service" element={<TermsOfService />} />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route
            path="/"
            element={<Navigate to="/projects" replace />}
          />
          <Route
            path="/teams"
            element={
              <ProtectedRoute>
                <Teams />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teams/:teamId"
            element={
              <ProtectedRoute>
                <TeamDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <Projects />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/documents/:documentId"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library"
            element={<Navigate to="/library/categories" replace />}
          />
          <Route
            path="/library/categories"
            element={
              <ProtectedRoute>
                <Library />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library/categories/:categoryId"
            element={
              <ProtectedRoute>
                <Library />
              </ProtectedRoute>
            }
          />
          <Route
            path="/library/templates/:templateId"
            element={
              <ProtectedRoute>
                <TemplateDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/profile"
            element={
              <ProtectedRoute>
                <ProfileSettings />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
    </ThemeProvider>
  )
}

export default App
