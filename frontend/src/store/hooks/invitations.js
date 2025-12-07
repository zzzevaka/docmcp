import { useRecoilState } from 'recoil';
import { useCallback } from 'react';
import axios from 'axios';
import { pendingInvitationsState, invitationsLoadingState } from '../atoms/invitations';

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
