import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Info } from 'lucide-react'

function CookieBanner() {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Check if user has acknowledged the cookie notice
    const cookieNoticeAcknowledged = localStorage.getItem('cookieNoticeAcknowledged')
    if (!cookieNoticeAcknowledged) {
      setIsVisible(true)
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem('cookieNoticeAcknowledged', 'true')
    setIsVisible(false)
  }

  if (!isVisible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6 animate-in slide-in-from-bottom duration-300">
      <div className="max-w-5xl mx-auto">
        <div className="bg-card border border-border rounded-lg shadow-lg p-4 md:p-6">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
            <div className="flex items-start gap-3 flex-1">
              <Info className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              <div className="space-y-1.5">
                <h3 className="text-sm font-semibold text-foreground">
                  Cookie Notice
                </h3>
                <p className="text-sm text-muted-foreground">
                  This application uses cookies strictly for authentication and session management.
                  No tracking or analytics cookies are used. If you do not agree to the use of these
                  essential cookies, please leave the site.{' '}
                  <Link
                    to="/privacy-policy"
                    className="text-primary hover:text-primary/80 underline"
                  >
                    Learn more
                  </Link>
                </p>
              </div>
            </div>

            <div className="w-full md:w-auto">
              <button
                onClick={handleAccept}
                className="w-full md:w-auto px-6 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                I Understand
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CookieBanner
