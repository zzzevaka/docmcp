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
      // Create document from template
      const response = await axios.post(
        `/api/v1/projects/${selectedProjectId}/documents/`,
        {
          name: template.name,
          type: template.type,
          content: template.content,
        },
        { withCredentials: true }
      );

      toast.success('Template added to project!');
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
            <FolderPlus className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Add to Project</h2>
            <p className="mt-1 text-sm text-gray-600">
              Add "{template.name}" as a document to a project
            </p>
          </div>
        </div>

        {loading ? (
          <div className="py-8 text-center text-gray-500">
            Loading projects...
          </div>
        ) : projects.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            No projects available. Please create a project first.
          </div>
        ) : (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Project
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            disabled={adding}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleAdd}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={adding || loading || projects.length === 0}
          >
            {adding ? 'Adding...' : 'Add to Project'}
          </button>
        </div>
      </div>
    </div>
  );
}
