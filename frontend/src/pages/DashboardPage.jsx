import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  Package, 
  AlertTriangle, 
  Briefcase, 
  FileText,
  TrendingUp,
  ArrowRight
} from 'lucide-react'
import { dashboard, stock } from '../services/api'
import Card from '../components/Common/Card'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import Badge from '../components/Common/Badge'

const DashboardPage = () => {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboard.getStats().then(res => res.data),
  })

  const { data: movements, isLoading: movementsLoading } = useQuery({
    queryKey: ['recent-movements'],
    queryFn: () => stock.getMovements({ limit: 10 }).then(res => res.data),
  })

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const statCards = [
    {
      title: 'Total Materials',
      value: stats?.total_materials || 0,
      icon: Package,
      color: 'bg-blue-500',
      link: '/materials',
    },
    {
      title: 'Low Stock Alerts',
      value: stats?.low_stock_count || 0,
      icon: AlertTriangle,
      color: 'bg-red-500',
      link: '/stock',
    },
    {
      title: 'Active Projects',
      value: stats?.active_projects || 0,
      icon: Briefcase,
      color: 'bg-green-500',
      link: '/projects',
    },
    {
      title: 'Total Projects',
      value: stats?.total_projects || 0,
      icon: FileText,
      color: 'bg-purple-500',
      link: '/projects',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">
          Overview of your solar panel management system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <Link key={stat.title} to={stat.link}>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {stat.title}
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm text-primary-600 hover:text-primary-700">
                <span>View details</span>
                <ArrowRight className="ml-1 h-4 w-4" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Recent Stock Movements */}
      <Card title="Recent Stock Movements">
        {movementsLoading ? (
          <LoadingSpinner />
        ) : movements && movements.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Material
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Notes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {movements.map((movement) => (
                  <tr key={movement.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {new Date(movement.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {movement.material_name || 'Unknown'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge 
                        variant={
                          movement.movement_type === 'in' ? 'success' : 
                          movement.movement_type === 'out' ? 'danger' : 
                          'info'
                        }
                      >
                        {movement.movement_type}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {movement.quantity}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {movement.notes || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No recent movements</p>
        )}
      </Card>

      {/* Quick Actions */}
      <Card title="Quick Actions">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/materials"
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Package className="h-6 w-6 text-primary-600" />
            <div>
              <h3 className="font-medium text-gray-900">Add Material</h3>
              <p className="text-sm text-gray-600">Create new material</p>
            </div>
          </Link>
          
          <Link
            to="/projects"
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Briefcase className="h-6 w-6 text-primary-600" />
            <div>
              <h3 className="font-medium text-gray-900">New Project</h3>
              <p className="text-sm text-gray-600">Start a new project</p>
            </div>
          </Link>
          
          <Link
            to="/invoices"
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <FileText className="h-6 w-6 text-primary-600" />
            <div>
              <h3 className="font-medium text-gray-900">Upload Invoice</h3>
              <p className="text-sm text-gray-600">Process XML invoice</p>
            </div>
          </Link>
        </div>
      </Card>
    </div>
  )
}

export default DashboardPage
