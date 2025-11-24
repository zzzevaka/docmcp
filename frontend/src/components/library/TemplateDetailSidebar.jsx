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
import { FileText, Image, ArrowLeft, MoreHorizontal, FolderPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { TreeView } from '@/components/ui/tree-view'

export default function TemplateDetailSidebar({ template, templates, activeTemplateId, canDelete, onAddToProject, onShowActions }) {
  const navigate = useNavigate();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  const buildTreeData = (tmpls, parentId = null) => {
    return tmpls
      .filter((t) => t.parent_id === parentId)
      .sort((a, b) => a.order - b.order)
      .map((tmpl) => {
        const item = {
          id: tmpl.id,
          name: tmpl.name,
          icon: tmpl.type === 'markdown' ? FileText : Image,
          draggable: false, // Templates are read-only
        }

        const children = buildTreeData(tmpls, tmpl.id);

        if (children.length) {
          item.children = children;
        }

        return item;
      });
  }

  const treeData = buildTreeData(templates);

  const handleTemplateSelected = (item) => {
    navigate(`/library/templates/${item.id}`);
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        {isCollapsed ? (
          <div className="flex items-center justify-center">
            <button
              onClick={() => navigate('/library/categories')}
              className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
              title="Back to library"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/library/categories')}
                className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                title="Back to library"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <span className="font-semibold truncate">{template.name}</span>
            </div>
            {canDelete && (
              <button
                onClick={onShowActions}
                className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                title="Template actions"
              >
                <MoreHorizontal className="w-5 h-5" />
              </button>
            )}
          </div>
        )}
      </SidebarHeader>
      {!isCollapsed && (
        <div className="px-4 py-3">
          <button
            onClick={onAddToProject}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <FolderPlus className="w-5 h-5" />
            Add to project
          </button>
        </div>
      )}
      <SidebarContent>
        {!isCollapsed && (
          <SidebarGroup>
            <div className="flex items-center justify-between px-2 py-1.5">
              <SidebarGroupLabel>Template Structure</SidebarGroupLabel>
            </div>
            <SidebarGroupContent>
              {treeData.length > 0 ? (
                <TreeView
                  data={treeData}
                  initialSelectedItemId={activeTemplateId}
                  onSelectChange={handleTemplateSelected}
                  defaultLeafIcon={FileText}
                  defaultNodeIcon={FileText}
                />
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-muted-foreground">
                    No child templates
                  </p>
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
