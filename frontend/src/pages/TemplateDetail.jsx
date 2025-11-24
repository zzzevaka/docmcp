import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

import { SidebarProvider } from "@/components/ui/sidebar";
import TemplateDetailSidebar from '@/components/library/TemplateDetailSidebar';
import MarkdownEditor from '@/components/editors/MarkdownEditor';
import ExcalidrawEditor from '@/components/editors/ExcalidrawEditor';
import { useAuth } from '@/contexts/AuthContext';
import AddTemplateToProjectModal from '@/components/library/AddTemplateToProjectModal';
import TemplateActionsModal from '@/components/library/TemplateActionsModal';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function TemplateDetail() {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [template, setTemplate] = useState(null);
  const [allTemplates, setAllTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAddToProjectModal, setShowAddToProjectModal] = useState(false);
  const [showActionsModal, setShowActionsModal] = useState(false);
  const excalidrawRef = useRef(null);

  useEffect(() => {
    fetchTemplateData();
  }, [templateId]);

  const fetchTemplateData = async () => {
    try {
      const response = await axios.get(`/api/v1/library/templates/${templateId}`, {
        withCredentials: true,
      });

      // Parse content if it's a string
      let templateData = response.data;
      if (typeof templateData.content === 'string') {
        try {
          templateData.content = JSON.parse(templateData.content);
        } catch (e) {
          console.error('Failed to parse template content:', e);
        }
      }

      setTemplate(templateData);

      // Find root template to fetch the whole hierarchy
      await fetchTemplateHierarchy(templateData);
    } catch (error) {
      console.error('Failed to fetch template:', error);
      if (error.response?.status === 404 || error.response?.status === 403) {
        navigate('/library/categories');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplateHierarchy = async (currentTemplate) => {
    try {
      // Find the root template ID
      let rootTemplateId = currentTemplate.id;
      let checkTemplate = currentTemplate;

      // Walk up the parent chain to find root
      while (checkTemplate.parent_id) {
        const parentResponse = await axios.get(`/api/v1/library/templates/${checkTemplate.parent_id}`, {
          withCredentials: true,
        });
        checkTemplate = parentResponse.data;
        rootTemplateId = checkTemplate.id;
      }

      // Fetch all templates (including children) from the same category
      const templatesResponse = await axios.get('/api/v1/library/templates/', {
        params: {
          category_name: currentTemplate.category_name,
          only_root: false  // Get all templates including children
        },
        withCredentials: true,
      });

      // Filter to get only templates in this hierarchy (starting from root)
      const hierarchyTemplates = filterTemplateHierarchy(templatesResponse.data, rootTemplateId);
      setAllTemplates(hierarchyTemplates);
    } catch (error) {
      console.error('Failed to fetch template hierarchy:', error);
    }
  };

  const filterTemplateHierarchy = (templates, rootId) => {
    const result = [];
    const visited = new Set();

    const addTemplateAndChildren = (templateId) => {
      if (visited.has(templateId)) return;
      visited.add(templateId);

      const tmpl = templates.find(t => t.id === templateId);
      if (tmpl) {
        result.push(tmpl);
        // Find and add all children
        const children = templates.filter(t => t.parent_id === templateId);
        children.forEach(child => addTemplateAndChildren(child.id));
      }
    };

    addTemplateAndChildren(rootId);
    return result;
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`/api/v1/library/templates/${templateId}`, {
        withCredentials: true,
      });
      toast.success('Template deleted successfully!');
      navigate('/library/categories');
    } catch (error) {
      console.error('Failed to delete template:', error);
      toast.error(`Failed to delete template: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Мемоизируем initialData чтобы не создавать новый объект на каждом рендере
  // ВАЖНО: useMemo (хук) должен быть вызван ДО любых условных return'ов (правило хуков)
  const excalidrawInitialData = useMemo(() => {
    if (!template?.content?.raw) {
      return { elements: [], appState: {}, files: {} };
    }
    return template.content.raw;
  }, [template?.content?.raw]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading template...</p>
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-gray-600">Template not found</p>
        </div>
      </div>
    );
  }

  // Check if user is member of the template's team
  const isTeamMember = user?.teams?.some(team => String(team.id) === String(template.team_id));
  const canDelete = isTeamMember;

  return (
    <>
      <SidebarProvider>
        <TemplateDetailSidebar
          template={template}
          templates={allTemplates}
          activeTemplateId={template.id}
          canDelete={canDelete}
          onAddToProject={() => setShowAddToProjectModal(true)}
          onShowActions={() => setShowActionsModal(true)}
        />
        <div className="h-screen w-full pl-4 relative">
          <div className="h-full">
            {template.type === 'markdown' ? (
              <MarkdownEditor
                markdown={template.content?.markdown || ''}
                onChange={() => {}}
                readOnly={true}
                key={template.id}
              />
            ) : (
              <ExcalidrawEditor
                initialData={excalidrawInitialData}
                onChange={() => {}}
                readOnly={true}
                excalidrawRef={excalidrawRef}
                key={template.id}
              />
            )}
          </div>
        </div>
      </SidebarProvider>

      {showAddToProjectModal && (
        <AddTemplateToProjectModal
          template={template}
          onClose={() => setShowAddToProjectModal(false)}
        />
      )}

      {showActionsModal && (
        <TemplateActionsModal
          template={template}
          onClose={() => setShowActionsModal(false)}
          onDelete={() => setShowDeleteDialog(true)}
        />
      )}

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Template</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this template? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setShowDeleteDialog(false);
                handleDelete();
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
