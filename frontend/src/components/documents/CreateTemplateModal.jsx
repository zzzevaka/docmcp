import { useState, useEffect } from 'react';
import { BookTemplate } from 'lucide-react';
import axios from 'axios';
import { Combobox } from '@/components/ui/combobox';

export default function CreateTemplateModal({ document, teamName, onClose, onSuccess }) {
  const [templateName, setTemplateName] = useState(document.name);
  const [categoryName, setCategoryName] = useState('');
  const [visibility, setVisibility] = useState('team');
  const [includeChildren, setIncludeChildren] = useState(false);
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
      await onSuccess(document.id, templateName.trim(), categoryName.trim(), visibility, includeChildren);
      onClose();
    } catch (error) {
      console.error('Failed to create template:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
            <BookTemplate className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Create Template</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Create a template from "{document.name}" that others can use
            </p>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-foreground mb-2">
              Template Name
            </label>
            <input
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Enter template name"
              autoFocus
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-foreground mb-2">
              Category
            </label>
            {loadingCategories ? (
              <div className="w-full px-3 py-2 bg-background border border-input rounded-md text-muted-foreground">
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
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-foreground mb-2">
              Visibility
            </label>
            <div className="flex gap-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="private"
                  checked={visibility === 'private'}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="w-4 h-4 text-primary border-input focus:ring-ring"
                />
                <span className="ml-2 text-sm text-foreground">Only me</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="team"
                  checked={visibility === 'team'}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="w-4 h-4 text-primary border-input focus:ring-ring"
                />
                <span className="ml-2 text-sm text-foreground">
                  {teamName || 'Team'}
                </span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="public"
                  checked={visibility === 'public'}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="w-4 h-4 text-primary border-input focus:ring-ring"
                />
                <span className="ml-2 text-sm text-foreground">Public</span>
              </label>
            </div>
          </div>
          <div className="mb-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={includeChildren}
                onChange={(e) => setIncludeChildren(e.target.checked)}
                className="w-4 h-4 text-primary border-input rounded focus:ring-ring"
              />
              <span className="ml-2 text-sm text-foreground">
                Include child documents
              </span>
            </label>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
              disabled={isCreating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
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
