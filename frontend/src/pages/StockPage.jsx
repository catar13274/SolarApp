import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Plus, ArrowRight } from 'lucide-react'
import { stock, companies } from '../services/api'
import { useCompanyScope } from '../hooks/useCompanyScope'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import Badge from '../components/Common/Badge'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import Modal from '../components/Common/Modal'
import StockMovementForm from '../components/Stock/StockMovementForm'
import AllocateMaterialForm from '../components/Stock/AllocateMaterialForm'

const StockPage = () => {
  const [companyCode, setCompanyCode] = useCompanyScope()
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false)
  const [isAllocateModalOpen, setIsAllocateModalOpen] = useState(false)
  const [selectedStock, setSelectedStock] = useState(null)
  const [showLowStockOnly, setShowLowStockOnly] = useState(false)

  const companyParams = companyCode ? { company: companyCode } : {}

  const { data: companiesList } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companies.getAll().then((res) => res.data),
  })

  const { data: stockData, isLoading: stockLoading } = useQuery({
    queryKey: ['stock', companyCode],
    queryFn: () => stock.getAll({ ...companyParams }).then(res => res.data),
  })

  const { data: lowStockData } = useQuery({
    queryKey: ['low-stock', companyCode],
    queryFn: () => stock.getLowStock({ ...companyParams }).then(res => res.data),
  })

  const { data: movements, isLoading: movementsLoading } = useQuery({
    queryKey: ['stock-movements', companyCode],
    queryFn: () => stock.getMovements({ limit: 50, ...companyParams }).then(res => res.data),
  })

  const displayData = showLowStockOnly ? lowStockData : stockData

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Stock Management</h1>
          <p className="mt-1 text-gray-600">
            Monitor inventory levels and stock movements
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <label className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm text-gray-700">
            <span className="font-medium whitespace-nowrap">Firma activa</span>
            <select
              value={companyCode}
              onChange={(e) => setCompanyCode(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 min-w-[200px]"
              title="Aceasta selectie filtreaza stocul si lista de materiale la miscari. Este aceeasi ca la pagina Materials."
            >
              <option value="">Toate firmele</option>
              {(companiesList || []).map((c) => (
                <option key={c.id} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <Button onClick={() => setIsMovementModalOpen(true)}>
            <Plus className="h-5 w-5 mr-2" />
            Record Movement
          </Button>
        </div>
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
                    Company
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
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
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
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant="info">
                        {item.material_company_display || item.material_company}
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
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => {
                          setSelectedStock(item)
                          setIsAllocateModalOpen(true)
                        }}
                        disabled={item.quantity <= 0}
                      >
                        <ArrowRight className="h-4 w-4 mr-1" />
                        Allocate
                      </Button>
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
          companyFilter={companyCode || null}
          onSuccess={() => setIsMovementModalOpen(false)}
          onCancel={() => setIsMovementModalOpen(false)}
        />
      </Modal>

      {/* Allocate Material Modal */}
      <Modal
        isOpen={isAllocateModalOpen}
        onClose={() => {
          setIsAllocateModalOpen(false)
          setSelectedStock(null)
        }}
        title="Allocate Material to Project"
        size="lg"
      >
        {selectedStock && (
          <AllocateMaterialForm
            stockItem={selectedStock}
            onSuccess={() => {
              setIsAllocateModalOpen(false)
              setSelectedStock(null)
            }}
            onCancel={() => {
              setIsAllocateModalOpen(false)
              setSelectedStock(null)
            }}
          />
        )}
      </Modal>
    </div>
  )
}

export default StockPage
