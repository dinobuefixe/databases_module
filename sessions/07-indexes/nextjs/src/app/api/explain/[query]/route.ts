import { NextResponse } from "next/server";
import { explain, queries, type QueryName } from "@/lib/explain";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ query: string }> };

// GET /api/explain/customer-latest?customer=42
// GET /api/explain/open-rentals
// GET /api/explain/customer-email?email=MARY.SMITH@sakilacustomer.org
// GET /api/explain/recent-rentals?days=730&force_index=1
export async function GET(request: Request, { params }: Params) {
  const name = (await params).query;
  if (!(name in queries)) {
    return NextResponse.json({ error: `query must be one of ${Object.keys(queries).join(", ")}` }, { status: 404 });
  }
  return NextResponse.json(await explain(name as QueryName, new URL(request.url).searchParams));
}
