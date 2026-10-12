// Android emulator: 10.0.2.2; physical phone: your PC's LAN IP.
// Never put secrets in EXPO_PUBLIC_* variables: they are embedded in the app.
export const config = {
  appName: 'StudentStore',
  apiBaseUrl: (process.env.EXPO_PUBLIC_API_BASE_URL || 'http://10.0.2.2:8000/api').replace(/\/$/, ''),
  requestTimeoutMs: 15000,
};
