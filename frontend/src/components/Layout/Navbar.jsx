import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Menu } from 'lucide-react'
import { companies as companiesApi } from '../../services/api'
import { useCompanyScope } from '../../hooks/useCompanyScope'

const Navbar = ({ toggleSidebar }) => {
  const [tenantCode, setTenantCode] = useCompanyScope()
  const { data: firmList } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesApi.getAll().then((r) => r.data),
  })

  useEffect(() => {
    if (!tenantCode && firmList?.length) {
      setTenantCode(firmList[0].code)
    }
  }, [tenantCode, firmList, setTenantCode])

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            type="button"
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

        <div className="flex flex-wrap items-center gap-4">
          <label className="flex flex-wrap items-center gap-2 text-sm text-gray-700">
            <span className="font-medium whitespace-nowrap">Firma activă</span>
            <select
              value={tenantCode}
              onChange={(e) => setTenantCode(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 min-w-[200px] max-w-[280px]"
              title="Întregul conținut (materiale, stoc, proiecte etc.) vine din baza acestei firme."
            >
              <option value="">— Selectați firma —</option>
              {(firmList || []).map((c) => (
                <option key={c.id} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <span className="text-sm text-gray-600">
            {new Date().toLocaleDateString('ro-RO', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
        </div>
      </div>
    </header>
  )
}

export default Navbar
