import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// GET /api/films/by-rating: films per rating with the average rental rate.
export async function GET() {
  const rows = await mongoDb()
    .collection("films")
    .aggregate([
      { $group: { _id: "$rating", films: { $sum: 1 }, avg_rate: { $avg: "$rental_rate" } } },
      { $sort: { films: -1 } },
    ])
    .toArray();
  return NextResponse.json(rows);
}
