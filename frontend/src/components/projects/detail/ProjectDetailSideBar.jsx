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
import { FileText, Image, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { TreeView } from '@/components/ui/tree-view'

export default function ProjectDetailSidebar({ project, documents, activeDocumentId, onCreateDocument, onDocumentsChange }) {
  const navigate = useNavigate();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

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
      alert(`Failed to reorder document: ${error.response?.data?.detail || error.message}`);
    }
  }

  return (
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
            <span className="font-semibold p-1.5">{ project.name }</span>
            <button
              onClick={onCreateDocument}
              className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
              title="Create new document"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
        )}
      </SidebarHeader>
      <SidebarContent>
        {!isCollapsed && (
          <SidebarGroup>
            <SidebarGroupLabel>Documents</SidebarGroupLabel>
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
  )
}