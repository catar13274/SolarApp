import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Package, FileText } from 'lucide-react'
import { purchases } from '../services/api'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import Badge from '../components/Common/Badge'
import LoadingSpinner from '../components/Common/LoadingSpinner'

const PurchaseDetailsPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: purchase, isLoading } = useQuery({
    queryKey: ['purchase', id],
    queryFn: () => purchases.getById(id).then(res => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!purchase) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Purchase not found</p>
        <Button onClick={() => navigate('/invoices')} className="mt-4">
          Back to Invoices
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/invoices')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Invoices
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Purchase Details</h1>
            <p className="mt-1 text-gray-600">
              Purchase #{purchase.id}
            </p>
          </div>
        </div>
      </div>

      {/* Purchase Information */}
      <Card>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Package className="h-6 w-6 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900">Purchase Information</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-sm font-medium text-gray-500">Supplier</label>
              <p className="mt-1 text-lg font-semibold text-gray-900">{purchase.supplier}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Purchase Date</label>
              <p className="mt-1 text-lg text-gray-900">
                {new Date(purchase.purchase_date).toLocaleDateString()}
              </p>
            </div>

            {purchase.invoice_number && (
              <div>
                <label className="text-sm font-medium text-gray-500">Invoice Number</label>
                <p className="mt-1 text-lg text-gray-900">{purchase.invoice_number}</p>
              </div>
            )}

            <div>
              <label className="text-sm font-medium text-gray-500">Total Amount</label>
              <div className="mt-1 flex items-center gap-2">
                <p className="text-lg font-bold text-gray-900">
                  {purchase.total_amount.toFixed(2)}
                </p>
                <Badge variant="default">{purchase.currency}</Badge>
              </div>
            </div>

            {purchase.notes && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-500">Notes</label>
                <p className="mt-1 text-gray-700">{purchase.notes}</p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Purchase Items */}
      {purchase.items && purchase.items.length > 0 && (
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <FileText className="h-6 w-6 text-primary-600" />
              <h2 className="text-xl font-semibold text-gray-900">Purchase Items</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SKU
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unit Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Price
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {purchase.items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {item.description}
                        {item.material_name && (
                          <span className="block text-xs text-gray-500 mt-1">
                            Material: {item.material_name}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.sku || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.unit_price.toFixed(2)} {purchase.currency}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                        {item.total_price.toFixed(2)} {purchase.currency}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

export default PurchaseDetailsPage
