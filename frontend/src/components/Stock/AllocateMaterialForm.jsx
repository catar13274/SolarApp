import { useForm, useWatch } from 'react-hook-form'
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
  
  // Get acquisition price from stockItem (now includes acquisition_price from backend)
  const acquisitionPrice = stockItem?.acquisition_price || materialData?.unit_price || 0
  
  const { register, handleSubmit, control, formState: { errors } } = useForm({
    mode: 'onChange',
    defaultValues: {
      project_id: '',
      quantity: 0,
      commercial_markup: 1.2, // Default 20% markup
    }
  })
  
  // Watch commercial_markup to calculate project price
  const commercialMarkup = useWatch({
    control,
    name: 'commercial_markup',
    defaultValue: 1.2
  })
  
  // Calculate project price
  const projectPrice = acquisitionPrice * (isNaN(parseFloat(commercialMarkup)) ? 1 : parseFloat(commercialMarkup))

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
      // Calculate final unit price for project
      const finalUnitPrice = acquisitionPrice * parseFloat(data.commercial_markup)
      
      // Find the project name
      const project = allProjects?.find(p => p.id === data.project_id)
      const projectName = project ? project.name : 'Unknown Project'
      
      // First, add material to project
      await projects.addMaterial(data.project_id, {
        material_id: stockItem.material_id,
        quantity_planned: data.quantity,
        quantity_used: 0,
        unit_price: finalUnitPrice,
        project_id: data.project_id
      })
      
      // Then create stock movement to track the allocation
      await stock.createMovement({
        material_id: stockItem.material_id,
        movement_type: 'out',
        quantity: data.quantity,
        reference_type: 'project',
        reference_id: data.project_id,
        notes: `Allocated to project: ${projectName}`
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
    
    const markup = parseFloat(data.commercial_markup)
    if (isNaN(markup) || markup <= 0) {
      toast.error('Please enter a valid commercial markup')
      return
    }
    
    allocateMutation.mutate({
      project_id: projectId,
      quantity: quantity,
      commercial_markup: markup
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
      </div>
      
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-green-900">Pricing Information</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2">
          <div>
            <p className="text-xs text-green-700 font-medium">Acquisition Price</p>
            <p className="text-sm text-green-900 font-semibold">{acquisitionPrice.toFixed(2)} RON</p>
          </div>
          <div>
            <p className="text-xs text-green-700 font-medium">Commercial Markup</p>
            <p className="text-sm text-green-900 font-semibold">{parseFloat(commercialMarkup).toFixed(2)}x</p>
          </div>
          <div>
            <p className="text-xs text-green-700 font-medium">Project Price</p>
            <p className="text-sm text-green-900 font-semibold">{projectPrice.toFixed(2)} RON</p>
          </div>
        </div>
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
        label="Commercial Markup (multiplier)"
        type="number"
        step="0.01"
        required
        defaultValue={1.2}
        {...register('commercial_markup', { 
          required: 'Commercial markup is required',
          min: { value: 0.01, message: 'Markup must be greater than 0' }
        })}
        error={errors.commercial_markup?.message}
        helperText="E.g., 1.2 for 20% markup, 1.5 for 50% markup"
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
