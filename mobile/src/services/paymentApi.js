import { apiRequest } from './apiClient';
export const paymentApi = {
  createRazorpayOrder: (order_id) => apiRequest('/payments/razorpay/create/', { method: 'POST', data: { order_id } }),
  verifyRazorpay: (data) => apiRequest('/payments/razorpay/verify/', { method: 'POST', data }),
  confirmCod: (order_id) => apiRequest('/payments/cod/confirm/', { method: 'POST', data: { order_id } }),
};
// Razorpay UI integration is Phase 11; never handle gateway secret keys in the app.
