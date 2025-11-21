import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'

function AuthCallback() {
  const navigate = useNavigate()
  const { checkAuth } = useAuth()
  const [error, setError] = useState(null)

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search)
      const code = params.get('code')
      const errorParam = params.get('error')

      if (errorParam) {
        navigate('/login?error=true')
        return
      }

      if (!code) {
        navigate('/login?error=true')
        return
      }

      try {
        const redirectUri = `${window.location.origin}/auth/callback`

        await axios.post(
          '/api/v1/auth/google/callback',
          {
            code,
            redirect_uri: redirectUri,
          },
          {
            withCredentials: true,
          }
        )

        // Refresh auth state
        await checkAuth()

        // Redirect to home
        navigate('/')
      } catch (err) {
        console.error('Authentication error:', err)
        setError(err.response?.data?.detail || 'Authentication failed')
        setTimeout(() => {
          navigate('/login?error=true')
        }, 2000)
      }
    }

    handleCallback()
  }, [navigate, checkAuth])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-2">Authentication Failed</h2>
          <p className="text-gray-600">{error}</p>
          <p className="text-sm text-gray-500 mt-2">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Authenticating...</h2>
        <p className="text-gray-600">Please wait while we sign you in</p>
      </div>
    </div>
  )
}

export default AuthCallback
