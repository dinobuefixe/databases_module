import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { stores } from "@/lib/stores";

export const dynamic = "force-dynamic";

// POST /api/stores/{id}/staff {"staff_id": 3, "name": "New Hire"}: $push adds to the embedded array.
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid store id" }, { status: 400 });
  const body = await request.json().catch(() => null);
  if (!Number.isInteger(body?.staff_id) || typeof body?.name !== "string" || !body.name.trim()) {
    return NextResponse.json({ error: "staff_id (integer) and name (string) are required" }, { status: 400 });
  }

  const doc = await stores().findOneAndUpdate(
    { _id: id },
    { $push: { staff: { staff_id: body.staff_id, name: body.name.trim() } } },
    { returnDocument: "after", projection: { staff: 1 } },
  );
  if (!doc) return NextResponse.json({ error: "Store not found" }, { status: 404 });
  return NextResponse.json(doc);
}
