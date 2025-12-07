import { atom } from 'recoil';

export const pendingInvitationsState = atom({
  key: 'pendingInvitationsState',
  default: null,
});

export const invitationsLoadingState = atom({
  key: 'invitationsLoadingState',
  default: false,
});
