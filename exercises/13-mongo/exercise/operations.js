// operations.js: the eight required operations.
// Run on freshly loaded collections (operations 6 to 8 change data):
//   mongosh "mongodb://localhost:27017/pagila" operations.js

function report(n, label, expected, actual) {
  print(`#${n} ${label}`);
  print(`   expected: ${JSON.stringify(expected)}`);
  print(`   actual:   ${JSON.stringify(actual)}`);
}

// 1. PG-13 films longer than 120 minutes
report(1, "films rated PG-13 longer than 120 min", 118,
  db.films.countDocuments({ rating: "PG-13", length: { $gt: 120 } }));

// 2. Films in which actor 1 appears
report(2, "films with actor 1", 19,
  db.films.countDocuments({ "actors.actor_id": 1 }));

// 3. Horror films with rental rate 0.99
report(3, "Horror films with rental_rate 0.99", 43,
  db.films.countDocuments({ categories: "Horror", rental_rate: NumberDecimal("0.99") }));

// 4. Customers with at least one unreturned rental among recent_rentals
report(4, "customers with an unreturned embedded rental", 56,
  db.customers.countDocuments({ recent_rentals: { $elemMatch: { return_date: null } } }));

// 5. Customer 1: names and recent rental titles only
const c5 = db.customers.findOne(
  { _id: 1 },
  { _id: 0, first_name: 1, last_name: 1, "recent_rentals.title": 1 }
);
report(5, "customer 1 projection (1 doc, 10 titles)", 10,
  { first_name: c5.first_name, last_name: c5.last_name,
    titles: c5.recent_rentals.map((r) => r.title) });

// 6. Raise rental_rate by 0.50 for NC-17 films shorter than 60 minutes
const r6 = db.films.updateMany(
  { rating: "NC-17", length: { $lt: 60 } },
  { $inc: { rental_rate: NumberDecimal("0.50") } }
);
report(6, "NC-17 films under 60 min, rate +0.50 (modified)", 21, r6.modifiedCount);

// 7. Push a new rental to the front of customer 1's recent_rentals, keep 10
const lastRental = db.rentals.find().sort({ _id: -1 }).limit(1).next();
const newRental = {
  rental_id: lastRental._id + 1,
  film_id: 1,
  title: "ACADEMY DINOSAUR",
  rental_date: new Date(),
  return_date: null,
};
const r7 = db.customers.updateOne(
  { _id: 1 },
  { $push: { recent_rentals: { $each: [newRental], $position: 0, $slice: 10 } } }
);
const after7 = db.customers.findOne({ _id: 1 }, { recent_rentals: 1 });
report(7, "customer 1 recent_rentals after push (10 items, new rental first)", "10 items, first = new", {
  modified: r7.modifiedCount,
  length: after7.recent_rentals.length,
  first_rental_id: after7.recent_rentals[0].rental_id,
  expected_first_rental_id: newRental.rental_id,
});

// 8. Upsert film 1001 twice with $setOnInsert
db.films.deleteOne({ _id: 1001 }); // start clean so the script can be re-run
const upsertUpdate = { $setOnInsert: { title: "TEST FILM" } };
const r8a = db.films.updateOne({ _id: 1001 }, upsertUpdate, { upsert: true });
const r8b = db.films.updateOne({ _id: 1001 }, upsertUpdate, { upsert: true });
report(8, "upsert film 1001, run twice", "run1 upserted 1; run2 matched 1, modified 0", {
  run1: { upserted: r8a.upsertedCount, matched: r8a.matchedCount, modified: r8a.modifiedCount },
  run2: { upserted: r8b.upsertedCount, matched: r8b.matchedCount, modified: r8b.modifiedCount },
});
