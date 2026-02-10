import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit, Trash2, Download, FileText } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { projects } from '../services/api'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import Badge from '../components/Common/Badge'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'
import Modal from '../components/Common/Modal'
import ProjectForm from '../components/Projects/ProjectForm'

const ProjectsPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProject, setEditingProject] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  
  const queryClient = useQueryClient()

  const { data: projectsData, isLoading } = useQuery({
    queryKey: ['projects', statusFilter],
    queryFn: () => projects.getAll({ 
      status: statusFilter || undefined,
    }).then(res => res.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => projects.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects'])
      toast.success('Project deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete project')
    },
  })

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleEdit = (project) => {
    setEditingProject(project)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingProject(null)
  }

  const getFilenameFromResponse = (response, defaultFilename) => {
    // Try to extract filename from Content-Disposition header
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
      if (filenameMatch && filenameMatch[1]) {
        return filenameMatch[1]
      }
    }
    return defaultFilename
  }

  const handleExportPDF = async (project) => {
    try {
      toast.loading('Generating PDF...')
      const response = await projects.exportPDF(project.id)
      
      // Create a blob from the response
      const blob = new Blob([response.data], { type: 'application/pdf' })
      
      // Create a download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = getFilenameFromResponse(response, `Oferta_Comerciala_${project.name.replace(/ /g, '_')}.pdf`)
      
      // Trigger download
      document.body.appendChild(link)
      link.click()
      
      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.dismiss()
      toast.success('PDF downloaded successfully')
    } catch (error) {
      toast.dismiss()
      toast.error('Failed to generate PDF')
      console.error('PDF generation error:', error)
    }
  }

  const handleExportWord = async (project) => {
    try {
      toast.loading('Generating Word document...')
      const response = await projects.exportWord(project.id)
      
      // Create a blob from the response
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      
      // Create a download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = getFilenameFromResponse(response, `Oferta_Comerciala_${project.name.replace(/ /g, '_')}.docx`)
      
      // Trigger download
      document.body.appendChild(link)
      link.click()
      
      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.dismiss()
      toast.success('Word document downloaded successfully')
    } catch (error) {
      toast.dismiss()
      toast.error('Failed to generate Word document')
      console.error('Word document generation error:', error)
    }
  }

  const statusOptions = [
    { value: '', label: 'All Projects' },
    { value: 'planned', label: 'Planned' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  const getStatusBadge = (status) => {
    const variants = {
      planned: 'default',
      in_progress: 'info',
      completed: 'success',
      cancelled: 'danger',
    }
    return variants[status] || 'default'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-gray-600">
            Manage solar panel installation projects
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="h-5 w-5 mr-2" />
          New Project
        </Button>
      </div>

      <Card>
        {/* Status Filter */}
        <div className="mb-6">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Projects Table */}
        {isLoading ? (
          <LoadingSpinner />
        ) : projectsData && projectsData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Project Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Capacity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Start Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {projectsData.map((project) => (
                  <tr key={project.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {project.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div>
                        <div>{project.client_name}</div>
                        {project.client_contact && (
                          <div className="text-xs text-gray-500">
                            {project.client_contact}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {project.capacity_kw ? `${project.capacity_kw} kW` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={getStatusBadge(project.status)}>
                        {project.status.replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {project.start_date ? new Date(project.start_date).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {project.estimated_cost ? `${project.estimated_cost.toFixed(0)} RON` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleExportPDF(project)}
                          className="text-green-600 hover:text-green-900"
                          title="Export PDF"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleExportWord(project)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Export Word"
                        >
                          <FileText className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(project)}
                          className="text-primary-600 hover:text-primary-900"
                          title="Edit"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(project.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
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
            title="No projects found"
            description="Get started by creating your first project"
            action={
              <Button onClick={() => setIsModalOpen(true)}>
                <Plus className="h-5 w-5 mr-2" />
                New Project
              </Button>
            }
          />
        )}
      </Card>

      {/* Project Form Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingProject ? 'Edit Project' : 'New Project'}
        size="xl"
      >
        <ProjectForm
          project={editingProject}
          onSuccess={handleCloseModal}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  )
}

export default ProjectsPage
