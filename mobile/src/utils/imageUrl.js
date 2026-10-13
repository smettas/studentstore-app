import { config } from '../constants/config';
const server = config.apiBaseUrl.replace(/\/api\/?$/, '');
export function resolveImageUrl(value) {
  if (!value || typeof value !== 'string') return null;
  const url = value.trim();
  if (url.startsWith('/')) return `${server}${url}`;
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//i.test(url)) {
    return url.replace(/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i, server);
  }
  return /^https?:\/\//i.test(url) ? url : `${server}/${url.replace(/^\/+/, '')}`;
}
