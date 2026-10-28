import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// UNSAFE, for a local demonstration only. Two mistakes at once:
// the passwords in legacy_users are stored in plain text, and the filter is
// built straight from the request body. A body of
//   {"username": "admin", "password": {"$ne": null}}
// becomes the filter "password is not null", which matches any password.
export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const user = await mongoDb()
    .collection("legacy_users")
    .findOne({ username: body.username, password: body.password });
  if (!user) return NextResponse.json({ ok: false }, { status: 401 });
  return NextResponse.json({ ok: true, username: user.username, role: user.role });
}
