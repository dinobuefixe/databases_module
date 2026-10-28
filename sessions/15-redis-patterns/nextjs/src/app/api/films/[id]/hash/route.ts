import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// PUT /api/films/{id}/hash: HSET film:{id} title ... rate ... with the values from PostgreSQL.
export async function PUT(_request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid film id" }, { status: 400 });
  const film = await prisma.film.findUnique({ where: { film_id: id } });
  if (!film) return NextResponse.json({ error: "Film not found" }, { status: 404 });

  const redis = await getRedis();
  await redis.hSet(`film:${id}`, { title: film.title, rate: film.rental_rate.toString() });
  return NextResponse.json({ key: `film:${id}`, fields: await redis.hGetAll(`film:${id}`) });
}

// GET /api/films/{id}/hash: HGETALL. Every value comes back as a string.
export async function GET(_request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid film id" }, { status: 400 });
  const fields = await (await getRedis()).hGetAll(`film:${id}`);
  return NextResponse.json({ key: `film:${id}`, fields });
}
