export const rows = value => Array.isArray(value) ? value : (value?.results || value?.items || []);
export const money = value => `₹${Number(value || 0).toLocaleString('en-IN', {maximumFractionDigits: 2})}`;
export const errorText = error => {
  const details = error?.details;
  if (details && typeof details === 'object') {
    const first = Object.values(details)[0];
    if (Array.isArray(first)) return String(first[0]);
    if (typeof first === 'string') return first;
  }
  return error?.message || 'Something went wrong. Please try again.';
};
export const priceOf = product => product?.effective_price ?? product?.discount_price ?? product?.price ?? 0;
