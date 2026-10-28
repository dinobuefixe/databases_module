import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { violationResponse } from "@/lib/db-errors";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// DELETE /api/authors/:id. ON DELETE RESTRICT refuses it while the author has
// recipes: 409 naming recipe_author_id_fkey.
export async function DELETE(_request: Request, { params }: Params) {
  const id = Number((await params).id);
  try {
    const { count } = await prisma.author.deleteMany({ where: { id } });
    if (count === 0) return NextResponse.json({ error: "author not found" }, { status: 404 });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    return violationResponse(err);
  }
}
