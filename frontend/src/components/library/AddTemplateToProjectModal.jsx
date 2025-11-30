import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { FolderPlus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export default function AddTemplateToProjectModal({ template, isOpen, onClose }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/v1/projects/', {
        withCredentials: true,
      });
      setProjects(response.data);
      if (response.data.length > 0) {
        setSelectedProjectId(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!selectedProjectId) {
      toast.error('Please select a project');
      return;
    }

    setAdding(true);
    try {
      // Create document(s) from template including all children
      const response = await axios.post(
        `/api/v1/projects/${selectedProjectId}/documents/from-template/${template.id}`,
        {},
        { withCredentials: true }
      );

      toast.success('Template added to project with all children!');
      onClose();

      // Redirect to the newly created document
      navigate(`/projects/${selectedProjectId}/documents/${response.data.id}`);
    } catch (error) {
      console.error('Failed to add template to project:', error);
      toast.error(`Failed to add template: ${error.response?.data?.detail || error.message}`);
      setAdding(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <DialogTitle>Add to Project</DialogTitle>
              <p className="mt-2 text-sm text-muted-foreground">
                Add "{template.name}" and all its children as documents to a project
              </p>
            </div>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="py-8 text-center text-muted-foreground">
            Loading projects...
          </div>
        ) : projects.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No projects available. Please create a project first.
          </div>
        ) : (
          <div className="mb-6">
            <label className="block text-sm font-medium text-foreground mb-2">
              Select Project
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={adding}
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={adding}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleAdd}
            disabled={adding || loading || projects.length === 0}
          >
            {adding ? 'Adding...' : 'Add to Project'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
