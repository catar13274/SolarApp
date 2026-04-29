import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'

const LoginPage = () => {
  const buttonRef = useRef(null)
  const [error, setError] = useState('')
  const { loginWithGoogle } = useAuth()

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    if (!clientId) {
      setError('Lipseste configurarea VITE_GOOGLE_CLIENT_ID in frontend/.env.')
      return
    }

    if (!window.google?.accounts?.id) {
      setError('Google Identity Services nu este disponibil.')
      return
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response) => {
        try {
          setError('')
          await loginWithGoogle(response.credential)
        } catch (err) {
          setError(err?.response?.data?.detail || 'Autentificarea a esuat.')
        }
      },
    })

    if (buttonRef.current) {
      buttonRef.current.innerHTML = ''
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: 'outline',
        size: 'large',
        width: 320,
        text: 'signin_with',
      })
    }
  }, [loginWithGoogle])

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-md p-8">
        <h1 className="text-2xl font-bold text-gray-900">SolarApp Login</h1>
        <p className="text-sm text-gray-600 mt-2">
          Acces permis pentru domeniile freevoltsrl.ro si energoteamconect.ro.
        </p>

        <div className="mt-6 flex justify-center">
          <div ref={buttonRef} />
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-600 text-center">{error}</p>
        )}
      </div>
    </div>
  )
}

export default LoginPage
