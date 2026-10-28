import "dotenv/config";

export const API = process.env.API_URL ?? "http://localhost:3000";

export async function call(method: string, path: string, body?: unknown) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return { status: res.status, body: await res.json() };
}

// Counts how many responses had each status code: { 200: 10, 409: 40 }.
export function byStatus(results: { status: number }[]) {
  const counts: Record<number, number> = {};
  for (const r of results) counts[r.status] = (counts[r.status] ?? 0) + 1;
  return counts;
}
