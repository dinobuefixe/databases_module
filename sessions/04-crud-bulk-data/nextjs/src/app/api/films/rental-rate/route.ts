import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { mpaa_rating } from "@/generated/prisma/client";

export const dynamic = "force-dynamic";

class CountMismatch extends Error {
  constructor(public matched: number) {
    super("row count mismatch");
  }
}

// POST /api/films/rental-rate
// {"rating": "NC-17", "below": 1, "newRate": 1.99, "expectedCount": 70}
// The safe UPDATE from the tutorial: change the rows inside a transaction,
// compare the number of rows with what the caller expected, and roll back if
// it differs.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const rating = typeof body?.rating === "string" ? body.rating.replace("-", "_") : "";
  if (
    !(rating in mpaa_rating) ||
    typeof body?.below !== "number" ||
    typeof body?.newRate !== "number" ||
    !Number.isInteger(body?.expectedCount)
  ) {
    return NextResponse.json({ error: "expected rating, below, newRate and expectedCount" }, { status: 400 });
  }

  try {
    const updated = await prisma.$transaction(async (tx) => {
      // UPDATE film SET rental_rate = ... WHERE rating = ... AND rental_rate < ... RETURNING ...
      const rows = await tx.film.updateManyAndReturn({
        where: { rating: rating as mpaa_rating, rental_rate: { lt: body.below } },
        data: { rental_rate: body.newRate },
        select: { film_id: true, title: true, rental_rate: true },
      });
      // Throwing inside the callback makes Prisma send ROLLBACK.
      if (rows.length !== body.expectedCount) throw new CountMismatch(rows.length);
      return rows;
    });
    return NextResponse.json({ committed: true, count: updated.length, films: updated });
  } catch (err) {
    if (err instanceof CountMismatch) {
      return NextResponse.json(
        { committed: false, error: "rolled back", expectedCount: body.expectedCount, matched: err.matched },
        { status: 409 },
      );
    }
    throw err;
  }
}
