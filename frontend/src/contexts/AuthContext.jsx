import { createContext, useContext, useState, useEffect, useRef } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const authChecked = useRef(false)

  const checkAuth = async () => {
    try {
      const response = await axios.get('/api/v1/auth/me', {
        withCredentials: true,
      })
      setUser(response.data)
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Prevent double fetch in React StrictMode
    if (authChecked.current) return
    authChecked.current = true
    checkAuth()
  }, [])

  const logout = async () => {
    try {
      await axios.post('/api/v1/auth/logout', {}, {
        withCredentials: true,
      })
      setUser(null)
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const value = {
    user,
    loading,
    setUser,
    logout,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
