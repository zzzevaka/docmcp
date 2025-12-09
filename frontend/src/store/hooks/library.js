import { useRecoilState } from 'recoil';
import { useCallback } from 'react';
import axios from 'axios';
import {
  categoriesState,
  templatesState,
  templatesFiltersState,
  categoriesLoadingState,
  templatesLoadingState,
} from '../atoms/library';

export const useCategories = () => {
  const [categories, setCategories] = useRecoilState(categoriesState);
  const [loading, setLoading] = useRecoilState(categoriesLoadingState);

  const fetchCategories = useCallback(async (force = false) => {
    if (categories !== null && !force) return;

    try {
      setLoading(true);
      const response = await axios.get('/api/v1/library/categories/', { withCredentials: true });
      setCategories(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      setCategories([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [categories, setCategories, setLoading]);

  const refreshCategories = useCallback(() => {
    return fetchCategories(true);
  }, [fetchCategories]);

  return { categories, loading, fetchCategories, refreshCategories };
};

export const useTemplates = () => {
  const [templates, setTemplates] = useRecoilState(templatesState);
  const [currentFilters, setCurrentFilters] = useRecoilState(templatesFiltersState);
  const [loading, setLoading] = useRecoilState(templatesLoadingState);

  const fetchTemplates = useCallback(async (filters = {}, force = false) => {
    // Check if filters have changed
    const filtersChanged = JSON.stringify(filters) !== JSON.stringify(currentFilters);

    // Skip if templates exist, filters haven't changed, and not forcing
    if (templates !== null && !filtersChanged && !force) return;

    try {
      setLoading(true);
      const response = await axios.get('/api/v1/library/templates/', {
        params: filters,
        withCredentials: true,
      });
      setTemplates(response.data);
      setCurrentFilters(filters);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      setTemplates([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [templates, currentFilters, setTemplates, setCurrentFilters, setLoading]);

  const refreshTemplates = useCallback((filters = {}) => {
    return fetchTemplates(filters, true);
  }, [fetchTemplates]);

  const deleteTemplate = useCallback((templateId) => {
    setTemplates((prevTemplates) => {
      if (!prevTemplates) return prevTemplates;
      return prevTemplates.filter((template) => template.id !== templateId);
    });
  }, [setTemplates]);

  const updateTemplate = useCallback((templateId, updatedFields) => {
    setTemplates((prevTemplates) => {
      if (!prevTemplates) return prevTemplates;
      return prevTemplates.map((template) =>
        template.id === templateId ? { ...template, ...updatedFields } : template
      );
    });
  }, [setTemplates]);

  const addTemplate = useCallback((newTemplate) => {
    // Instead of adding to existing templates, reset to null to force reload on next visit
    // This ensures we get the full list from the server with correct filtering
    setTemplates(null);
    setCurrentFilters({});
  }, [setTemplates, setCurrentFilters]);

  return { templates, loading, fetchTemplates, refreshTemplates, deleteTemplate, updateTemplate, addTemplate };
};
