import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { violationResponse } from "@/lib/db-errors";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(await prisma.author.findMany({ orderBy: { id: "asc" } }));
}

// POST /api/authors {"name", "email"}. A repeated email reaches the database
// and comes back as 409 naming author_email_key.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (typeof body?.name !== "string" || typeof body?.email !== "string") {
    return NextResponse.json({ error: "expected name and email" }, { status: 400 });
  }
  try {
    const author = await prisma.author.create({ data: { name: body.name, email: body.email } });
    return NextResponse.json(author, { status: 201 });
  } catch (err) {
    return violationResponse(err);
  }
}
