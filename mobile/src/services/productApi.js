import { apiRequest } from './apiClient';
const queryString = (params = {}) => {
  const parts = Object.entries(params).filter(([, value]) => value !== '' && value !== null && value !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  return parts.length ? `?${parts.join('&')}` : '';
};
export const productApi = {
  list: (filters) => apiRequest(`/catalog/products/${queryString(filters)}`, { auth: false }),
  detail: (slug) => apiRequest(`/catalog/products/${encodeURIComponent(slug)}/`, { auth: false }),
  categories: () => apiRequest('/catalog/categories/', { auth: false }),
  brands: () => apiRequest('/catalog/brands/', { auth: false }),
  studyLevels: () => apiRequest('/catalog/study-levels/', { auth: false }),
};
