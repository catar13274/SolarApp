import { useCallback, useState } from 'react'

const STORAGE_KEY = 'solarapp_selected_company_code'

export function useCompanyScope() {
  const [companyCode, setState] = useState(() => localStorage.getItem(STORAGE_KEY) || '')

  const setCompanyCode = useCallback((code) => {
    const next = code || ''
    setState(next)
    if (next) {
      localStorage.setItem(STORAGE_KEY, next)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  return [companyCode, setCompanyCode]
}
