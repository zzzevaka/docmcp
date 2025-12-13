import { useRecoilState } from 'recoil';
import { useCallback } from 'react';
import axios from 'axios';
import {
  projectsState,
  projectsLoadingState,
  projectDetailState,
  documentsState,
  projectDetailLoadingState,
} from '../atoms/projects';

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

  const deleteProject = useCallback((projectId) => {
    setProjects((prevProjects) => {
      if (!prevProjects) return prevProjects;
      return prevProjects.filter((project) => project.id !== projectId);
    });
  }, [setProjects]);

  const updateProject = useCallback((projectId, updatedFields) => {
    setProjects((prevProjects) => {
      if (!prevProjects) return prevProjects;
      return prevProjects.map((project) =>
        project.id === projectId ? { ...project, ...updatedFields } : project
      );
    });
  }, [setProjects]);

  return { projects, loading, fetchProjects, refreshProjects, deleteProject, updateProject };
};

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

  const updateDocument = useCallback((documentId, updatedFields) => {
    setDocuments((prevDocuments) => {
      if (!prevDocuments) return prevDocuments;
      return prevDocuments.map((doc) =>
        doc.id === documentId ? { ...doc, ...updatedFields } : doc
      );
    });
  }, [setDocuments]);

  const deleteDocument = useCallback((documentId) => {
    setDocuments((prevDocuments) => {
      if (!prevDocuments) return prevDocuments;
      return prevDocuments.filter((doc) => doc.id !== documentId);
    });
  }, [setDocuments]);

  const fetchDocumentContent = useCallback(async (documentId) => {
    try {
      const response = await axios.get(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
        { withCredentials: true }
      );
      const documentWithContent = response.data;

      // Update the document in state with content
      updateDocument(documentId, { content: documentWithContent.content });

      return documentWithContent.content;
    } catch (error) {
      console.error('Failed to fetch document content:', error);
      throw error;
    }
  }, [projectId, updateDocument]);

  return { project, documents, loading, fetchProjectData, refreshProjectData, updateDocument, deleteDocument, fetchDocumentContent };
};
