import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit, Trash2, Search, Download, Upload } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { materials, companies } from '../services/api'
import { useCompanyScope } from '../hooks/useCompanyScope'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import Badge from '../components/Common/Badge'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'
import MaterialForm from '../components/Materials/MaterialForm'
import Modal from '../components/Common/Modal'

const MaterialsPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingMaterial, setEditingMaterial] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [tenantCode] = useCompanyScope()
  const importInputRef = useRef(null)
  
  const queryClient = useQueryClient()

  const { data: companiesList } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companies.getAll().then((res) => res.data),
  })

  const { data: materialsData, isLoading } = useQuery({
    queryKey: ['materials', searchTerm, categoryFilter, tenantCode],
    queryFn: () =>
      materials
        .getAll({
          search: searchTerm || undefined,
          category: categoryFilter || undefined,
        })
        .then((res) => res.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => materials.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['materials'])
      toast.success('Material deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete material')
    },
  })

  const exportMutation = useMutation({
    mutationFn: () => materials.exportExcel({}),
    onSuccess: (response) => {
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `materials_export_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Materials exported successfully')
    },
    onError: () => {
      toast.error('Failed to export materials')
    },
  })

  const importMutation = useMutation({
    mutationFn: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return materials.importExcel(formData)
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries(['materials'])
      const { created = 0, updated = 0, skipped = 0, errors = [] } = response.data || {}
      const msg = `Import completed: ${created} created, ${updated} updated, ${skipped} skipped`
      toast.success(msg)
      if (errors.length > 0) {
        toast.error(`Import completed with ${errors.length} errors. Check backend response for details.`)
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to import materials')
    },
  })

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this material?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleEdit = (material) => {
    setEditingMaterial(material)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingMaterial(null)
  }

  const handleImportClick = () => {
    importInputRef.current?.click()
  }

  const handleImportFileChange = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    const fileName = file.name.toLowerCase()
    if (!fileName.endsWith('.xlsx')) {
      toast.error('Please select an .xlsx file')
      event.target.value = ''
      return
    }
    importMutation.mutate(file)
    event.target.value = ''
  }

  const categories = [
    { value: '', label: 'All Categories' },
    { value: 'panel', label: 'Solar Panels' },
    { value: 'inverter', label: 'Inverters' },
    { value: 'battery', label: 'Batteries' },
    { value: 'cable', label: 'Cables' },
    { value: 'mounting', label: 'Mounting' },
    { value: 'other', label: 'Other' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Materials</h1>
          <p className="mt-1 text-gray-600">
            Manage your solar panel components and materials
            {tenantCode && companiesList?.length ? (
              <span className="block text-sm text-primary-700 mt-1">
                Baza curentă:{' '}
                <strong>
                  {companiesList.find((c) => c.code === tenantCode)?.name || tenantCode}
                </strong>{' '}
                (selectată în bara de sus)
              </span>
            ) : null}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={importInputRef}
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={handleImportFileChange}
          />
          <Button
            variant="secondary"
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending}
          >
            <Download className="h-5 w-5 mr-2" />
            {exportMutation.isPending ? 'Exporting...' : 'Export Excel'}
          </Button>
          <Button
            variant="secondary"
            onClick={handleImportClick}
            disabled={importMutation.isPending}
          >
            <Upload className="h-5 w-5 mr-2" />
            {importMutation.isPending ? 'Importing...' : 'Import Excel'}
          </Button>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="h-5 w-5 mr-2" />
            Add Material
          </Button>
        </div>
      </div>

      <Card>
        {/* Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search materials..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        {/* Materials Table */}
        {isLoading ? (
          <LoadingSpinner />
        ) : materialsData && materialsData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    SKU
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unit Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Min Stock
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Stock
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {materialsData.map((material) => (
                  <tr key={material.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {material.sku}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{material.name}</div>
                        {material.description && (
                          <div className="text-gray-500 text-xs mt-1">
                            {material.description.substring(0, 50)}
                            {material.description.length > 50 ? '...' : ''}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant="default">
                        {material.category}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {material.unit_price.toFixed(2)} RON
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {material.min_stock}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge 
                        variant={
                          material.current_stock < material.min_stock 
                            ? 'danger' 
                            : 'success'
                        }
                      >
                        {material.current_stock || 0}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEdit(material)}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(material.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="No materials found"
            description="Get started by adding your first material"
            action={
              <Button onClick={() => setIsModalOpen(true)}>
                <Plus className="h-5 w-5 mr-2" />
                Add Material
              </Button>
            }
          />
        )}
      </Card>

      {/* Material Form Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingMaterial ? 'Edit Material' : 'Add Material'}
        size="lg"
      >
        <MaterialForm
          material={editingMaterial}
          onSuccess={handleCloseModal}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  )
}

export default MaterialsPage
