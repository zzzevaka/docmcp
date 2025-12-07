import { useRecoilState } from 'recoil';
import { useCallback } from 'react';
import axios from 'axios';
import { teamsState, teamsLoadingState } from '../atoms/teams';

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
