import { useState, useEffect, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useDropzone } from 'react-dropzone';

import { SidebarProvider, useSidebar } from "@/components/ui/sidebar";
import MainLayout from '@/components/layout/MainLayout'
import ProjectDetailSidebar from "@/components/projects/detail/ProjectDetailSideBar";
import DocumentEditor from "@/components/documents/DocumentEditor";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useProjectDetail, useProjects, useTemplates } from '@/store';

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
  const { project, documents, loading, fetchProjectData, refreshProjectData, updateDocument, deleteDocument, fetchDocumentContent } = useProjectDetail(projectId);
  const { deleteProject, updateProject } = useProjects();
  const { addTemplate } = useTemplates();
  const [activeDocument, setActiveDocument] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDocumentName, setNewDocumentName] = useState('');
  const [newDocumentType, setNewDocumentType] = useState('markdown');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [parentDocumentId, setParentDocumentId] = useState(null);

  useEffect(() => {
    fetchProjectData().catch((error) => {
      if (error.response?.status === 404) {
        navigate('/projects')
      }
    })
  }, [projectId, fetchProjectData, navigate]);

  useEffect(() => {
    if (!loading && documents) {
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
      setIsUploading(true);

      let response;

      // If there's an uploaded file (Jupyter notebook), use the upload endpoint
      if (uploadedFile && newDocumentType === 'markdown') {
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('name', newDocumentName);

        response = await axios.post(
          `/api/v1/projects/${projectId}/documents/from-file`,
          formData,
          {
            withCredentials: true,
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );
      } else {
        // Regular document creation
        response = await axios.post(
          `/api/v1/projects/${projectId}/documents/`,
          {
            name: newDocumentName,
            type: newDocumentType,
            content: newDocumentType === 'markdown' ? { markdown: '' } : { raw: { elements: [], appState: {}, files: {} } },
            parent_id: parentDocumentId,
          },
          { withCredentials: true }
        );
      }

      setNewDocumentName('');
      setUploadedFile(null);
      setParentDocumentId(null);
      setShowCreateModal(false);
      await refreshProjectData();
      navigate(`/projects/${projectId}/documents/${response.data.id}`);
    } catch (error) {
      console.error('Failed to create document:', error);
      toast.error(`Failed to create document: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const supportedExtensions = ['.ipynb', '.md', '.txt'];
      const hasValidExtension = supportedExtensions.some(ext => file.name.endsWith(ext));

      if (!hasValidExtension) {
        toast.error('This file is not supported. Supported formats: .ipynb, .md, .txt');
        return;
      }
      setUploadedFile(file);
      // Auto-fill document name from filename if empty
      if (!newDocumentName) {
        // Remove extension from filename
        const nameWithoutExt = file.name.replace(/\.(ipynb|md|txt)$/, '');
        setNewDocumentName(nameWithoutExt);
      }
    }
  }, [newDocumentName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/x-ipynb+json': ['.ipynb'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt']
    },
    multiple: false,
    disabled: newDocumentType !== 'markdown'
  });

  const handleCreateTemplate = async (documentId, templateName, categoryName, visibility, includeChildren = false) => {
    try {
      const response = await axios.post(
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

      const newTemplate = response.data;

      // Add template to store
      addTemplate(newTemplate);

      toast.success(
        <span>
          Template <Link className="text-primary" to={`/library/templates/${newTemplate.id}`}>{newTemplate.name}</Link> created.
        </span>
      );
    } catch (error) {
      console.error('Failed to create template:', error);
      toast.error(`Failed to create template: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const handleCreateChildDocument = (parentId) => {
    setParentDocumentId(parentId);
    setShowCreateModal(true);
  };

  return (
    <>
      <SidebarProvider>
        <ProjectDetailSidebar
          project={project}
          documents={documents}
          activeDocumentId={activeDocument?.id}
          onCreateDocument={() => setShowCreateModal(true)}
          onCreateChildDocument={handleCreateChildDocument}
          onDocumentsChange={refreshProjectData}
          onCreateTemplate={handleCreateTemplate}
          onProjectDelete={deleteProject}
          onProjectUpdate={updateProject}
          onDocumentUpdate={updateDocument}
          onDocumentDelete={deleteDocument}
        />
        <div
          className="flex-1 h-screen relative overflow-x-hidden overflow-y-auto"
        >
          <MobileSidebarTrigger />
          {
            activeDocument !== null
              ? <DocumentEditor document={ activeDocument } key={activeDocument.id} onDocumentUpdate={updateDocument} onFetchContent={fetchDocumentContent} />
              : <div />
          }
        </div>
      </SidebarProvider>

      {/* Create Document Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New Document</DialogTitle>
          </DialogHeader>
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
                onChange={(e) => {
                  setNewDocumentType(e.target.value);
                  setUploadedFile(null); // Clear uploaded file when switching type
                }}
                className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="markdown">Markdown</option>
                <option value="whiteboard">Whiteboard</option>
              </select>
            </div>

            {/* Dropzone for Jupyter Notebook upload - only for Markdown documents */}
            {newDocumentType === 'markdown' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Upload a file (Optional)
                </label>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-md p-2 text-center cursor-pointer transition-colors ${
                    isDragActive
                      ? 'border-primary bg-primary/10'
                      : uploadedFile
                      ? 'border-green-500 bg-green-500/10'
                      : 'border-input hover:border-primary/50'
                  }`}
                >
                  <input {...getInputProps()} />
                  {uploadedFile ? (
                    <div className="space-y-2">
                      <div className="text-sm text-foreground font-medium">
                        📓 {uploadedFile.name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {(uploadedFile.size / 1024).toFixed(2)} KB
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setUploadedFile(null);
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  ) : isDragActive ? (
                    <p className="text-sm text-foreground">Drop the notebook here...</p>
                  ) : (
                    <div className="space-y-1">
                      <p className="text-sm text-foreground">
                        Drag & drop or click to select
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Supported formats: .ipynb, .md, .txt
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateModal(false);
                  setNewDocumentName('');
                  setNewDocumentType('markdown');
                  setUploadedFile(null);
                  setParentDocumentId(null);
                }}
                disabled={isUploading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isUploading}>
                {isUploading ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}


export default ProjectDetail;