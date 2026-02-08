import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Upload, FileText, ExternalLink, Trash2 } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { invoices } from '../services/api'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import Badge from '../components/Common/Badge'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'
import Modal from '../components/Common/Modal'
import InvoiceUpload from '../components/Invoices/InvoiceUpload'

const InvoicesPage = () => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [deleteInvoiceId, setDeleteInvoiceId] = useState(null)
  
  const queryClient = useQueryClient()

  const { data: invoicesData, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => invoices.getAll().then(res => res.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => invoices.delete(id),
    onSuccess: () => {
      toast.success('Invoice deleted successfully!')
      queryClient.invalidateQueries(['invoices'])
      setDeleteInvoiceId(null)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to delete invoice')
    },
  })

  const handleDeleteClick = (id) => {
    setDeleteInvoiceId(id)
  }

  const handleConfirmDelete = () => {
    if (deleteInvoiceId) {
      deleteMutation.mutate(deleteInvoiceId)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
          <p className="mt-1 text-gray-600">
            Upload and manage invoices (XML, PDF, DOC, XLS, TXT formats)
          </p>
        </div>
        <Button onClick={() => setIsUploadModalOpen(true)}>
          <Upload className="h-5 w-5 mr-2" />
          Upload Invoice
        </Button>
      </div>

      <Card>
        {/* Invoices Table */}
        {isLoading ? (
          <LoadingSpinner />
        ) : invoicesData && invoicesData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invoice Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Supplier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Currency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Purchase
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoicesData.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {invoice.invoice_number}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {invoice.supplier}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(invoice.invoice_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      {invoice.total_amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant="default">
                        {invoice.currency}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {invoice.purchase_id ? (
                        <Link
                          to={`/purchases/${invoice.purchase_id}`}
                          className="text-primary-600 hover:text-primary-900 inline-flex items-center gap-1"
                        >
                          View Purchase
                          <ExternalLink className="h-3 w-3" />
                        </Link>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(invoice.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleDeleteClick(invoice.id)}
                        className="text-red-600 hover:text-red-800 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={FileText}
            title="No invoices uploaded"
            description="Upload your first invoice to get started"
            action={
              <Button onClick={() => setIsUploadModalOpen(true)}>
                <Upload className="h-5 w-5 mr-2" />
                Upload Invoice
              </Button>
            }
          />
        )}
      </Card>

      {/* Invoice Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Invoice"
        size="lg"
      >
        <InvoiceUpload
          onSuccess={() => {
            setIsUploadModalOpen(false)
            queryClient.invalidateQueries(['invoices'])
          }}
          onCancel={() => setIsUploadModalOpen(false)}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteInvoiceId !== null}
        onClose={() => setDeleteInvoiceId(null)}
        title="Delete Invoice"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            Are you sure you want to delete this invoice? This action will also delete the associated purchase record and all its items.
          </p>
          <p className="text-sm text-red-600 font-medium">
            This action cannot be undone.
          </p>
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setDeleteInvoiceId(null)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmDelete}
              disabled={deleteMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete Invoice'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default InvoicesPage
