import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// GET /api/rentals/latest: the 5 latest rentals with the rating and categories of the film,
// read from films with $lookup.
export async function GET() {
  const rows = await mongoDb()
    .collection("customers")
    .aggregate([
      { $unwind: "$recent_rentals" },
      { $sort: { "recent_rentals.rental_date": -1, "recent_rentals.rental_id": -1 } },
      { $limit: 5 },
      // After $limit, so only 5 documents look up their film, not every embedded rental.
      { $lookup: { from: "films", localField: "recent_rentals.film_id", foreignField: "_id", as: "film" } },
      { $unwind: "$film" },
      {
        $project: {
          _id: 0,
          customer: "$name",
          rental_date: "$recent_rentals.rental_date",
          title: "$film.title",
          rating: "$film.rating",
          categories: "$film.categories",
        },
      },
    ])
    .toArray();
  return NextResponse.json(rows);
}
