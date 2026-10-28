import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { mongoDb } from "@/lib/mongo";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// POST /api/hello {"msg": "..."}: write the same message to each engine.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const msg = typeof body?.msg === "string" ? body.msg.trim() : "";
  if (!msg) {
    return NextResponse.json({ error: "msg must be a non-empty string" }, { status: 400 });
  }

  // PostgreSQL: a row in a table with a fixed structure.
  const row = await prisma.hello.create({ data: { msg } });

  // MongoDB: a document; the tags array needs no extra table.
  const doc = await mongoDb().collection("hello").insertOne({ msg, tags: ["a", "b"], createdAt: new Date() });

  // Redis: a key holding the last message and a counter.
  const redis = await getRedis();
  await redis.set("hello:last", msg);
  const count = await redis.incr("hello:count");

  return NextResponse.json(
    { postgres: row, mongo: { _id: doc.insertedId }, redis: { last: msg, count } },
    { status: 201 },
  );
}

// GET /api/hello: read back what each engine holds.
export async function GET() {
  const redis = await getRedis();
  const [rows, docs, last, count] = await Promise.all([
    prisma.hello.findMany({ orderBy: { id: "desc" }, take: 5 }),
    mongoDb().collection("hello").find().sort({ _id: -1 }).limit(5).toArray(),
    redis.get("hello:last"),
    redis.get("hello:count"),
  ]);
  return NextResponse.json({ postgres: rows, mongo: docs, redis: { last, count: Number(count ?? 0) } });
}
