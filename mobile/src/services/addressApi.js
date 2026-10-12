import { apiRequest } from './apiClient';
export const addressApi = {
  list: () => apiRequest('/addresses/'),
  create: (data) => apiRequest('/addresses/', { method: 'POST', data }),
  update: (id, data) => apiRequest(`/addresses/${id}/`, { method: 'PATCH', data }),
  remove: (id) => apiRequest(`/addresses/${id}/`, { method: 'DELETE' }),
  setDefault: (id) => apiRequest(`/addresses/${id}/default/`, { method: 'POST' }),
};
