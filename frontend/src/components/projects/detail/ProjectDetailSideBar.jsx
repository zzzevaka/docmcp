import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarTrigger,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarGroup,
  useSidebar,
} from "@/components/ui/sidebar"
import { FileText, Image, Plus, MoreHorizontal, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { TreeView } from '@/components/ui/tree-view'
import EditDocumentModal from '@/components/documents/EditDocumentModal'
import DeleteDocumentModal from '@/components/documents/DeleteDocumentModal'
import DocumentActionsModal from '@/components/documents/DocumentActionsModal'
import CreateTemplateModal from '@/components/documents/CreateTemplateModal'
import ProjectActionsModal from '@/components/projects/ProjectActionsModal'
import EditProjectModal from '@/components/projects/EditProjectModal'
import DeleteProjectModal from '@/components/projects/DeleteProjectModal'
import MCPInstructionsModal from '@/components/projects/MCPInstructionsModal'

export default function ProjectDetailSidebar({ project, documents, activeDocumentId, onCreateDocument, onDocumentsChange, onCreateTemplate, onProjectDelete, onProjectUpdate, onDocumentUpdate, onDocumentDelete }) {
  const navigate = useNavigate();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const [editingDocument, setEditingDocument] = useState(null);
  const [deletingDocument, setDeletingDocument] = useState(null);
  const [actionsDocument, setActionsDocument] = useState(null);
  const [creatingTemplateDocument, setCreatingTemplateDocument] = useState(null);
  const [showProjectActions, setShowProjectActions] = useState(false);
  const [editingProject, setEditingProject] = useState(false);
  const [deletingProject, setDeletingProject] = useState(false);
  const [showMCPInstructions, setShowMCPInstructions] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleEditDocument = async (documentId, newName) => {
    try {
      await axios.put(
        `/api/v1/projects/${project.id}/documents/${documentId}`,
        { name: newName },
        { withCredentials: true }
      );

      // Update document in store
      if (onDocumentUpdate) {
        onDocumentUpdate(documentId, { name: newName });
      }
    } catch (error) {
      console.error('Failed to update document:', error);
      toast.error(`Failed to update document: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const handleToggleEditableByAgent = async (documentId, editableByAgent) => {
    try {
      await axios.put(
        `/api/v1/projects/${project.id}/documents/${documentId}`,
        { editable_by_agent: editableByAgent },
        { withCredentials: true }
      );

      // Update the actionsDocument state immediately to reflect the change in the modal
      if (actionsDocument && actionsDocument.id === documentId) {
        setActionsDocument({ ...actionsDocument, editable_by_agent: editableByAgent });
      }

      // Update document in store
      if (onDocumentUpdate) {
        onDocumentUpdate(documentId, { editable_by_agent: editableByAgent });
      }

      toast.success(editableByAgent ? 'Document is now editable by AI' : 'Document is no longer editable by AI');
    } catch (error) {
      console.error('Failed to update document:', error);
      toast.error(`Failed to update document: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const handleDeleteDocument = async (documentId) => {
    try {
      await axios.delete(
        `/api/v1/projects/${project.id}/documents/${documentId}`,
        { withCredentials: true }
      );

      // Update document in store
      if (onDocumentDelete) {
        onDocumentDelete(documentId);
      }

      // If deleting the currently active document, redirect to project page
      if (documentId === activeDocumentId) {
        navigate(`/projects/${project.id}`);
      }
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast.error(`Failed to delete document: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const handleEditProject = async (newName) => {
    try {
      await axios.put(
        `/api/v1/projects/${project.id}`,
        { name: newName },
        { withCredentials: true }
      );

      // Update project in both stores
      if (onProjectUpdate) {
        onProjectUpdate(project.id, { name: newName });
      }
      if (onDocumentsChange) {
        await onDocumentsChange();
      }
      toast.success('Project renamed successfully');
    } catch (error) {
      console.error('Failed to update project:', error);
      toast.error(`Failed to update project: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const handleDeleteProject = async () => {
    try {
      await axios.delete(
        `/api/v1/projects/${project.id}`,
        { withCredentials: true }
      );

      // Update projects store
      if (onProjectDelete) {
        onProjectDelete(project.id);
      }

      toast.success('Project deleted successfully');
      navigate('/');
    } catch (error) {
      console.error('Failed to delete project:', error);
      toast.error(`Failed to delete project: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const handleExportProject = async () => {
    try {
      setIsExporting(true);

      const response = await axios.get(
        `/api/v1/projects/${project.id}/export`,
        {
          withCredentials: true,
          responseType: 'blob'
        }
      );

      // Create blob URL and initiate download
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Get filename from Content-Disposition header or generate
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${project.name}_export_${Date.now()}.zip`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);

      toast.success('Project exported successfully');
    } catch (error) {
      console.error('Failed to export project:', error);
      toast.error(`Failed to export project: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const buildTreeData = (docs, parentId = null) => {
    if (!docs) return [];

    return docs
      .filter((doc) => doc.parent_id === parentId)
      .sort((a, b) => a.order - b.order)
      .map((doc) => {
        const item = {
          id: doc.id,
          name: doc.name,
          icon: doc.type === 'markdown' ? FileText : Image,
          draggable: true,
          actions: (
            <div
              onClick={(e) => {
                e.stopPropagation();
                setActionsDocument(doc);
              }}
              className="p-1 hover:bg-gray-200 rounded transition-all cursor-pointer"
              title="Document actions"
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  e.stopPropagation();
                  setActionsDocument(doc);
                }
              }}
            >
              <MoreHorizontal className="w-3 h-3 text-gray-600" />
            </div>
          ),
        }

        const children = buildTreeData(docs, doc.id);

        if (children.length) {
          item.children = children;
        }

        return item;
      });
  }

  const treeData = buildTreeData(documents);

  const handleDocumentSelected = (item) => {
    navigate(`/projects/${project.id}/documents/${item.id}`);
  }

  const handleDocumentDrag = async (draggedItem, targetItem, dropZone = 'on') => {
    if (!documents) return;

    try {
      // Find the dragged and target documents
      const draggedDoc = documents.find(d => d.id === draggedItem.id);
      if (!draggedDoc) return;

      // Determine new parent_id and order based on drop zone
      let newParentId = null;
      let newOrder = 0;

      // If target is the parent div (root level), set parent to null
      if (targetItem.name === 'parent_div') {
        newParentId = null;
        // Calculate order: find max order of root-level documents + 1
        const rootDocs = documents.filter(d => d.parent_id === null && d.id !== draggedDoc.id);
        newOrder = rootDocs.length > 0 ? Math.max(...rootDocs.map(d => d.order)) + 1 : 0;
      } else {
        const targetDoc = documents.find(d => d.id === targetItem.id);
        if (!targetDoc) return;

        if (dropZone === 'on') {
          // Dropped ON the element - make it a child
          newParentId = targetDoc.id;
          // Calculate order: find max order of target's children + 1
          const children = documents.filter(d => d.parent_id === newParentId && d.id !== draggedDoc.id);
          newOrder = children.length > 0 ? Math.max(...children.map(d => d.order)) + 1 : 0;
        } else if (dropZone === 'before') {
          // Dropped BEFORE the element - insert at same level, before target
          newParentId = targetDoc.parent_id;
          newOrder = targetDoc.order;

          // Update orders of siblings that come at or after the insert position
          const siblings = documents.filter(d =>
            d.parent_id === newParentId &&
            d.id !== draggedDoc.id &&
            d.order >= newOrder
          ).sort((a, b) => a.order - b.order);

          // Update their orders to make room
          for (let i = 0; i < siblings.length; i++) {
            const sibling = siblings[i];
            await axios.put(
              `/api/v1/projects/${project.id}/documents/${sibling.id}`,
              { order: newOrder + i + 1 },
              { withCredentials: true }
            );
          }
        } else if (dropZone === 'after') {
          // Dropped AFTER the element - insert at same level, after target
          newParentId = targetDoc.parent_id;
          newOrder = targetDoc.order + 1;

          // Update orders of siblings that come after the insert position
          const siblings = documents.filter(d =>
            d.parent_id === newParentId &&
            d.id !== draggedDoc.id &&
            d.order >= newOrder
          ).sort((a, b) => a.order - b.order);

          // Update their orders to make room
          for (let i = 0; i < siblings.length; i++) {
            const sibling = siblings[i];
            await axios.put(
              `/api/v1/projects/${project.id}/documents/${sibling.id}`,
              { order: newOrder + i + 1 },
              { withCredentials: true }
            );
          }
        }
      }

      // Update dragged document with new parent and order
      await axios.put(
        `/api/v1/projects/${project.id}/documents/${draggedDoc.id}`,
        {
          parent_id: newParentId,
          order: newOrder
        },
        { withCredentials: true }
      );

      // Refresh documents list
      if (onDocumentsChange) {
        await onDocumentsChange();
      }
    } catch (error) {
      console.error('Failed to reorder document:', error);
      toast.error(`Failed to reorder document: ${error.response?.data?.detail || error.message}`);
    }
  }

  if (!project) return null;

  return (
    <>
    <Sidebar collapsible="icon">
      <SidebarHeader>
        {isCollapsed ? (
          <div className="flex items-center justify-center">
            <button
              onClick={onCreateDocument}
              className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
              title="Create new document"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
              title="Back to home"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <span
              className="font-semibold truncate"
              title={ project.name }
            >
              { project.name }
            </span>
            <button
              onClick={() => setShowProjectActions(true)}
              className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
              title="Project actions"
            >
              <MoreHorizontal className="w-5 h-5" />
            </button>
          </div>
        )}
      </SidebarHeader>
      <SidebarContent>
        {!isCollapsed && (
          <SidebarGroup>
            <div className="flex items-center justify-between px-2 py-1.5">
              <SidebarGroupLabel>Documents</SidebarGroupLabel>
              <button
                onClick={onCreateDocument}
                className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                title="Create new document"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <SidebarGroupContent>
              {treeData.length > 0 ? (
                <TreeView
                  data={treeData}
                  initialSelectedItemId={activeDocumentId}
                  onSelectChange={handleDocumentSelected}
                  onDocumentDrag={handleDocumentDrag}
                  defaultLeafIcon={FileText}
                  defaultNodeIcon={FileText}
                />
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-muted-foreground mb-3">
                    No documents yet
                  </p>
                  <button
                    onClick={onCreateDocument}
                    className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Create First Document
                  </button>
                </div>
              )}
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>
      <SidebarFooter>
        <SidebarTrigger />
      </SidebarFooter>
    </Sidebar>

    {/* Document Actions Modal */}
    {actionsDocument && (
      <DocumentActionsModal
        document={actionsDocument}
        isOpen={true}
        onClose={() => setActionsDocument(null)}
        onEdit={() => setEditingDocument(actionsDocument)}
        onDelete={() => setDeletingDocument(actionsDocument)}
        onCreateTemplate={() => setCreatingTemplateDocument(actionsDocument)}
        onToggleEditableByAgent={handleToggleEditableByAgent}
      />
    )}

    {/* Edit Document Modal */}
    {editingDocument && (
      <EditDocumentModal
        document={editingDocument}
        isOpen={true}
        onClose={() => setEditingDocument(null)}
        onSave={(newName) => handleEditDocument(editingDocument.id, newName)}
      />
    )}

    {/* Delete Document Modal */}
    {deletingDocument && (
      <DeleteDocumentModal
        document={deletingDocument}
        isOpen={true}
        onClose={() => setDeletingDocument(null)}
        onDelete={() => handleDeleteDocument(deletingDocument.id)}
      />
    )}

    {/* Create Template Modal */}
    {creatingTemplateDocument && onCreateTemplate && (
      <CreateTemplateModal
        document={creatingTemplateDocument}
        teamName={project.team?.name}
        isOpen={true}
        onClose={() => setCreatingTemplateDocument(null)}
        onSuccess={onCreateTemplate}
      />
    )}

    {/* Project Actions Modal */}
    <ProjectActionsModal
      project={project}
      isOpen={showProjectActions}
      onClose={() => setShowProjectActions(false)}
      onEdit={() => setEditingProject(true)}
      onDelete={() => setDeletingProject(true)}
      onConnectMCP={() => setShowMCPInstructions(true)}
      onExport={handleExportProject}
    />

    {/* Edit Project Modal */}
    <EditProjectModal
      project={project}
      isOpen={editingProject}
      onClose={() => setEditingProject(false)}
      onSave={handleEditProject}
    />

    {/* Delete Project Modal */}
    <DeleteProjectModal
      project={project}
      isOpen={deletingProject}
      onClose={() => setDeletingProject(false)}
      onDelete={handleDeleteProject}
    />

    {/* MCP Instructions Modal */}
    <MCPInstructionsModal
      project={project}
      isOpen={showMCPInstructions}
      onClose={() => setShowMCPInstructions(false)}
    />
  </>
  )
}