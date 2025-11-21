import { useState, useEffect } from 'react';
import { BookTemplate } from 'lucide-react';
import axios from 'axios';
import { Combobox } from '@/components/ui/combobox';

export default function CreateTemplateModal({ document, onClose, onSuccess }) {
  const [templateName, setTemplateName] = useState(document.name);
  const [categoryName, setCategoryName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/api/v1/library/categories/', {
        withCredentials: true,
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setLoadingCategories(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!templateName.trim() || !categoryName.trim()) return;

    setIsCreating(true);
    try {
      await onSuccess(document.id, templateName.trim(), categoryName.trim());
      onClose();
    } catch (error) {
      console.error('Failed to create template:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
            <BookTemplate className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Create Template</h2>
            <p className="mt-1 text-sm text-gray-600">
              Create a template from "{document.name}" that others can use
            </p>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template Name
            </label>
            <input
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter template name"
              autoFocus
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            {loadingCategories ? (
              <div className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-500">
                Loading categories...
              </div>
            ) : (
              <Combobox
                options={categories.map(cat => ({ value: cat.name, label: cat.name }))}
                value={categoryName}
                onValueChange={setCategoryName}
                placeholder="Select or create category..."
                searchPlaceholder="Search categories..."
                emptyText="No categories found."
                allowCustom={true}
              />
            )}
            <p className="mt-1 text-xs text-gray-500">
              Select existing category or type to create a new one
            </p>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              disabled={isCreating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              disabled={isCreating || !templateName.trim() || !categoryName.trim()}
            >
              {isCreating ? 'Creating...' : 'Create Template'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
