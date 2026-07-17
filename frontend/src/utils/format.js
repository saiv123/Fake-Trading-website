// Shared formatters. API money fields are Decimal-as-string (e.g. "1234.50") — always parseFloat
// before formatting, never do string math on them.

export function formatMoney(value) {
  const n = parseFloat(value);
  if (Number.isNaN(n)) return '—';
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

export function formatPercent(value) {
  const n = parseFloat(value);
  if (Number.isNaN(n)) return '—';
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
}

export function formatDateTime(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function formatDate(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString('en-US', { dateStyle: 'medium' });
}
