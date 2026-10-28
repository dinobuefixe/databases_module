import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// POST /api/actors {"first_name": "ADA", "last_name": "LOVELACE"}
// prisma.actor.create runs INSERT ... RETURNING, so the generated actor_id and
// last_update come back without a second query.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (typeof body?.first_name !== "string" || typeof body?.last_name !== "string") {
    return NextResponse.json({ error: "expected first_name and last_name" }, { status: 400 });
  }
  const actor = await prisma.actor.create({
    data: { first_name: body.first_name, last_name: body.last_name },
    select: { actor_id: true, first_name: true, last_name: true, last_update: true },
  });
  return NextResponse.json(actor, { status: 201 });
}
