import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Plus } from 'lucide-react'
import { stock } from '../services/api'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import Badge from '../components/Common/Badge'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import Modal from '../components/Common/Modal'
import StockMovementForm from '../components/Stock/StockMovementForm'

const StockPage = () => {
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false)
  const [showLowStockOnly, setShowLowStockOnly] = useState(false)

  const { data: stockData, isLoading: stockLoading } = useQuery({
    queryKey: ['stock'],
    queryFn: () => stock.getAll().then(res => res.data),
  })

  const { data: lowStockData } = useQuery({
    queryKey: ['low-stock'],
    queryFn: () => stock.getLowStock().then(res => res.data),
  })

  const { data: movements, isLoading: movementsLoading } = useQuery({
    queryKey: ['stock-movements'],
    queryFn: () => stock.getMovements({ limit: 50 }).then(res => res.data),
  })

  const displayData = showLowStockOnly ? lowStockData : stockData

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Stock Management</h1>
          <p className="mt-1 text-gray-600">
            Monitor inventory levels and stock movements
          </p>
        </div>
        <Button onClick={() => setIsMovementModalOpen(true)}>
          <Plus className="h-5 w-5 mr-2" />
          Record Movement
        </Button>
      </div>

      {/* Low Stock Alert */}
      {lowStockData && lowStockData.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Low Stock Warning
              </h3>
              <p className="mt-1 text-sm text-red-700">
                {lowStockData.length} material{lowStockData.length !== 1 ? 's' : ''} below minimum stock level
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stock Levels */}
      <Card title="Current Stock Levels">
        <div className="mb-4 flex items-center gap-4">
          <Button
            variant={showLowStockOnly ? 'secondary' : 'primary'}
            size="sm"
            onClick={() => setShowLowStockOnly(false)}
          >
            All Stock
          </Button>
          <Button
            variant={showLowStockOnly ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setShowLowStockOnly(true)}
          >
            Low Stock Only ({lowStockData?.length || 0})
          </Button>
        </div>

        {stockLoading ? (
          <LoadingSpinner />
        ) : displayData && displayData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Material
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    SKU
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Min Stock
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayData.map((item) => (
                  <tr 
                    key={item.id} 
                    className={`hover:bg-gray-50 ${item.is_low ? 'bg-red-50' : ''}`}
                  >
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {item.material_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {item.material_sku}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant="default">
                        {item.material_category}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      {item.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {item.min_stock}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {item.location}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.is_low ? (
                        <Badge variant="danger">
                          Low Stock
                        </Badge>
                      ) : (
                        <Badge variant="success">
                          OK
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No stock data available</p>
        )}
      </Card>

      {/* Stock Movements History */}
      <Card title="Stock Movements History">
        {movementsLoading ? (
          <LoadingSpinner />
        ) : movements && movements.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Material
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reference
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Notes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {movements.map((movement) => (
                  <tr key={movement.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(movement.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {movement.material_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      {movement.movement_type === 'out' ? '-' : '+'}{movement.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {movement.reference_type || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {movement.notes || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No movements recorded</p>
        )}
      </Card>

      {/* Stock Movement Form Modal */}
      <Modal
        isOpen={isMovementModalOpen}
        onClose={() => setIsMovementModalOpen(false)}
        title="Record Stock Movement"
        size="lg"
      >
        <StockMovementForm
          onSuccess={() => setIsMovementModalOpen(false)}
          onCancel={() => setIsMovementModalOpen(false)}
        />
      </Modal>
    </div>
  )
}

export default StockPage
