import { NextResponse } from "next/server";
import { explainByCountry, stores } from "@/lib/stores";

export const dynamic = "force-dynamic";

// GET /api/stores/explain?country=Canada: the current plan. `npm run explain` shows before and after.
export async function GET(request: Request) {
  const country = new URL(request.url).searchParams.get("country") ?? "Canada";
  const indexes = (await stores().indexes()).map((i) => i.name);
  return NextResponse.json({ country, indexes, ...(await explainByCountry(country)) });
}
