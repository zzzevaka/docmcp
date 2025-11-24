import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

function MainLayout({ children, activeTab = 'projects' }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const getTabClassName = (tab) => {
    const baseClass = "inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2"
    if (activeTab === tab) {
      return `${baseClass} text-blue-600 border-blue-600`
    }
    return `${baseClass} text-gray-500 hover:text-gray-900 border-transparent hover:border-gray-300`
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left side - Logo and main nav */}
            <div className="flex">
              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <Link
                  to="/"
                  className="text-xl font-bold text-blue-600 hover:text-blue-700"
                >
                  DocMCP
                </Link>
              </div>

              {/* Main Navigation */}
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                <Link
                  to="/projects"
                  className={getTabClassName('projects')}
                >
                  Projects
                </Link>
                <Link
                  to="/library/categories"
                  className={getTabClassName('library')}
                >
                  Library
                </Link>
                <Link
                  to="/teams"
                  className={getTabClassName('teams')}
                >
                  Teams
                </Link>
              </div>
            </div>

            {/* Right side - User menu */}
            <div className="flex items-center">
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 p-2 rounded-full hover:bg-gray-100"
                >
                  <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                </button>

                {/* User dropdown menu */}
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border border-gray-200">
                    <div className="px-4 py-2 border-b border-gray-200">
                      <p className="text-sm font-medium text-gray-900">
                        {user?.username}
                      </p>
                      <p className="text-sm text-gray-500 truncate">
                        {user?.email}
                      </p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}

export default MainLayout
