import { config } from '../constants/config';
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '../utils/tokenStorage';

let refreshPromise = null;
function makeError(status, body) {
  const error = new Error(body?.detail || body?.message || `Request failed (${status})`);
  error.status = status;
  error.details = body;
  return error;
}
async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return { detail: text }; }
}
async function fetchJson(path, { method = 'GET', data, token, timeoutMs = config.requestTimeoutMs } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${config.apiBaseUrl}${path}`, {
      method, signal: controller.signal,
      headers: { Accept: 'application/json', ...(data === undefined ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    });
    const body = await parseBody(response);
    if (!response.ok) throw makeError(response.status, body);
    return body;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Request timed out. Check your connection.');
    throw error;
  } finally { clearTimeout(timer); }
}
async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refresh = await getRefreshToken();
      if (!refresh) throw new Error('Session expired. Please sign in again.');
      const tokens = await fetchJson('/accounts/token/refresh/', { method: 'POST', data: { refresh } });
      await saveTokens({ access: tokens.access, refresh: tokens.refresh || refresh });
      return tokens.access;
    })().finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}
export async function apiRequest(path, options = {}) {
  const { auth = true, ...requestOptions } = options;
  if (!auth) return fetchJson(path, requestOptions);
  const access = await getAccessToken();
  if (!access) throw new Error('Please sign in to continue.');
  try { return await fetchJson(path, { ...requestOptions, token: access }); }
  catch (error) {
    if (error.status !== 401) throw error;
    try {
      const nextToken = await refreshAccessToken();
      return await fetchJson(path, { ...requestOptions, token: nextToken });
    } catch (refreshError) {
      if (refreshError.status === 400 || refreshError.status === 401 || refreshError.message.startsWith('Session expired')) await clearTokens();
      throw refreshError;
    }
  }
}
