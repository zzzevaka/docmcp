import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { ArrowLeft, Pencil, Trash2 } from 'lucide-react';

import MainLayout from '@/components/layout/MainLayout';
import MarkdownEditor from '@/components/editors/MarkdownEditor';
import ExcalidrawEditor from '@/components/editors/ExcalidrawEditor';
import { useAuth } from '@/contexts/AuthContext';
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
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const excalidrawRef = useRef(null);

  useEffect(() => {
    fetchTemplate();
  }, [templateId]);

  const fetchTemplate = async () => {
    try {
      const response = await axios.get(`/api/v1/library/templates/${templateId}`, {
        withCredentials: true,
      });
      setTemplate(response.data);

      // Parse content if it's a string
      let content = response.data.content;
      if (typeof content === 'string') {
        try {
          content = JSON.parse(content);
        } catch (e) {
          // Keep as string if parsing fails
        }
      }
      setEditedContent(content);
    } catch (error) {
      console.error('Failed to fetch template:', error);
      if (error.response?.status === 404 || error.response?.status === 403) {
        navigate('/library/categories');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      let contentToSave = editedContent;

      if (template.type === 'whiteboard' && excalidrawRef.current) {
        const sceneData = {
          elements: excalidrawRef.current.getSceneElements(),
          appState: excalidrawRef.current.getAppState(),
          files: excalidrawRef.current.getFiles(),
        };
        contentToSave = { raw: sceneData };
      }

      await axios.put(
        `/api/v1/library/templates/${templateId}`,
        { content: contentToSave },
        { withCredentials: true }
      );

      toast.success('Template saved successfully!');
      setIsEditing(false);
      await fetchTemplate();
    } catch (error) {
      console.error('Failed to save template:', error);
      toast.error(`Failed to save template: ${error.response?.data?.detail || error.message}`);
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

  const handleMarkdownChange = (data) => {
    setEditedContent({ markdown: data });
  };

  const handleExcalidrawChange = (data) => {
    setEditedContent({ raw: data });
  };

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
  const canEdit = isTeamMember;

  return (
    <MainLayout activeTab="library">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/library/categories')}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
              title="Back to library"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-semibold">{template.name}</h1>
              <p className="text-sm text-gray-500 capitalize">{template.type} template</p>
            </div>
          </div>

          {canEdit && (
            <div className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Save
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                    title="Edit template"
                  >
                    <Pencil className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setShowDeleteDialog(true)}
                    className="p-2 hover:bg-red-100 rounded-md transition-colors"
                    title="Delete template"
                  >
                    <Trash2 className="w-5 h-5 text-red-600" />
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {template.type === 'markdown' ? (
            <MarkdownEditor
              markdown={editedContent?.markdown || ''}
              onChange={handleMarkdownChange}
              readOnly={!isEditing}
            />
          ) : (
            <ExcalidrawEditor
              initialData={editedContent?.raw || { elements: [], appState: {}, files: {} }}
              onChange={handleExcalidrawChange}
              readOnly={!isEditing}
              excalidrawRef={excalidrawRef}
            />
          )}
        </div>
      </div>

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
