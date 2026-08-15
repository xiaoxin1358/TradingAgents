// Minimal fetch wrapper (docs 7: no axios).

export async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export function enc(s: string): string {
  return encodeURIComponent(s);
}
