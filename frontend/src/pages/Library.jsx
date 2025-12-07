import { useState, useEffect, useRef } from 'react';
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
import { useCategories, useTemplates } from '@/store';

export default function Library() {
  const navigate = useNavigate();
  const { categoryId } = useParams();
  const { categories, loading: categoriesLoading, fetchCategories } = useCategories();
  const { templates, loading: templatesLoading, fetchTemplates } = useTemplates();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const initialFetchDone = useRef(false);

  const loading = templatesLoading;

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    if (categoryId && categories) {
      const selected = categories.find(c => c.id === categoryId);
      setSelectedCategory(selected);
    } else {
      setSelectedCategory(null);
    }
  }, [categoryId, categories]);

  useEffect(() => {
    // Wait for categories to load before fetching templates
    if (!categories || categories.length === 0) {
      return;
    }

    // For initial load with categoryId, wait for selectedCategory to be set
    if (!initialFetchDone.current && categoryId && !selectedCategory) {
      return;
    }

    const params = {};
    if (selectedCategory) {
      params.category_name = selectedCategory.name;
    }

    fetchTemplates(params);
    initialFetchDone.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categories, selectedCategory, searchQuery]);

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
  const templatesByCategory = categories && templates ? categories.reduce((acc, category) => {
    acc[category.id] = templates.filter(t => t.category_id === category.id);
    return acc;
  }, {}) : {};

  // Filter templates by search query
  const filteredTemplates = templates && searchQuery
    ? templates.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : (templates || []);

  if (selectedCategory) {
    // Focused category view - /library/categories/<uuid>/
    return (
      <MainLayout activeTab="library">
        <div className="h-full flex flex-col">
          {/* Header with breadcrumbs and search */}
          <div className="py-6 pb-12 flex items-center justify-between gap-4">
            <Breadcrumb className="mr-6">
              <BreadcrumbList className="text-2xl">
                <BreadcrumbItem>
                  <BreadcrumbLink onClick={() => navigate('/library/categories')} className="cursor-pointer">Library</BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage className="font-bold">{selectedCategory.name}</BreadcrumbPage>
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
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              null
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
                  <div className="text-center text-muted-foreground py-12">
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
        <div className="py-6 pb-12 flex justify-between items-center">
          <Breadcrumb className="mr-6">
            <BreadcrumbList className="text-2xl">
              <BreadcrumbItem>
                <BreadcrumbPage className="font-bold">Library</BreadcrumbPage>
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

        {/* Templates by category */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            null
          ) : (
            <div className="space-y-8">
              {categories && categories.map(category => {
                const categoryTemplates = searchQuery
                  ? filteredTemplates.filter(t => t.category_id === category.id)
                  : templatesByCategory[category.id] || [];

                if (categoryTemplates.length === 0) return null;

                return (
                  <div key={category.id}>
                    <h2
                      className="text-lg font-semibold mb-4 cursor-pointer hover:text-primary transition-colors"
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
                <div className="text-center text-muted-foreground py-12">
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
