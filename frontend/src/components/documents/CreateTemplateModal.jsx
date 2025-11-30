import { useState, useEffect } from 'react';
import { BookTemplate } from 'lucide-react';
import axios from 'axios';
import { Combobox } from '@/components/ui/combobox';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export default function CreateTemplateModal({ document, teamName, isOpen, onClose, onSuccess }) {
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
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
              <BookTemplate className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <DialogTitle>Create Template</DialogTitle>
              <p className="mt-2 text-sm text-muted-foreground">
                Create a template from "{document.name}" that others can use
              </p>
            </div>
          </div>
        </DialogHeader>
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
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isCreating || !templateName.trim() || !categoryName.trim()}
            >
              {isCreating ? 'Creating...' : 'Create Template'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
