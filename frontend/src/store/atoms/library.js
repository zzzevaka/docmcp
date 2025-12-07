import { atom } from 'recoil';

export const categoriesState = atom({
  key: 'categoriesState',
  default: null,
});

export const templatesState = atom({
  key: 'templatesState',
  default: null,
});

export const templatesFiltersState = atom({
  key: 'templatesFiltersState',
  default: {},
});

export const categoriesLoadingState = atom({
  key: 'categoriesLoadingState',
  default: false,
});

export const templatesLoadingState = atom({
  key: 'templatesLoadingState',
  default: false,
});
