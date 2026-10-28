import { NextResponse } from "next/server";
import { MongoServerError } from "mongodb";
import { stores, type StoreDoc } from "@/lib/stores";

export const dynamic = "force-dynamic";

// GET /api/stores?country=Canada: dot notation in the filter, a projection to return two fields.
export async function GET(request: Request) {
  const country = new URL(request.url).searchParams.get("country") ?? "Canada";
  const docs = await stores()
    .find({ "address.country": country }, { projection: { _id: 1, "address.city": 1 } })
    .sort({ _id: 1 })
    .toArray();
  return NextResponse.json(docs);
}

// POST /api/stores: inserts the body as it is, so the $jsonSchema validator decides.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (typeof body !== "object" || body === null || Array.isArray(body)) {
    return NextResponse.json({ error: "Body must be a JSON object" }, { status: 400 });
  }
  try {
    const result = await stores().insertOne(body as StoreDoc);
    return NextResponse.json({ _id: result.insertedId }, { status: 201 });
  } catch (err) {
    if (err instanceof MongoServerError && err.code === 121) {
      // Document failed validation: errInfo says which rule failed.
      return NextResponse.json({ error: err.message, details: err.errInfo?.details }, { status: 422 });
    }
    if (err instanceof MongoServerError && err.code === 11000) {
      return NextResponse.json({ error: "A store with this _id already exists" }, { status: 409 });
    }
    throw err;
  }
}
