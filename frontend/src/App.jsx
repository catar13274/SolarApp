import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import LoginPage from './pages/LoginPage'
import { useAuth } from './context/AuthContext'
import DashboardPage from './pages/DashboardPage'
import MaterialsPage from './pages/MaterialsPage'
import StockPage from './pages/StockPage'
import ProjectsPage from './pages/ProjectsPage'
import InvoicesPage from './pages/InvoicesPage'
import PurchaseDetailsPage from './pages/PurchaseDetailsPage'

function App() {
  const { isAuthenticated, loading, user, logout } = useAuth()

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <Layout user={user} onLogout={logout}>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/materials" element={<MaterialsPage />} />
        <Route path="/stock" element={<StockPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/purchases/:id" element={<PurchaseDetailsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
