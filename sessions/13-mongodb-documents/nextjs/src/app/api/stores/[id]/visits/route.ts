import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { stores } from "@/lib/stores";

export const dynamic = "force-dynamic";

// POST /api/stores/{id}/visits: $inc creates the field on the first call, then adds 1 atomically.
export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid store id" }, { status: 400 });

  const doc = await stores().findOneAndUpdate(
    { _id: id },
    { $inc: { visits: 1 } },
    { returnDocument: "after", projection: { visits: 1 } },
  );
  if (!doc) return NextResponse.json({ error: "Store not found" }, { status: 404 });
  return NextResponse.json(doc);
}
