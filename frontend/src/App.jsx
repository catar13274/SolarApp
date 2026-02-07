import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import DashboardPage from './pages/DashboardPage'
import MaterialsPage from './pages/MaterialsPage'
import StockPage from './pages/StockPage'
import ProjectsPage from './pages/ProjectsPage'
import InvoicesPage from './pages/InvoicesPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/materials" element={<MaterialsPage />} />
        <Route path="/stock" element={<StockPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
      </Routes>
    </Layout>
  )
}

export default App
