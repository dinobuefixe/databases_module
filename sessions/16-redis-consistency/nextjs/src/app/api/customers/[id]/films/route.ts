import { NextResponse } from "next/server";
import { filmsKey } from "@/lib/films-sets";
import { parseId } from "@/lib/params";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/customers/{id}/films: the derived set as Redis holds it.
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const films = (await (await getRedis()).sMembers(filmsKey(id))).map(Number).sort((a, b) => a - b);
  return NextResponse.json({ key: filmsKey(id), count: films.length, films });
}
