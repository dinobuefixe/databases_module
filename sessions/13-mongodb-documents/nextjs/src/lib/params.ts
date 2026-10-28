export function parseId(id: string): number | null {
  return /^\d+$/.test(id) ? Number(id) : null;
}
