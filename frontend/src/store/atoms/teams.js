import { atom } from 'recoil';

export const teamsState = atom({
  key: 'teamsState',
  default: null,
});

export const teamsLoadingState = atom({
  key: 'teamsLoadingState',
  default: false,
});
