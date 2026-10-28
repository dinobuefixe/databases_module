import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { getProfile } from "@/lib/profile";

export const dynamic = "force-dynamic";

// GET /api/customers/{id}/profile
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const profile = await getProfile(id);
  if (!profile) return NextResponse.json({ error: "Customer not found" }, { status: 404 });
  return NextResponse.json(profile);
}
