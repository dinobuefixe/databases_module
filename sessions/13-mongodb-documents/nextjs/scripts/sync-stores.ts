// Reads every Pagila store from PostgreSQL and upserts one document per store into MongoDB.
import "dotenv/config";
import { mongo } from "@/lib/mongo";
import { prisma } from "@/lib/prisma";
import { stores, type StoreDoc } from "@/lib/stores";

const name = (s: { first_name: string; last_name: string }) => `${s.first_name} ${s.last_name}`;

async function main() {
  // Three joins (address, city, country) and the staff, written as nested includes.
  const rows = await prisma.store.findMany({
    include: {
      address: { include: { city: { include: { country: true } } } },
      staff: { orderBy: { staff_id: "asc" } },
    },
    orderBy: { store_id: "asc" },
  });
  const managers = await prisma.staff.findMany({
    where: { staff_id: { in: rows.map((r) => r.manager_staff_id) } },
  });
  const managerById = new Map(managers.map((m) => [m.staff_id, m]));

  // Same as update_one(..., upsert=True) in a loop, but sent to MongoDB in one round trip.
  const result = await stores().bulkWrite(
    rows.map((r) => {
      const manager = managerById.get(r.manager_staff_id)!;
      const doc: Omit<StoreDoc, "_id"> = {
        manager: { staff_id: manager.staff_id, name: name(manager) },
        address: { line: r.address.address, city: r.address.city.city, country: r.address.city.country.country },
        staff: r.staff.map((s) => ({ staff_id: s.staff_id, name: name(s) })),
      };
      return { updateOne: { filter: { _id: r.store_id }, update: { $set: doc }, upsert: true } };
    }),
  );
  console.log(
    `Read ${rows.length} stores: ${result.upsertedCount} inserted, ${result.matchedCount} already there (${result.modifiedCount} changed)`,
  );
}

main().finally(() => Promise.all([prisma.$disconnect(), mongo.close()]));
