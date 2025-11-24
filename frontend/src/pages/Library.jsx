import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import MainLayout from '@/components/layout/MainLayout';
import SearchBar from '@/components/common/SearchBar';
import CategoryPill from '@/components/library/CategoryPill';
import TemplateCard from '@/components/library/TemplateCard';
import AddTemplateToProjectModal from '@/components/library/AddTemplateToProjectModal';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

export default function Library() {
  const navigate = useNavigate();
  const { categoryId } = useParams();
  const [categories, setCategories] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    if (categoryId) {
      const selected = categories.find(c => c.id === categoryId);
      setSelectedCategory(selected);
    } else {
      setSelectedCategory(null);
    }
  }, [categoryId, categories]);

  useEffect(() => {
    // Don't fetch templates if we're waiting for categories to load
    // (when categoryId is present in URL but selectedCategory is not yet set)
    if (categoryId && !selectedCategory && categories.length === 0) {
      return;
    }
    fetchTemplates();
  }, [selectedCategory, searchQuery, categoryId, categories.length]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/api/v1/library/categories/', {
        withCredentials: true,
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const params = {};
      if (selectedCategory) {
        params.category_name = selectedCategory.name;
      }

      const response = await axios.get('/api/v1/library/templates/', {
        params,
        withCredentials: true,
      });
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (category) => {
    if (selectedCategory?.id === category.id) {
      navigate('/library/categories');
    } else {
      navigate(`/library/categories/${category.id}`);
    }
  };

  const handleTemplateClick = (template) => {
    navigate(`/library/templates/${template.id}`);
  };

  // Group templates by category for display
  const templatesByCategory = categories.reduce((acc, category) => {
    acc[category.id] = templates.filter(t => t.category_id === category.id);
    return acc;
  }, {});

  // Filter templates by search query
  const filteredTemplates = searchQuery
    ? templates.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : templates;

  if (selectedCategory) {
    // Focused category view - /library/categories/<uuid>/
    return (
      <MainLayout activeTab="library">
        <div className="h-full flex flex-col">
          {/* Header with breadcrumbs and search */}
          <div className="px-6 py-4 flex items-center justify-between gap-4">
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink href="/library/categories">Library</BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>{selectedCategory.name}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            <div className="w-80">
              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search..."
              />
            </div>
          </div>

          {/* Templates grid */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-gray-500">Loading templates...</div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {filteredTemplates.map(template => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      onClick={() => handleTemplateClick(template)}
                    />
                  ))}
                </div>
                {filteredTemplates.length === 0 && (
                  <div className="text-center text-gray-500 py-12">
                    No templates found
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </MainLayout>
    );
  }

  // Multi-category view - /library/categories/
  return (
    <MainLayout activeTab="library">
      <div className="h-full flex flex-col">
        {/* Header with title and search */}
        <div className="px-6 py-4 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Library</h1>
          <div className="w-80">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search..."
            />
          </div>
        </div>

        {/* Templates by category */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading templates...</div>
            </div>
          ) : (
            <div className="space-y-8">
              {categories.map(category => {
                const categoryTemplates = searchQuery
                  ? filteredTemplates.filter(t => t.category_id === category.id)
                  : templatesByCategory[category.id] || [];

                if (categoryTemplates.length === 0) return null;

                return (
                  <div key={category.id}>
                    <h2
                      className="text-lg font-semibold mb-4 cursor-pointer hover:text-blue-600 transition-colors"
                      onClick={() => handleCategoryClick(category)}
                    >
                      {category.name}
                    </h2>
                    <div className="flex gap-4 overflow-x-auto pb-2">
                      {categoryTemplates.map(template => (
                        <div key={template.id} className="flex-shrink-0 w-64">
                          <TemplateCard
                            template={template}
                            onClick={() => handleTemplateClick(template)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
              {filteredTemplates.length === 0 && (
                <div className="text-center text-gray-500 py-12">
                  {searchQuery ? 'No templates found matching your search' : 'No templates available'}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
