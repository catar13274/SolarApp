import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation } from '@tanstack/react-query'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { invoices } from '../../services/api'
import Button from '../Common/Button'
import LoadingSpinner from '../Common/LoadingSpinner'

const InvoiceUpload = ({ onSuccess, onCancel }) => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadResult, setUploadResult] = useState(null)

  const uploadMutation = useMutation({
    mutationFn: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return invoices.upload(formData)
    },
    onSuccess: (response) => {
      setUploadResult(response.data)
      toast.success('Invoice uploaded and processed successfully!')
      setTimeout(() => {
        onSuccess()
      }, 2000)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to upload invoice')
      setUploadResult({ error: error.response?.data?.detail || 'Upload failed' })
    },
  })

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      const fileExtension = file.name.split('.').pop().toLowerCase()
      const allowedExtensions = ['xml', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt']
      
      if (allowedExtensions.includes(fileExtension)) {
        setSelectedFile(file)
        setUploadResult(null)
      } else {
        toast.error('Only XML, PDF, DOC, XLS, and TXT files are allowed')
      }
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/xml': ['.xml'],
      'application/xml': ['.xml'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    multiple: false,
  })

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    setUploadResult(null)
  }

  return (
    <div className="space-y-4">
      {!uploadResult ? (
        <>
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-colors
              ${isDragActive 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-300 hover:border-primary-400'
              }
            `}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-lg text-primary-600 font-medium">
                Drop the invoice file here...
              </p>
            ) : (
              <div>
                <p className="text-lg text-gray-700 font-medium mb-2">
                  Drag & drop an invoice here
                </p>
                <p className="text-sm text-gray-500">
                  or click to select a file
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  Supports XML (e-Factura), PDF, DOC, XLS, and TXT formats
                </p>
              </div>
            )}
          </div>

          {/* Selected File */}
          {selectedFile && (
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-primary-600" />
                  <div>
                    <p className="font-medium text-gray-900">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleRemoveFile}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          )}

          {/* Upload Status */}
          {uploadMutation.isPending && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center gap-3">
                <LoadingSpinner size="sm" />
                <div>
                  <p className="font-medium text-blue-900">
                    Processing invoice...
                  </p>
                  <p className="text-sm text-blue-700">
                    Parsing invoice and creating purchase record
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload & Process'}
            </Button>
          </div>
        </>
      ) : (
        <>
          {/* Upload Result */}
          {uploadResult.error ? (
            <div className="bg-red-50 rounded-lg p-6 border border-red-200">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-red-900 mb-2">
                    Upload Failed
                  </h4>
                  <p className="text-sm text-red-700">
                    {uploadResult.error}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-green-50 rounded-lg p-6 border border-green-200">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-green-900 mb-2">
                    Invoice Processed Successfully
                  </h4>
                  <div className="text-sm text-green-700 space-y-1">
                    <p>
                      <span className="font-medium">Invoice Number:</span>{' '}
                      {uploadResult.invoice?.invoice_number}
                    </p>
                    <p>
                      <span className="font-medium">Supplier:</span>{' '}
                      {uploadResult.invoice?.supplier}
                    </p>
                    <p>
                      <span className="font-medium">Total Amount:</span>{' '}
                      {uploadResult.invoice?.total_amount} {uploadResult.invoice?.currency}
                    </p>
                    <p>
                      <span className="font-medium">Purchase ID:</span>{' '}
                      {uploadResult.purchase_id}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button onClick={onSuccess}>
              Done
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

export default InvoiceUpload
