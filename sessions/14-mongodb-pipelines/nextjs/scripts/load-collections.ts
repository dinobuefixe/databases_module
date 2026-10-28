// Builds the two collections the pipelines read:
//   films:     one document per film, categories and actors embedded
//   customers: one document per customer with its store and total rentals, the last 10 rentals embedded
import "dotenv/config";
import { mongo, mongoDb } from "@/lib/mongo";
import { prisma } from "@/lib/prisma";

async function loadFilms() {
  const films = await prisma.film.findMany({
    include: {
      film_actor: { include: { actor: true }, orderBy: { actor_id: "asc" } },
      film_category: { include: { category: true }, orderBy: { category: { name: "asc" } } },
    },
    orderBy: { film_id: "asc" },
  });
  const docs = films.map((f) => ({
    _id: f.film_id,
    title: f.title,
    rating: f.rating?.replace("_", "-") ?? null, // Prisma names the enum value PG_13; the database stores PG-13
    rental_rate: f.rental_rate.toNumber(), // a display price here; money that is summed goes in as a string (see the report)
    length: f.length,
    // Embedded: 1 to 3 names, read with the film.
    categories: f.film_category.map((fc) => fc.category.name),
    actors: f.film_actor.map((fa) => ({ actor_id: fa.actor_id, name: `${fa.actor.first_name} ${fa.actor.last_name}` })),
  }));
  // Numeric _id (the PostgreSQL key) instead of a generated ObjectId.
  const collection = mongoDb().collection<(typeof docs)[number]>("films");
  await collection.deleteMany({});
  await collection.insertMany(docs);
  return docs.length;
}

async function loadCustomers() {
  const customers = await prisma.customer.findMany({
    include: {
      // take inside include: the latest 10 per customer, not 10 in total.
      rental: {
        orderBy: { rental_date: "desc" },
        take: 10,
        include: { inventory: { select: { film_id: true, film: { select: { title: true } } } } },
      },
      _count: { select: { rental: true } }, // every rental, not only the 10 embedded
    },
    orderBy: { customer_id: "asc" },
  });
  const docs = customers.map((c) => ({
    _id: c.customer_id,
    name: `${c.first_name} ${c.last_name}`,
    store_id: c.store_id,
    rentals_total: c._count.rental,
    recent_rentals: c.rental.map((r) => ({
      rental_id: r.rental_id,
      rental_date: r.rental_date, // a JavaScript Date becomes a BSON date, which $dateTrunc needs
      film_id: r.inventory.film_id,
      title: r.inventory.film.title,
    })),
  }));
  // Numeric _id (the PostgreSQL key) instead of a generated ObjectId.
  const collection = mongoDb().collection<(typeof docs)[number]>("customers");
  await collection.deleteMany({});
  await collection.insertMany(docs);
  // Multikey index: one entry per embedded rental. A $match on the rental date at the
  // start of a pipeline can use it (see /api/rentals/match-position).
  await collection.createIndex({ "recent_rentals.rental_date": 1 });
  return docs.length;
}

async function main() {
  console.log(`films: ${await loadFilms()} documents`);
  console.log(`customers: ${await loadCustomers()} documents`);
}

main().finally(() => Promise.all([prisma.$disconnect(), mongo.close()]));
