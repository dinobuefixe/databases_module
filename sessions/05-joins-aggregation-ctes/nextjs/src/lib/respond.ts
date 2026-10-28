import { NextResponse } from "next/server";
import type { Implementation } from "@/lib/questions";

// Shared handler: ?impl=orm (default) or ?impl=sql.
export async function answer(request: Request, question: Implementation) {
  const impl = new URL(request.url).searchParams.get("impl") ?? "orm";
  if (impl !== "orm" && impl !== "sql") {
    return NextResponse.json({ error: "impl must be orm or sql" }, { status: 400 });
  }
  const rows = (await question[impl]()) as unknown[];
  return NextResponse.json({ impl, count: rows.length, rows });
}
