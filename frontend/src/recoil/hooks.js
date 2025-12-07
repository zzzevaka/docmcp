import { useRecoilState, useSetRecoilState, useRecoilValue } from 'recoil';
import { useCallback } from 'react';
import axios from 'axios';
import {
  teamsState,
  projectsState,
  pendingInvitationsState,
  categoriesState,
  templatesState,
  projectDetailState,
  documentsState,
  teamsLoadingState,
  projectsLoadingState,
  invitationsLoadingState,
  categoriesLoadingState,
  templatesLoadingState,
  projectDetailLoadingState,
} from './atoms';

// Teams hooks
export const useTeams = () => {
  const [teams, setTeams] = useRecoilState(teamsState);
  const [loading, setLoading] = useRecoilState(teamsLoadingState);

  const fetchTeams = useCallback(async (force = false) => {
    // Skip if already loaded and not forcing refresh
    if (teams !== null && !force) return;

    try {
      setLoading(true);
      const response = await axios.get('/api/v1/teams/', { withCredentials: true });
      setTeams(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      setTeams([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [teams, setTeams, setLoading]);

  const refreshTeams = useCallback(() => {
    return fetchTeams(true);
  }, [fetchTeams]);

  return { teams, loading, fetchTeams, refreshTeams };
};

// Projects hooks
export const useProjects = () => {
  const [projects, setProjects] = useRecoilState(projectsState);
  const [loading, setLoading] = useRecoilState(projectsLoadingState);

  const fetchProjects = useCallback(async (force = false) => {
    if (projects !== null && !force) return;

    try {
      setLoading(true);
      const response = await axios.get('/api/v1/projects/', { withCredentials: true });
      setProjects(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      setProjects([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [projects, setProjects, setLoading]);

  const refreshProjects = useCallback(() => {
    return fetchProjects(true);
  }, [fetchProjects]);

  return { projects, loading, fetchProjects, refreshProjects };
};

// Pending Invitations hooks
export const usePendingInvitations = () => {
  const [invitations, setInvitations] = useRecoilState(pendingInvitationsState);
  const [loading, setLoading] = useRecoilState(invitationsLoadingState);

  const fetchInvitations = useCallback(async (force = false) => {
    if (invitations !== null && !force) return;

    try {
      setLoading(true);
      const response = await axios.get('/api/v1/invitations/me', { withCredentials: true });
      setInvitations(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch invitations:', error);
      setInvitations([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [invitations, setInvitations, setLoading]);

  const refreshInvitations = useCallback(() => {
    return fetchInvitations(true);
  }, [fetchInvitations]);

  return { invitations, loading, fetchInvitations, refreshInvitations };
};

// Categories hooks
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

// Templates hooks
export const useTemplates = () => {
  const [templates, setTemplates] = useRecoilState(templatesState);
  const [loading, setLoading] = useRecoilState(templatesLoadingState);

  const fetchTemplates = useCallback(async (filters = {}, force = false) => {
    // For templates, we always refetch because filters can change
    // But we skip if templates exist and no filters and not forcing
    if (templates !== null && Object.keys(filters).length === 0 && !force) return;

    try {
      setLoading(true);
      const response = await axios.get('/api/v1/library/templates/', {
        params: filters,
        withCredentials: true,
      });
      setTemplates(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      setTemplates([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [templates, setTemplates, setLoading]);

  const refreshTemplates = useCallback((filters = {}) => {
    return fetchTemplates(filters, true);
  }, [fetchTemplates]);

  return { templates, loading, fetchTemplates, refreshTemplates };
};

// Project Detail hooks
export const useProjectDetail = (projectId) => {
  const [project, setProject] = useRecoilState(projectDetailState(projectId));
  const [documents, setDocuments] = useRecoilState(documentsState(projectId));
  const [loading, setLoading] = useRecoilState(projectDetailLoadingState(projectId));

  const fetchProjectData = useCallback(async (force = false) => {
    if (project !== null && documents !== null && !force) return;

    try {
      setLoading(true);
      const [projectRes, docsRes] = await Promise.all([
        axios.get(`/api/v1/projects/${projectId}`, { withCredentials: true }),
        axios.get(`/api/v1/projects/${projectId}/documents/`, { withCredentials: true }),
      ]);
      setProject(projectRes.data);
      setDocuments(docsRes.data);
      return { project: projectRes.data, documents: docsRes.data };
    } catch (error) {
      console.error('Failed to fetch project data:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [projectId, project, documents, setProject, setDocuments, setLoading]);

  const refreshProjectData = useCallback(() => {
    return fetchProjectData(true);
  }, [fetchProjectData]);

  return { project, documents, loading, fetchProjectData, refreshProjectData };
};
