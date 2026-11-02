import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { getRedis } from "@/lib/redis";
import { changeWithLua, changeWithWatch } from "@/lib/usernames";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// PUT /api/customers/{id}/username {"username": "ana", "method": "watch" | "lua"}
export async function PUT(request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const body = await request.json().catch(() => null);
  const username = typeof body?.username === "string" ? body.username.trim().toLowerCase() : "";
  const method = body?.method ?? "watch";
  if (!/^[a-z0-9_]{3,30}$/.test(username)) {
    return NextResponse.json({ error: "username must be 3-30 letters, digits or _" }, { status: 422 });
  }
  if (method !== "watch" && method !== "lua") {
    return NextResponse.json({ error: "method must be watch or lua" }, { status: 400 });
  }

  const redis = await getRedis();
  const result = method === "watch" ? await changeWithWatch(redis, id, username) : await changeWithLua(redis, id, username);
  if (!result.changed) return NextResponse.json({ error: `${username} is taken`, method }, { status: 409 });
  return NextResponse.json({ customer_id: id, username, method, attempts: result.attempts });
}

// GET /api/customers/{id}/username
export async function GET(_request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const username = await (await getRedis()).hGet(`customer:${id}`, "username");
  return NextResponse.json({ customer_id: id, username });
}
