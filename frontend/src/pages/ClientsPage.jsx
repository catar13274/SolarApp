import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit, Trash2, Users } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { clients } from '../services/api'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'
import Modal from '../components/Common/Modal'
import Input from '../components/Common/Input'

const emptyForm = {
  name: '',
  contact: '',
  tax_id: '',
  registration: '',
  billing_address: '',
  location: '',
  notes: '',
}

const ClientsPage = () => {
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const queryClient = useQueryClient()

  const { data: list, isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: () => clients.getAll({ limit: 200 }).then((res) => res.data),
  })

  const saveMutation = useMutation({
    mutationFn: () =>
      editingId
        ? clients.update(editingId, {
            name: form.name.trim(),
            contact: form.contact || null,
            tax_id: form.tax_id || null,
            registration: form.registration || null,
            billing_address: form.billing_address || null,
            location: form.location || null,
            notes: form.notes || null,
          })
        : clients.create({
            name: form.name.trim(),
            contact: form.contact || null,
            tax_id: form.tax_id || null,
            registration: form.registration || null,
            billing_address: form.billing_address || null,
            location: form.location || null,
            notes: form.notes || null,
          }),
    onSuccess: () => {
      queryClient.invalidateQueries(['clients'])
      toast.success(editingId ? 'Client actualizat' : 'Client adaugat')
      closeModal()
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Eroare la salvare')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => clients.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['clients'])
      toast.success('Client sters')
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Nu se poate sterge clientul')
    },
  })

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  const openEdit = (row) => {
    setEditingId(row.id)
    setForm({
      name: row.name || '',
      contact: row.contact || '',
      tax_id: row.tax_id || '',
      registration: row.registration || '',
      billing_address: row.billing_address || '',
      location: row.location || '',
      notes: row.notes || '',
    })
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.name.trim()) {
      toast.error('Numele clientului este obligatoriu')
      return
    }
    saveMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clienti</h1>
          <p className="mt-1 text-gray-600">
            Lista clientilor folosita la proiecte. Puteti completa rapid datele de facturare selectand un client salvat.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-5 w-5 mr-2" />
          Adauga client
        </Button>
      </div>

      <Card>
        {isLoading ? (
          <LoadingSpinner />
        ) : list && list.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nume</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CUI</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actiuni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {list.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-gray-400 shrink-0" />
                        {c.name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{c.contact || '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{c.tax_id || '—'}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => openEdit(c)}
                        className="text-primary-600 hover:text-primary-900 p-1"
                        title="Editeaza"
                      >
                        <Edit className="h-4 w-4 inline" />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (window.confirm(`Stergeti clientul „${c.name}”?`)) {
                            deleteMutation.mutate(c.id)
                          }
                        }}
                        className="text-red-600 hover:text-red-900 p-1 ml-2"
                        title="Sterge"
                      >
                        <Trash2 className="h-4 w-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="Niciun client inregistrat"
            description="Adaugati clientii cu care lucrati; ii veti putea selecta la crearea unui proiect."
            action={
              <Button onClick={openCreate}>
                <Plus className="h-5 w-5 mr-2" />
                Adauga primul client
              </Button>
            }
          />
        )}
      </Card>

      <Modal
        isOpen={modalOpen}
        onClose={closeModal}
        title={editingId ? 'Editeaza client' : 'Client nou'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nume client / firma"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
          <Input
            label="Contact (telefon sau email)"
            value={form.contact}
            onChange={(e) => setForm((f) => ({ ...f, contact: e.target.value }))}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="CUI / CIF"
              value={form.tax_id}
              onChange={(e) => setForm((f) => ({ ...f, tax_id: e.target.value }))}
            />
            <Input
              label="Nr. Reg. Com."
              value={form.registration}
              onChange={(e) => setForm((f) => ({ ...f, registration: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Adresa de facturare</label>
            <textarea
              value={form.billing_address}
              onChange={(e) => setForm((f) => ({ ...f, billing_address: e.target.value }))}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Strada, numar, localitate"
            />
          </div>
          <Input
            label="Locatie montaj / santier (optional)"
            value={form.location}
            onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>
              Renunta
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Se salveaza...' : 'Salveaza'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default ClientsPage
