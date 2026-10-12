import * as SecureStore from 'expo-secure-store';
const ACCESS_KEY = 'studentstore_access';
const REFRESH_KEY = 'studentstore_refresh';
export async function getAccessToken() { return SecureStore.getItemAsync(ACCESS_KEY); }
export async function getRefreshToken() { return SecureStore.getItemAsync(REFRESH_KEY); }
export async function saveTokens({ access, refresh }) {
  if (!access || !refresh) throw new Error('Both JWT tokens are required');
  await SecureStore.setItemAsync(ACCESS_KEY, access);
  await SecureStore.setItemAsync(REFRESH_KEY, refresh);
}
export async function clearTokens() {
  await Promise.all([SecureStore.deleteItemAsync(ACCESS_KEY), SecureStore.deleteItemAsync(REFRESH_KEY)]);
}
