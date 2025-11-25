import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { FolderPlus } from 'lucide-react';

export default function AddTemplateToProjectModal({ template, onClose }) {
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
    <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
            <FolderPlus className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Add to Project</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Add "{template.name}" and all its children as documents to a project
            </p>
          </div>
        </div>

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

        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
            disabled={adding}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleAdd}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90 disabled:opacity-50"
            disabled={adding || loading || projects.length === 0}
          >
            {adding ? 'Adding...' : 'Add to Project'}
          </button>
        </div>
      </div>
    </div>
  );
}
