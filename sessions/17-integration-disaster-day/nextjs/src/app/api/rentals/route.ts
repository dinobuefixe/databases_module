import { NextResponse } from "next/server";
import { Prisma } from "@/generated/prisma/client";
import { filmsKey } from "@/lib/films-sets";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// POST /api/rentals {"customer_id": 1, "inventory_id": 10, "staff_id": 1}
// Records a rental and keeps customer:{id}:films up to date. Availability is not checked here.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const { customer_id, inventory_id, staff_id = 1 } = body ?? {};
  if (![customer_id, inventory_id, staff_id].every(Number.isInteger)) {
    return NextResponse.json({ error: "customer_id, inventory_id and staff_id must be integers" }, { status: 422 });
  }

  // 1. The source of truth first.
  let rental;
  try {
    rental = await prisma.rental.create({
      data: { rental_date: new Date(), customer_id, inventory_id, staff_id },
      include: { inventory: { select: { film_id: true } } },
    });
  } catch (err) {
    if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2003") {
      return NextResponse.json({ error: "Unknown customer, inventory item or staff member" }, { status: 422 });
    }
    throw err;
  }

  // 2. Then the derived data. If this fails, PostgreSQL already has the rental and the two
  // engines disagree until the rebuild (npm run redis:rebuild) runs. Never write Redis first.
  await (await getRedis()).sAdd(filmsKey(customer_id), String(rental.inventory.film_id));

  return NextResponse.json(
    { rental_id: rental.rental_id, customer_id, film_id: rental.inventory.film_id },
    { status: 201 },
  );
}
