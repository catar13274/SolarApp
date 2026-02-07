import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Package, 
  Warehouse, 
  Briefcase, 
  FileText,
  Sun
} from 'lucide-react'

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/materials', icon: Package, label: 'Materials' },
    { to: '/stock', icon: Warehouse, label: 'Stock' },
    { to: '/projects', icon: Briefcase, label: 'Projects' },
    { to: '/invoices', icon: FileText, label: 'Invoices' },
  ]

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full bg-white border-r border-gray-200 z-30
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:z-0
          w-64
        `}
      >
        <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-200">
          <Sun className="h-8 w-8 text-primary-600" />
          <h1 className="text-xl font-bold text-gray-900">SolarApp</h1>
        </div>
        
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
              onClick={() => {
                if (window.innerWidth < 1024) {
                  toggleSidebar()
                }
              }}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}

export default Sidebar
