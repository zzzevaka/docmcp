import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

import { SidebarProvider, useSidebar } from "@/components/ui/sidebar";
import MainLayout from '@/components/layout/MainLayout'
import ProjectDetailSidebar from "@/components/projects/detail/ProjectDetailSideBar";
import DocumentEditor from "@/components/documents/DocumentEditor";

// Mobile sidebar trigger component
function MobileSidebarTrigger() {
  const { toggleSidebar, isMobile } = useSidebar();

  if (!isMobile) return null;

  return (
    <div
      onClick={toggleSidebar}
      className="md:hidden fixed left-0 top-0 bottom-0 w-2 bg-gradient-to-r from-primary/50 to-transparent hover:from-primary/50 hover:w-2 transition-all cursor-pointer z-50"
      title="Open menu"
    />
  );
}

function ProjectDetail() {
  const { projectId, documentId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeDocument, setActiveDocument] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDocumentName, setNewDocumentName] = useState('');
  const [newDocumentType, setNewDocumentType] = useState('markdown');

  const fetchProjectData = async () => {
    try {
      const [projectRes, docsRes] = await Promise.all([
        axios.get(`/api/v1/projects/${projectId}`, { withCredentials: true }),
        axios.get(`/api/v1/projects/${projectId}/documents/`, { withCredentials: true }),
      ])
      setProject(projectRes.data)
      setDocuments(docsRes.data)
    } catch (error) {
      console.error('Failed to fetch project data:', error)
      if (error.response?.status === 404) {
        navigate('/projects')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjectData()
  }, [projectId]);

  useEffect(() => {
    if (!loading) {
      if (documentId) {
        const doc = documents.filter((doc) => doc.id === documentId);
        if (doc.length) {
          setActiveDocument(doc[0]);
          return;
        }
      }
      // If no documentId and documents exist, redirect to first root document by order
      if (!documentId && documents.length > 0) {
        const rootDocuments = documents
          .filter((doc) => doc.parent_id === null)
          .sort((a, b) => a.order - b.order);
        if (rootDocuments.length > 0) {
          navigate(`/projects/${projectId}/documents/${rootDocuments[0].id}`, { replace: true });
          return;
        }
      }
      setActiveDocument(null);
    }
  }, [documentId, loading, documents, navigate, projectId]);

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    if (!newDocumentName.trim()) return;

    try {
      const response = await axios.post(
        `/api/v1/projects/${projectId}/documents/`,
        {
          name: newDocumentName,
          type: newDocumentType,
          content: newDocumentType === 'markdown' ? { markdown: '' } : { raw: { elements: [], appState: {}, files: {} } },
        },
        { withCredentials: true }
      );

      setNewDocumentName('');
      setShowCreateModal(false);
      await fetchProjectData();
      navigate(`/projects/${projectId}/documents/${response.data.id}`);
    } catch (error) {
      console.error('Failed to create document:', error);
      toast.error(`Failed to create document: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleCreateTemplate = async (documentId, templateName, categoryName, visibility, includeChildren = false) => {
    try {
      await axios.post(
        `/api/v1/library/templates/`,
        {
          document_id: documentId,
          name: templateName,
          category_name: categoryName,
          visibility: visibility,
          include_children: includeChildren,
        },
        { withCredentials: true }
      );
      toast.success('Template created successfully!');
    } catch (error) {
      console.error('Failed to create template:', error);
      toast.error(`Failed to create template: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  if (loading) {
    return null;
  }

  return (
    <>
      <SidebarProvider>
        <ProjectDetailSidebar
          project={project}
          documents={documents}
          activeDocumentId={activeDocument?.id}
          onCreateDocument={() => setShowCreateModal(true)}
          onDocumentsChange={fetchProjectData}
          onCreateTemplate={handleCreateTemplate}
        />
        <div
          className="h-screen w-full relative"
        >
          <MobileSidebarTrigger />
          {
            activeDocument !== null
              ? <DocumentEditor document={ activeDocument } key={activeDocument.id} />
              : <div />
          }
        </div>
      </SidebarProvider>

      {/* Create Document Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
          <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
            <h2 className="text-2xl font-bold mb-4 text-foreground">Create New Document</h2>
            <form onSubmit={handleCreateDocument}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Document Name
                </label>
                <input
                  type="text"
                  value={newDocumentName}
                  onChange={(e) => setNewDocumentName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Enter document name"
                  autoFocus
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Document Type
                </label>
                <select
                  value={newDocumentType}
                  onChange={(e) => setNewDocumentType(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="markdown">Markdown</option>
                  <option value="whiteboard">Whiteboard</option>
                </select>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewDocumentName('');
                    setNewDocumentType('markdown');
                  }}
                  className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}


export default ProjectDetail;