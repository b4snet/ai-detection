import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

const SentinelContext = createContext(null)

export function SentinelProvider({ children }) {
  const [status, setStatus] = useState(null)
  const [logs, setLogs] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const timerRef = useRef(null)

  const refreshStatus = useCallback(async () => {
    try {
      const s = await api.status()
      setStatus(s)
    } catch { /* server may be warming up */ }
  }, [])

  const refreshLogs = useCallback(async () => {
    try {
      const rows = await api.logs(120)
      setLogs(rows)
    } catch { /* ignore */ }
  }, [])

  const refreshAnalyses = useCallback(async () => {
    try {
      setAnalyses(await api.analyses())
    } catch { /* ignore */ }
  }, [])

  const refreshAll = useCallback(() => {
    refreshStatus()
    refreshLogs()
    refreshAnalyses()
  }, [refreshStatus, refreshLogs, refreshAnalyses])

  useEffect(() => {
    refreshAll()
    timerRef.current = setInterval(refreshAll, 5000)
    return () => clearInterval(timerRef.current)
  }, [refreshAll])

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(t)
  }, [])

  return (
    <SentinelContext.Provider
      value={{
        status, logs, analyses, loading,
        refreshStatus, refreshLogs, refreshAnalyses, refreshAll,
      }}
    >
      {children}
    </SentinelContext.Provider>
  )
}

export function useSentinel() {
  return useContext(SentinelContext)
}
