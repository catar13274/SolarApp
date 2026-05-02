import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit, Trash2, Building2 } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { companies } from '../services/api'
import Card from '../components/Common/Card'
import Button from '../components/Common/Button'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'
import Modal from '../components/Common/Modal'
import Input from '../components/Common/Input'

const emptyForm = {
  code: '',
  name: '',
  legal_name: '',
  tax_id: '',
  registration: '',
  address: '',
  phone: '',
  email: '',
  notes: '',
}

const CompaniesPage = () => {
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const queryClient = useQueryClient()

  const { data: list, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companies.getAll().then((res) => res.data),
  })

  const saveMutation = useMutation({
    mutationFn: () =>
      editingId
        ? companies.update(editingId, {
            name: form.name,
            legal_name: form.legal_name || null,
            tax_id: form.tax_id || null,
            registration: form.registration || null,
            address: form.address || null,
            phone: form.phone || null,
            email: form.email || null,
            notes: form.notes || null,
          })
        : companies.create({
            code: form.code.trim(),
            name: form.name.trim(),
            legal_name: form.legal_name || null,
            tax_id: form.tax_id || null,
            registration: form.registration || null,
            address: form.address || null,
            phone: form.phone || null,
            email: form.email || null,
            notes: form.notes || null,
          }),
    onSuccess: () => {
      queryClient.invalidateQueries(['companies'])
      toast.success(editingId ? 'Firma actualizata' : 'Firma adaugata')
      closeModal()
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Eroare la salvare')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => companies.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['companies'])
      toast.success('Firma stearsa')
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Nu se poate sterge firma')
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
      code: row.code,
      name: row.name || '',
      legal_name: row.legal_name || '',
      tax_id: row.tax_id || '',
      registration: row.registration || '',
      address: row.address || '',
      phone: row.phone || '',
      email: row.email || '',
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
      toast.error('Numele firmei este obligatoriu')
      return
    }
    if (!editingId && !form.code.trim()) {
      toast.error('Codul pentru stoc este obligatoriu la firma noua')
      return
    }
    saveMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Firme</h1>
          <p className="mt-1 text-gray-600">
            Inregistrati societatile pentru care gestionati stocul. La materiale si stoc veti alege firma din lista.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-5 w-5 mr-2" />
          Adauga firma
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
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Denumire</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cod stoc</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CUI</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actiuni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {list.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-gray-400 shrink-0" />
                        {c.name}
                      </div>
                      {c.legal_name && c.legal_name !== c.name && (
                        <div className="text-xs text-gray-500 mt-0.5">{c.legal_name}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 font-mono">{c.code}</td>
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
                          if (window.confirm(`Stergeti firma „${c.name}”?`)) {
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
            title="Nicio firma inregistrata"
            description="Adaugati cel putin o firma inainte de a crea materiale in stoc."
            action={
              <Button onClick={openCreate}>
                <Plus className="h-5 w-5 mr-2" />
                Adauga prima firma
              </Button>
            }
          />
        )}
      </Card>

      <Modal
        isOpen={modalOpen}
        onClose={closeModal}
        title={editingId ? 'Editeaza firma' : 'Firma noua'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {!editingId && (
            <Input
              label="Cod pentru stoc (unic)"
              value={form.code}
              onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
              placeholder="ex: freevoltsrl.ro sau firma-measerl"
              required
            />
          )}
          {editingId && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cod stoc</label>
              <p className="text-sm font-mono text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">{form.code}</p>
              <p className="text-xs text-gray-500 mt-1">Codul nu poate fi schimbat dupa creare.</p>
            </div>
          )}
          <Input
            label="Nume afisat"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
          <Input
            label="Denumire legala (optional)"
            value={form.legal_name}
            onChange={(e) => setForm((f) => ({ ...f, legal_name: e.target.value }))}
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
          <Input
            label="Adresa"
            value={form.address}
            onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Telefon"
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            />
            <Input
              label="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </div>
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

export default CompaniesPage
