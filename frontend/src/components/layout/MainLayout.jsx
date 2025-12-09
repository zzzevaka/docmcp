import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor, Menu, X } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import logo from '../../static/logo.svg'

function MainLayout({ children, activeTab }) {
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()

  // Auto-detect active tab from URL if not explicitly provided
  const currentTab = activeTab || (() => {
    const path = location.pathname
    if (path.startsWith('/library')) return 'library'
    if (path.startsWith('/teams')) return 'teams'
    if (path.startsWith('/projects')) return 'projects'
    return null // No tab active (e.g., settings pages)
  })()

  const getTabClassName = (tab) => {
    const baseClass = "inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2"
    if (currentTab === tab) {
      return `${baseClass} text-primary border-primary`
    }
    return `${baseClass} text-muted-foreground hover:text-foreground border-transparent hover:border-border`
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <nav className="bg-card border-b border-border shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left side - Logo and main nav */}
            <div className="flex">
              <div className="sm:hidden inline-flex py-2 mr-2">
                <Popover modal={true}>
                  <PopoverTrigger asChild>
                    <button className="items-center justify-center px-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent">
                      <Menu className="h-6 w-6" />
                    </button>
                  </PopoverTrigger>
                  <PopoverContent align="start" className="w-48 p-1">
                    <Link
                      to="/projects"
                      className={`block px-4 py-2 text-sm rounded ${
                        currentTab === 'projects'
                          ? 'bg-primary/10 text-primary'
                          : 'text-popover-foreground hover:bg-accent'
                      }`}
                    >
                      Projects
                    </Link>
                    <Link
                      to="/library/categories"
                      className={`block px-4 py-2 text-sm rounded ${
                        currentTab === 'library'
                          ? 'bg-primary/10 text-primary'
                          : 'text-popover-foreground hover:bg-accent'
                      }`}
                    >
                      Library
                    </Link>
                    <Link
                      to="/teams"
                      className={`block px-4 py-2 text-sm rounded ${
                        currentTab === 'teams'
                          ? 'bg-primary/10 text-primary'
                          : 'text-popover-foreground hover:bg-accent'
                      }`}
                    >
                      Teams
                    </Link>
                  </PopoverContent>
                </Popover>
              </div>

              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <Link
                  to="/"
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                  <img
                    src={logo}
                    alt="DocuMur"
                    className="h-14 w-14 mr-1 dark:invert"
                  />
                  <span className="text-xl font-bold">
                    DocuMur
                  </span>
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
              <Popover modal={true}>
                <PopoverTrigger asChild>
                  <button className="flex items-center gap-2 p-2 rounded-full hover:bg-accent">
                    <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-medium">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                  </button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-56 p-0">
                  <div className="px-4 py-2 border-b border-border">
                    <p className="text-sm font-medium text-popover-foreground">
                      {user?.username}
                    </p>
                    <p className="text-sm text-muted-foreground truncate">
                      {user?.email}
                    </p>
                  </div>

                  {/* Theme selection */}
                  <div className="px-4 py-2 border-b border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Theme
                    </p>
                    <div className="space-y-1">
                      <button
                        onClick={() => setTheme('light')}
                        className={`flex items-center gap-2 w-full text-left px-2 py-1.5 text-sm rounded transition-colors ${
                          theme === 'light'
                            ? 'bg-primary/10 text-primary'
                            : 'text-popover-foreground hover:bg-accent'
                        }`}
                      >
                        <Sun className="h-4 w-4" />
                        <span>Light</span>
                      </button>
                      <button
                        onClick={() => setTheme('dark')}
                        className={`flex items-center gap-2 w-full text-left px-2 py-1.5 text-sm rounded transition-colors ${
                          theme === 'dark'
                            ? 'bg-primary/10 text-primary'
                            : 'text-popover-foreground hover:bg-accent'
                        }`}
                      >
                        <Moon className="h-4 w-4" />
                        <span>Dark</span>
                      </button>
                      <button
                        onClick={() => setTheme('system')}
                        className={`flex items-center gap-2 w-full text-left px-2 py-1.5 text-sm rounded transition-colors ${
                          theme === 'system'
                            ? 'bg-primary/10 text-primary'
                            : 'text-popover-foreground hover:bg-accent'
                        }`}
                      >
                        <Monitor className="h-4 w-4" />
                        <span>System</span>
                      </button>
                    </div>
                  </div>

                  <Link
                    to="/settings/profile"
                    className="block w-full text-left px-4 py-2 text-sm text-popover-foreground hover:bg-accent border-b border-border"
                  >
                    Profile Settings
                  </Link>

                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-popover-foreground hover:bg-accent rounded-b-md"
                  >
                    Logout
                  </button>
                </PopoverContent>
              </Popover>
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
