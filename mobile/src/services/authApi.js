import { apiRequest } from './apiClient';
export const authApi = {
  signup: (name, mobile, email) => apiRequest('/accounts/signup/', { method: 'POST', data: { name, mobile, email }, auth: false }),
  sendOtp: (mobile) => apiRequest('/accounts/otp/send/', { method: 'POST', data: { mobile }, auth: false }),
  verifyOtp: (mobile, otp) => apiRequest('/accounts/otp/verify/', { method: 'POST', data: { mobile, otp }, auth: false }),
  profile: () => apiRequest('/accounts/profile/'),
};
