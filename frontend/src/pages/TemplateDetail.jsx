import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Trash2, FolderPlus } from 'lucide-react';

import MainLayout from '@/components/layout/MainLayout';
import MarkdownEditor from '@/components/editors/MarkdownEditor';
import ExcalidrawEditor from '@/components/editors/ExcalidrawEditor';
import { useAuth } from '@/contexts/AuthContext';
import AddTemplateToProjectModal from '@/components/library/AddTemplateToProjectModal';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
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
  const [loading, setLoading] = useState(true);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAddToProjectModal, setShowAddToProjectModal] = useState(false);
  const excalidrawRef = useRef(null);

  useEffect(() => {
    fetchTemplate();
  }, [templateId]);

  const fetchTemplate = async () => {
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

      console.log('Template loaded:', templateData);
      setTemplate(templateData);
    } catch (error) {
      console.error('Failed to fetch template:', error);
      if (error.response?.status === 404 || error.response?.status === 403) {
        navigate('/library/categories');
      }
    } finally {
      setLoading(false);
    }
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
      <MainLayout activeTab="library">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading template...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (!template) {
    return (
      <MainLayout activeTab="library">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-gray-600">Template not found</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  // Check if user is member of the template's team
  const isTeamMember = user?.teams?.some(team => String(team.id) === String(template.team_id));
  const canDelete = isTeamMember;

  return (
    <MainLayout activeTab="library">
      <div className="flex flex-col" style={{ height: 'calc(100vh - 8rem)' }}>
        {/* Header */}
        <div className="border-b px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink href="/library/categories">Library</BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                {template.category_name && (
                  <>
                    <BreadcrumbItem>
                      <BreadcrumbLink href={`/library/categories/${template.category_id || ''}`}>
                        {template.category_name}
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator />
                  </>
                )}
                <BreadcrumbItem>
                  <BreadcrumbPage>{template.name}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>

            <div className="flex gap-2">
              <button
                onClick={() => setShowAddToProjectModal(true)}
                className="p-2 hover:bg-blue-100 rounded-md transition-colors"
                title="Add to project"
              >
                <FolderPlus className="w-5 h-5 text-blue-600" />
              </button>
              {canDelete && (
                <button
                  onClick={() => setShowDeleteDialog(true)}
                  className="p-2 hover:bg-red-100 rounded-md transition-colors"
                  title="Delete template"
                >
                  <Trash2 className="w-5 h-5 text-red-600" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {template.type === 'markdown' ? (
            <MarkdownEditor
              markdown={template.content?.markdown || ''}
              onChange={() => {}}
              readOnly={true}
            />
          ) : (
            <ExcalidrawEditor
              initialData={excalidrawInitialData}
              onChange={() => {}}
              readOnly={true}
              excalidrawRef={excalidrawRef}
            />
          )}
        </div>
      </div>

      {showAddToProjectModal && (
        <AddTemplateToProjectModal
          template={template}
          onClose={() => setShowAddToProjectModal(false)}
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
    </MainLayout>
  );
}
