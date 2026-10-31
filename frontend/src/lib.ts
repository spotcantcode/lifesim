export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = payload.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((item: { msg: string; loc: string[] }) => `${item.loc.slice(1).join('.')}: ${item.msg}`).join('; ') : 'Unable to complete this action. Check the local server.');
  }
  return response.json();
}
export const money = (value: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
export const compactMoney = (value: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 }).format(value);
export function dateLabel(start: string, month: number) {
  const [year, initialMonth] = start.split('-').map(Number);
  return new Date(Date.UTC(year, initialMonth - 1 + month, 1)).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });
}
export function download(name: string, content: string, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function interpretDecision(text: string): string | null {
  const normalized = text.toLowerCase();
  if (/sell|disease|divorce|marry/.test(normalized)) return null;
  if (/hire|operator|manager|delegat/.test(normalized)) return 'hire_manager';
  if (/expand|aggressive|growth|grow/.test(normalized)) return 'expand_owner';
  if (/expense|spend less|frugal|simplify/.test(normalized)) return 'reduce_expenses';
  if (/abroad|international|travel|portugal/.test(normalized)) return 'abroad';
  if (/invest/.test(normalized)) return 'invest_cash';
  if (/hours|schedule|less work/.test(normalized)) return 'reduce_hours';
  if (/maintain|steady|current|nothing/.test(normalized)) return 'maintain';
  return null;
}
