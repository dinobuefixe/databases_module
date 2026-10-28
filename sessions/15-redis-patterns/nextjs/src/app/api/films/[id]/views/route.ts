import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// POST /api/films/{id}/views: INCR is atomic, so concurrent calls never lose a view.
export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid film id" }, { status: 400 });
  const views = await (await getRedis()).incr(`film:${id}:views`);
  return NextResponse.json({ key: `film:${id}:views`, views });
}

// GET /api/films/{id}/views: the current count, 0 if the key does not exist yet.
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid film id" }, { status: 400 });
  const views = Number((await (await getRedis()).get(`film:${id}:views`)) ?? 0);
  return NextResponse.json({ key: `film:${id}:views`, views });
}
