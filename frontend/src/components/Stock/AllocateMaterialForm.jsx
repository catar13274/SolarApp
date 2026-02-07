import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { projects, stock, materials } from '../../services/api'
import Button from '../Common/Button'
import Input from '../Common/Input'
import Select from '../Common/Select'

const AllocateMaterialForm = ({ stockItem, onSuccess, onCancel }) => {
  const queryClient = useQueryClient()
  
  // Fetch material details to get unit price
  const { data: materialData } = useQuery({
    queryKey: ['material', stockItem?.material_id],
    queryFn: () => materials.getById(stockItem.material_id).then(res => res.data),
    enabled: !!stockItem?.material_id,
  })
  
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      project_id: '',
      quantity: 0,
    }
  })

  // Fetch both planned and in_progress projects
  const { data: allProjects } = useQuery({
    queryKey: ['projects-for-allocation'],
    queryFn: async () => {
      const [planned, inProgress] = await Promise.all([
        projects.getAll({ status: 'planned' }).then(res => res.data),
        projects.getAll({ status: 'in_progress' }).then(res => res.data)
      ])
      return [...planned, ...inProgress]
    }
  })

  const allocateMutation = useMutation({
    mutationFn: async (data) => {
      // First, add material to project
      await projects.addMaterial(data.project_id, {
        material_id: stockItem.material_id,
        quantity_planned: data.quantity,
        quantity_used: 0,
        unit_price: data.unit_price,
        project_id: data.project_id
      })
      
      // Then create stock movement to track the allocation
      await stock.createMovement({
        material_id: stockItem.material_id,
        movement_type: 'out',
        quantity: data.quantity,
        reference_type: 'project',
        reference_id: data.project_id,
        notes: `Allocated to project`
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['stock'])
      queryClient.invalidateQueries(['stock-movements'])
      queryClient.invalidateQueries(['projects'])
      toast.success('Material allocated to project successfully')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to allocate material')
    },
  })

  const onSubmit = (data) => {
    const projectId = parseInt(data.project_id)
    if (isNaN(projectId) || projectId <= 0) {
      toast.error('Please select a valid project')
      return
    }
    
    const quantity = parseFloat(data.quantity)
    if (isNaN(quantity) || quantity <= 0) {
      toast.error('Please enter a valid quantity')
      return
    }
    
    if (quantity > stockItem.quantity) {
      toast.error('Insufficient stock available')
      return
    }
    
    allocateMutation.mutate({
      project_id: projectId,
      quantity: quantity,
      unit_price: parseFloat(data.unit_price) || (materialData?.unit_price || 0)
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-blue-900">Material Details</h4>
        <p className="text-sm text-blue-800 mt-1">
          <span className="font-medium">{stockItem?.material_name}</span> ({stockItem?.material_sku})
        </p>
        <p className="text-sm text-blue-700 mt-1">
          Available: <span className="font-semibold">{stockItem?.quantity}</span> units
        </p>
        {materialData && (
          <p className="text-sm text-blue-700 mt-1">
            Unit Price: <span className="font-semibold">{materialData.unit_price} RON</span>
          </p>
        )}
      </div>

      <Select
        label="Project"
        required
        options={[
          { value: '', label: 'Select a project' },
          ...(allProjects || []).map(p => ({
            value: p.id.toString(),
            label: `${p.name} - ${p.client_name} (${p.status})`
          }))
        ]}
        {...register('project_id', { 
          required: 'Project is required',
          validate: (value) => value !== '' || 'Please select a project'
        })}
        error={errors.project_id?.message}
      />

      <Input
        label="Quantity to Allocate"
        type="number"
        step="0.01"
        required
        {...register('quantity', { 
          required: 'Quantity is required',
          min: { value: 0.01, message: 'Quantity must be greater than 0' },
          max: { value: stockItem?.quantity || 0, message: 'Exceeds available stock' }
        })}
        error={errors.quantity?.message}
      />

      <Input
        label="Unit Price (RON)"
        type="number"
        step="0.01"
        required
        defaultValue={materialData?.unit_price || 0}
        {...register('unit_price', { 
          required: 'Unit price is required',
          min: { value: 0, message: 'Price must be 0 or greater' }
        })}
        error={errors.unit_price?.message}
      />

      <div className="flex justify-end gap-3 mt-6">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={allocateMutation.isPending}>
          Allocate to Project
        </Button>
      </div>
    </form>
  )
}

export default AllocateMaterialForm
