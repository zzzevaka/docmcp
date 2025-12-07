import { atom, atomFamily } from 'recoil';

// Teams
export const teamsState = atom({
  key: 'teamsState',
  default: null, // null means not loaded yet, [] means empty
});

// Projects
export const projectsState = atom({
  key: 'projectsState',
  default: null,
});

// Pending Invitations
export const pendingInvitationsState = atom({
  key: 'pendingInvitationsState',
  default: null,
});

// Library Categories
export const categoriesState = atom({
  key: 'categoriesState',
  default: null,
});

// Library Templates
export const templatesState = atom({
  key: 'templatesState',
  default: null,
});

// Project Detail - using atomFamily to cache data per projectId
export const projectDetailState = atomFamily({
  key: 'projectDetailState',
  default: null,
});

// Documents per project - using atomFamily to cache data per projectId
export const documentsState = atomFamily({
  key: 'documentsState',
  default: null,
});

// Loading states
export const teamsLoadingState = atom({
  key: 'teamsLoadingState',
  default: false,
});

export const projectsLoadingState = atom({
  key: 'projectsLoadingState',
  default: false,
});

export const invitationsLoadingState = atom({
  key: 'invitationsLoadingState',
  default: false,
});

export const categoriesLoadingState = atom({
  key: 'categoriesLoadingState',
  default: false,
});

export const templatesLoadingState = atom({
  key: 'templatesLoadingState',
  default: false,
});

export const projectDetailLoadingState = atomFamily({
  key: 'projectDetailLoadingState',
  default: false,
});
