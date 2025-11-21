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
import { TreeView } from '@/components/ui/tree-view'

export default function ProjectDetailSidebar({ project, documents, activeDocumentId, onCreateDocument }) {
  const navigate = useNavigate();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  const buildTreeData = (docs, parentId = null) => {
    return docs
      .filter((doc) => doc.parent_id === parentId)
      .map((doc) => {
        const item = {
          id: doc.id,
          name: doc.name,
          icon: doc.type === 'markdown' ? FileText : Image,
          draggable: false,
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