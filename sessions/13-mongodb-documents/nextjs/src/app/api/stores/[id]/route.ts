import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { stores } from "@/lib/stores";

export const dynamic = "force-dynamic";

// GET /api/stores/{id}: the whole document, with everything embedded.
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid store id" }, { status: 400 });
  const doc = await stores().findOne({ _id: id });
  if (!doc) return NextResponse.json({ error: "Store not found" }, { status: 404 });
  return NextResponse.json(doc);
}
