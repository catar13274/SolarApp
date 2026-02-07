import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { projects } from '../../services/api'
import Button from '../Common/Button'
import Input from '../Common/Input'
import Select from '../Common/Select'

const ProjectForm = ({ project, onSuccess, onCancel }) => {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: project || {
      name: '',
      client_name: '',
      client_contact: '',
      location: '',
      capacity_kw: 0,
      status: 'planned',
      start_date: '',
      end_date: '',
      estimated_cost: 0,
      actual_cost: 0,
      notes: '',
    }
  })

  const createMutation = useMutation({
    mutationFn: (data) => projects.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects'])
      toast.success('Project created successfully')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create project')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data) => projects.update(project.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects'])
      toast.success('Project updated successfully')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to update project')
    },
  })

  const onSubmit = (data) => {
    // Convert numeric fields
    if (data.capacity_kw) data.capacity_kw = parseFloat(data.capacity_kw)
    if (data.estimated_cost) data.estimated_cost = parseFloat(data.estimated_cost)
    if (data.actual_cost) data.actual_cost = parseFloat(data.actual_cost)
    
    // Convert empty strings to null for optional date fields
    if (!data.start_date) data.start_date = null
    if (!data.end_date) data.end_date = null
    
    if (project) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const statusOptions = [
    { value: 'planned', label: 'Planned' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Project Name"
        required
        {...register('name', { required: 'Project name is required' })}
        error={errors.name?.message}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Client Name"
          required
          {...register('client_name', { required: 'Client name is required' })}
          error={errors.client_name?.message}
        />
        
        <Input
          label="Client Contact"
          {...register('client_contact')}
          error={errors.client_contact?.message}
          placeholder="Phone or email"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Location"
          {...register('location')}
          error={errors.location?.message}
        />
        
        <Input
          label="System Capacity (kW)"
          type="number"
          step="0.1"
          {...register('capacity_kw')}
          error={errors.capacity_kw?.message}
        />
      </div>

      <Select
        label="Status"
        required
        options={statusOptions}
        {...register('status', { required: 'Status is required' })}
        error={errors.status?.message}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Start Date"
          type="date"
          {...register('start_date')}
          error={errors.start_date?.message}
        />
        
        <Input
          label="End Date"
          type="date"
          {...register('end_date')}
          error={errors.end_date?.message}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Estimated Cost (RON)"
          type="number"
          step="0.01"
          {...register('estimated_cost')}
          error={errors.estimated_cost?.message}
        />
        
        <Input
          label="Actual Cost (RON)"
          type="number"
          step="0.01"
          {...register('actual_cost')}
          error={errors.actual_cost?.message}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          {...register('notes')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Additional project notes"
        />
      </div>

      <div className="flex justify-end gap-3 mt-6">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button 
          type="submit"
          disabled={createMutation.isPending || updateMutation.isPending}
        >
          {project ? 'Update' : 'Create'} Project
        </Button>
      </div>
    </form>
  )
}

export default ProjectForm
