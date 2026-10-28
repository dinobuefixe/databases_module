import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/counts: rows in the tables that simulate-disaster damages.
// Call it before the disaster, after it, and after the restore.
export async function GET() {
  const [filmActor, filmCategory, payment, march] = await Promise.all([
    prisma.film_actor.count(),
    prisma.film_category.count(),
    prisma.payment.count(),
    prisma.payment.count({
      where: { payment_date: { gte: new Date("2022-03-01T00:00:00Z"), lt: new Date("2022-05-01T00:00:00Z") } },
    }),
  ]);
  return NextResponse.json({
    film_actor: filmActor,
    film_category: filmCategory,
    payment,
    payment_march_april_2022: march,
  });
}
