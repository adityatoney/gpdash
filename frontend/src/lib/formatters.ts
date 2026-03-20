export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '--';
  return value.toLocaleString();
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null) return '--';
  return `${value.toFixed(1)}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '--';
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
