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

export default function ProjectDetailSidebar({ project, documents, activeDocumentId, onCreateDocument, onDocumentsChange, onCreateTemplate }) {
  const navigate = useNavigate();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const [editingDocument, setEditingDocument] = useState(null);
  const [deletingDocument, setDeletingDocument] = useState(null);
  const [actionsDocument, setActionsDocument] = useState(null);
  const [creatingTemplateDocument, setCreatingTemplateDocument] = useState(null);

  const handleEditDocument = async (documentId, newName) => {
    try {
      await axios.put(
        `/api/v1/projects/${project.id}/documents/${documentId}`,
        { name: newName },
        { withCredentials: true }
      );

      if (onDocumentsChange) {
        await onDocumentsChange();
      }
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

      if (onDocumentsChange) {
        await onDocumentsChange();
      }
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast.error(`Failed to delete document: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const buildTreeData = (docs, parentId = null) => {
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
            <button
              onClick={(e) => {
                e.stopPropagation();
                setActionsDocument(doc);
              }}
              className="p-1 hover:bg-gray-200 rounded transition-all opacity-40 hover:opacity-100"
              title="Document actions"
            >
              <MoreHorizontal className="w-3.5 h-3.5 text-gray-600" />
            </button>
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
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/')}
                className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                title="Back to home"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <span className="font-semibold">{ project.name }</span>
            </div>
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
        onClose={() => setActionsDocument(null)}
        onEdit={() => setEditingDocument(actionsDocument)}
        onDelete={() => setDeletingDocument(actionsDocument)}
        onCreateTemplate={() => setCreatingTemplateDocument(actionsDocument)}
      />
    )}

    {/* Edit Document Modal */}
    {editingDocument && (
      <EditDocumentModal
        document={editingDocument}
        onClose={() => setEditingDocument(null)}
        onSave={(newName) => handleEditDocument(editingDocument.id, newName)}
      />
    )}

    {/* Delete Document Modal */}
    {deletingDocument && (
      <DeleteDocumentModal
        document={deletingDocument}
        onClose={() => setDeletingDocument(null)}
        onDelete={() => handleDeleteDocument(deletingDocument.id)}
      />
    )}

    {/* Create Template Modal */}
    {creatingTemplateDocument && onCreateTemplate && (
      <CreateTemplateModal
        document={creatingTemplateDocument}
        onClose={() => setCreatingTemplateDocument(null)}
        onSuccess={onCreateTemplate}
      />
    )}
  </>
  )
}