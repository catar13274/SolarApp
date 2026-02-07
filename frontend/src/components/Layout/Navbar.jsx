import { Menu } from 'lucide-react'

const Navbar = ({ toggleSidebar }) => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Toggle menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <h2 className="text-lg font-semibold text-gray-900">
            Solar Panel Management
          </h2>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {new Date().toLocaleDateString('ro-RO', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </span>
        </div>
      </div>
    </header>
  )
}

export default Navbar
