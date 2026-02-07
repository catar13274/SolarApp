import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { stock, materials } from '../../services/api'
import Button from '../Common/Button'
import Input from '../Common/Input'
import Select from '../Common/Select'

const StockMovementForm = ({ onSuccess, onCancel }) => {
  const queryClient = useQueryClient()
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    defaultValues: {
      material_id: '',
      movement_type: 'in',
      quantity: 0,
      notes: '',
    }
  })

  const { data: materialsData } = useQuery({
    queryKey: ['materials'],
    queryFn: () => materials.getAll().then(res => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (data) => stock.createMovement(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['stock'])
      queryClient.invalidateQueries(['stock-movements'])
      queryClient.invalidateQueries(['low-stock'])
      toast.success('Stock movement recorded successfully')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to record movement')
    },
  })

  const onSubmit = (data) => {
    data.material_id = parseInt(data.material_id)
    data.quantity = parseFloat(data.quantity)
    
    createMutation.mutate(data)
  }

  const movementTypes = [
    { value: 'in', label: 'Stock In (Add)' },
    { value: 'out', label: 'Stock Out (Remove)' },
    { value: 'adjustment', label: 'Adjustment (Set to)' },
    { value: 'transfer', label: 'Transfer' },
  ]

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Select
        label="Material"
        required
        options={[
          { value: '', label: 'Select a material' },
          ...(materialsData || []).map(m => ({
            value: m.id.toString(),
            label: `${m.name} (${m.sku})`
          }))
        ]}
        {...register('material_id', { required: 'Material is required' })}
        error={errors.material_id?.message}
      />

      <Select
        label="Movement Type"
        required
        options={movementTypes}
        {...register('movement_type', { required: 'Movement type is required' })}
        error={errors.movement_type?.message}
      />

      <Input
        label="Quantity"
        type="number"
        step="0.01"
        required
        {...register('quantity', { 
          required: 'Quantity is required',
          min: { value: 0.01, message: 'Quantity must be greater than 0' }
        })}
        error={errors.quantity?.message}
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          {...register('notes')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Optional notes about this movement"
        />
      </div>

      <div className="flex justify-end gap-3 mt-6">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={createMutation.isPending}>
          Record Movement
        </Button>
      </div>
    </form>
  )
}

export default StockMovementForm
