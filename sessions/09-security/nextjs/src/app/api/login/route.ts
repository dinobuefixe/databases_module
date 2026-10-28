import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// POST /api/login {"username": "...", "password": "..."}
// Safe: check the types first, so an object like {"$ne": null} never reaches
// the filter; look the user up by username only; compare the password with
// the stored bcrypt hash in the application.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (typeof body?.username !== "string" || typeof body?.password !== "string") {
    return NextResponse.json({ error: "username and password must be strings" }, { status: 400 });
  }
  const user = await mongoDb().collection("users").findOne({ username: body.username });
  // Same answer for "no such user" and "wrong password": do not tell an
  // attacker which usernames exist.
  if (!user || !(await bcrypt.compare(body.password, user.passwordHash))) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  return NextResponse.json({ ok: true, username: user.username, role: user.role });
}
