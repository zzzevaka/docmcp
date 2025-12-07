import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { toast } from 'sonner'
import { Trash2, Copy } from 'lucide-react'
import MainLayout from '../components/layout/MainLayout'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

function ProfileSettings() {
  const [tokens, setTokens] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [tokenToDelete, setTokenToDelete] = useState(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newTokenName, setNewTokenName] = useState('')
  const dataFetched = useRef(false)

  const fetchTokens = async () => {
    try {
      const response = await axios.get('/api/v1/api-tokens/', { withCredentials: true })
      setTokens(response.data)
    } catch (error) {
      console.error('Failed to fetch API tokens:', error)
      toast.error('Failed to fetch API tokens')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Prevent double fetch in React StrictMode
    if (dataFetched.current) return
    dataFetched.current = true
    fetchTokens()
  }, [])

  const handleDeleteClick = (token) => {
    setTokenToDelete(token)
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!tokenToDelete) return

    try {
      await axios.delete(`/api/v1/api-tokens/${tokenToDelete.id}`, { withCredentials: true })
      toast.success('Token deleted successfully')
      setDeleteDialogOpen(false)
      setTokenToDelete(null)
      fetchTokens()
    } catch (error) {
      console.error('Failed to delete token:', error)
      toast.error('Failed to delete token')
    }
  }

  const handleCreateToken = async (e) => {
    e.preventDefault()
    if (!newTokenName.trim()) return

    try {
      await axios.post(
        '/api/v1/api-tokens/',
        { name: newTokenName },
        { withCredentials: true }
      )
      setNewTokenName('')
      setCreateDialogOpen(false)
      toast.success('Token created successfully')
      fetchTokens()
    } catch (error) {
      console.error('Failed to create token:', error)
      toast.error('Failed to create token')
    }
  }

  const handleCloseCreateDialog = () => {
    setCreateDialogOpen(false)
    setNewTokenName('')
  }

  const content = (
    loading
      ? null
      : tokens.length === 0 ? (
      <div className="text-sm text-muted-foreground">
        No API tokens yet. Create one to get started.
      </div>
    ) : (
      <div className="space-y-3">
        {tokens.map((token) => (
          <div
            key={token.id}
            className="bg-card border border-border p-4 rounded-lg shadow-sm flex justify-between items-center"
          >
            <div className="flex-1 min-w-0">
              <h3 className="text-base font-medium text-card-foreground mb-1">
                {token.name}
              </h3>
              <p className="text-sm text-muted-foreground mb-2">
                Created {new Date(token.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="flex gap-2 ml-4">
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(token.token)
                    toast.success('Token copied to clipboard')
                  } catch (error) {
                    toast.error('Failed to copy token')
                  }
                }}
                className="p-2 text-muted-foreground hover:bg-accent rounded-md transition-colors"
                title="Copy token"
              >
                <Copy className="h-5 w-5" />
              </button>
              <button
                onClick={() => handleDeleteClick(token)}
                className="p-2 text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                title="Delete token"
              >
                <Trash2 className="h-5 w-5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    )
  )

  return (
    <MainLayout>
      <div className="py-6">
        {/* Header */}
        <div className="mb-6 pb-12">
          <Breadcrumb>
            <BreadcrumbList className="text-2xl">
              <BreadcrumbItem>
                <BreadcrumbPage className="font-bold">Profile Settings</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        {/* API Tokens Section */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">API Tokens</h2>
            <button
              onClick={() => setCreateDialogOpen(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Create new token
            </button>
          </div>

          {content}
        </div>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Delete API Token</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{tokenToDelete?.name}"? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setDeleteDialogOpen(false)
                  setTokenToDelete(null)
                }}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="destructive"
                onClick={handleConfirmDelete}
              >
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Create Token Dialog */}
        <Dialog open={createDialogOpen} onOpenChange={(open) => {
          if (!open) handleCloseCreateDialog()
        }}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create New API Token</DialogTitle>
              <DialogDescription>
                Enter a name for your new API token.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateToken}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Token Name
                </label>
                <input
                  type="text"
                  value={newTokenName}
                  onChange={(e) => setNewTokenName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="e.g., Production Server, Development Environment"
                  autoFocus
                  required
                />
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCloseCreateDialog}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  Create Token
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </MainLayout>
  )
}

export default ProfileSettings
