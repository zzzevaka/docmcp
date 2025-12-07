import { atom, atomFamily } from 'recoil';

export const projectsState = atom({
  key: 'projectsState',
  default: null,
});

export const projectsLoadingState = atom({
  key: 'projectsLoadingState',
  default: false,
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

export const projectDetailLoadingState = atomFamily({
  key: 'projectDetailLoadingState',
  default: false,
});
