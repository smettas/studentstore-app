import { apiRequest } from './apiClient';
export const orderApi = {
  list: () => apiRequest('/orders/'),
  detail: (id) => apiRequest(`/orders/${id}/`),
  create: (data) => apiRequest('/orders/', { method: 'POST', data }),
  cancel: (id) => apiRequest(`/orders/${id}/cancel/`, { method: 'POST' }),
};
