import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { materials } from '../../services/api'
import Button from '../Common/Button'
import Input from '../Common/Input'
import Select from '../Common/Select'

const MaterialForm = ({ material, onSuccess, onCancel }) => {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: material || {
      name: '',
      sku: '',
      description: '',
      category: 'panel',
      unit: 'buc',
      unit_price: 0,
      min_stock: 0,
    }
  })

  const createMutation = useMutation({
    mutationFn: (data) => materials.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['materials'])
      toast.success('Material created successfully')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create material')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data) => materials.update(material.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['materials'])
      toast.success('Material updated successfully')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to update material')
    },
  })

  const onSubmit = (data) => {
    // Convert numeric fields
    data.unit_price = parseFloat(data.unit_price)
    data.min_stock = parseInt(data.min_stock)
    
    if (material) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const categories = [
    { value: 'panel', label: 'Solar Panel' },
    { value: 'inverter', label: 'Inverter' },
    { value: 'battery', label: 'Battery' },
    { value: 'cable', label: 'Cable' },
    { value: 'mounting', label: 'Mounting' },
    { value: 'other', label: 'Other' },
  ]

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Name"
          required
          {...register('name', { required: 'Name is required' })}
          error={errors.name?.message}
        />
        
        <Input
          label="SKU"
          required
          {...register('sku', { required: 'SKU is required' })}
          error={errors.sku?.message}
        />
      </div>

      <Input
        label="Description"
        {...register('description')}
        error={errors.description?.message}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Select
          label="Category"
          required
          options={categories}
          {...register('category', { required: 'Category is required' })}
          error={errors.category?.message}
        />
        
        <Input
          label="Unit"
          required
          {...register('unit', { required: 'Unit is required' })}
          error={errors.unit?.message}
          placeholder="e.g., buc, m, kg"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Unit Price (RON)"
          type="number"
          step="0.01"
          required
          {...register('unit_price', { required: 'Unit price is required' })}
          error={errors.unit_price?.message}
        />
        
        <Input
          label="Minimum Stock"
          type="number"
          required
          {...register('min_stock', { required: 'Minimum stock is required' })}
          error={errors.min_stock?.message}
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
          {material ? 'Update' : 'Create'} Material
        </Button>
      </div>
    </form>
  )
}

export default MaterialForm
