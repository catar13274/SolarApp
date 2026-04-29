import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api, { authApi } from '../services/api'

const TOKEN_KEY = 'solarapp_auth_token'
const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || '')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    localStorage.setItem(TOKEN_KEY, token)
    authApi
      .me()
      .then((response) => setUser(response.data))
      .catch(() => {
        setToken('')
        setUser(null)
        localStorage.removeItem(TOKEN_KEY)
      })
      .finally(() => setLoading(false))
  }, [token])

  useEffect(() => {
    const requestInterceptor = api.interceptors.request.use((config) => {
      const storedToken = localStorage.getItem(TOKEN_KEY)
      if (storedToken) {
        config.headers.Authorization = `Bearer ${storedToken}`
      }
      return config
    })

    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error?.response?.status === 401) {
          localStorage.removeItem(TOKEN_KEY)
          setToken('')
          setUser(null)
        }
        return Promise.reject(error)
      }
    )

    return () => {
      api.interceptors.request.eject(requestInterceptor)
      api.interceptors.response.eject(responseInterceptor)
    }
  }, [])

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated: Boolean(token && user),
      loginWithGoogle: async (idToken) => {
        const response = await authApi.google(idToken)
        const nextToken = response.data?.access_token || ''
        setToken(nextToken)
        setUser(response.data?.user || null)
        localStorage.setItem(TOKEN_KEY, nextToken)
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY)
        setToken('')
        setUser(null)
      },
    }),
    [loading, token, user]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
