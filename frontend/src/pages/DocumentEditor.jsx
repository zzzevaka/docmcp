import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { FileText, Image } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { TreeView } from '@/components/ui/tree-view'
import { Button } from '@/components/ui/button'
import MarkdownEditor from '@/components/editors/MarkdownEditor'
import ExcalidrawEditor from '@/components/editors/ExcalidrawEditor'
import MainLayout from '@/components/layout/MainLayout'

function DocumentEditor() {
  const { projectId, documentId } = useParams()
  const navigate = useNavigate()

  // Data state
  const [project, setProject] = useState(null)
  const [documents, setDocuments] = useState([])
  const [document, setDocument] = useState(null)
  const [loading, setLoading] = useState(true)

  // Editor state
  const [content, setContent] = useState(null)
  const [saving, setSaving] = useState(false)

  // UI state
  const [showActionMenu, setShowActionMenu] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newDocName, setNewDocName] = useState('')
  const [newDocType, setNewDocType] = useState('markdown')

  // Fetch all data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projectRes, documentsRes, documentRes] = await Promise.all([
          axios.get(`/api/v1/projects/${projectId}`, { withCredentials: true }),
          axios.get(`/api/v1/projects/${projectId}/documents/`, { withCredentials: true }),
          axios.get(`/api/v1/projects/${projectId}/documents/${documentId}`, { withCredentials: true }),
        ])

        setProject(projectRes.data)
        setDocuments(documentsRes.data)
        setDocument(documentRes.data)
        setContent(documentRes.data.content)
      } catch (error) {
        console.error('Failed to fetch data:', error)
        if (error.response?.status === 404) {
          navigate(`/projects/${projectId}`)
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [projectId, documentId, navigate])

  // Save document
  const handleSave = async () => {
    setSaving(true)
    try {
      await axios.put(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
        {
          name: document.name,
          content: content,
        },
        { withCredentials: true }
      )
      alert('Document saved successfully!')
    } catch (error) {
      alert('Failed to save document')
    } finally {
      setSaving(false)
    }
  }

  // Delete document
  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await axios.delete(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
        { withCredentials: true }
      )
      navigate(`/projects/${projectId}`)
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('Failed to delete document')
    }
  }

  // Create new document
  const handleCreateDocument = async (e) => {
    e.preventDefault()
    if (!newDocName.trim()) return

    try {
      const defaultContent = newDocType === 'markdown'
        ? { text: '# New Document\n\nStart writing...' }
        : { elements: [], appState: {}, files: {} }

      await axios.post(
        `/api/v1/projects/${projectId}/documents/`,
        {
          name: newDocName,
          type: newDocType,
          content: defaultContent,
          parent_id: null,
        },
        { withCredentials: true }
      )

      // Refresh documents list
      const documentsRes = await axios.get(
        `/api/v1/projects/${projectId}/documents/`,
        { withCredentials: true }
      )
      setDocuments(documentsRes.data)

      setNewDocName('')
      setNewDocType('markdown')
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create document:', error)
      alert('Failed to create document')
    }
  }

  // Build document tree for TreeView
  const buildTreeData = (docs, parentId = null) => {
    return docs
      .filter((doc) => doc.parent_id === parentId)
      .map((doc) => ({
        id: doc.id,
        name: doc.name,
        icon: doc.type === 'markdown' ? FileText : Image,
        onClick: () => navigate(`/projects/${projectId}/documents/${doc.id}`),
        children: buildTreeData(docs, doc.id),
      }))
  }

  // Loading state
  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </MainLayout>
    )
  }

  // Not found state
  if (!document || !project) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <p className="text-gray-600">Document not found</p>
        </div>
      </MainLayout>
    )
  }

  const treeData = buildTreeData(documents)

  // Handle content changes for different editor types
  const handleMarkdownChange = (markdown) => {
    setContent({ text: markdown })
  }

  const handleExcalidrawChange = (data) => {
    setContent(data)
  }

  return (
    <MainLayout>
      <SidebarProvider>
        <div className="flex w-full h-[calc(100vh-4rem)]">
          {/* Collapsible Sidebar */}
          <Sidebar collapsible="icon">
            <SidebarHeader>
              <div className="px-4 py-2">
                <h2 className="text-lg font-semibold truncate">{project.name}</h2>
              </div>
            </SidebarHeader>
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupLabel>
                  <div className="flex items-center justify-between w-full">
                    <span>Documents</span>
                  </div>
                </SidebarGroupLabel>
                <SidebarGroupContent>
                  <Button
                    onClick={() => setShowCreateModal(true)}
                    className="w-full mb-2"
                    size="sm"
                  >
                    New document +
                  </Button>
                  {treeData.length > 0 ? (
                    <TreeView
                      data={treeData}
                      initialSelectedItemId={documentId}
                      defaultLeafIcon={FileText}
                      defaultNodeIcon={FileText}
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No documents yet
                    </p>
                  )}
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>
          </Sidebar>

          {/* Main Content Area */}
          <SidebarInset className="flex-1 relative">
            <div className="flex flex-col h-full">
              {/* Header with sidebar trigger */}
              <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger />
                <div className="flex-1" />
                {/* Floating Action Menu */}
                <div className="relative">
                  <Button
                    onClick={() => setShowActionMenu(!showActionMenu)}
                    variant="ghost"
                    size="icon"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                    </svg>
                  </Button>

                  {showActionMenu && (
                    <div className="absolute right-0 mt-2 w-32 bg-background rounded-md shadow-lg border py-1 z-50">
                      <button
                        onClick={() => {
                          handleDelete()
                          setShowActionMenu(false)
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-destructive hover:bg-accent"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </header>

              {/* Document Content */}
              <div className="flex-1 overflow-hidden p-6">
                {document.type === 'markdown' ? (
                  <div className="h-full w-full">
                    <MarkdownEditor
                      markdown={content?.text || ''}
                      onChange={handleMarkdownChange}
                      readOnly={false}
                    />
                  </div>
                ) : (
                  <div className="h-full w-full border rounded-lg overflow-hidden">
                    <ExcalidrawEditor
                      initialData={content}
                      onChange={handleExcalidrawChange}
                      readOnly={false}
                    />
                  </div>
                )}
              </div>

              {/* Save Button - Bottom Right */}
              <div className="absolute bottom-6 right-6 z-10">
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  size="lg"
                >
                  {saving ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          </SidebarInset>
        </div>

        {/* Create Document Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-background rounded-lg p-6 w-full max-w-md border shadow-lg">
              <h2 className="text-2xl font-bold mb-4">Create New Document</h2>
              <form onSubmit={handleCreateDocument}>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">
                    Document Name
                  </label>
                  <input
                    type="text"
                    value={newDocName}
                    onChange={(e) => setNewDocName(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Enter document name"
                    autoFocus
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">
                    Document Type
                  </label>
                  <select
                    value={newDocType}
                    onChange={(e) => setNewDocType(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="markdown">Markdown</option>
                    <option value="whiteboard">Whiteboard</option>
                  </select>
                </div>
                <div className="flex gap-2 justify-end">
                  <Button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false)
                      setNewDocName('')
                    }}
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Create</Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </SidebarProvider>
    </MainLayout>
  )
}

export default DocumentEditor
