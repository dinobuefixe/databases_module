import { Prisma } from "@/generated/prisma/client";
import { prisma } from "@/lib/prisma";

// The ten questions from the tutorial, each written twice: with the Prisma
// query API (orm) and with the tutorial's SQL through $queryRaw (sql).
// Both versions return the same rows in the same order; scripts/compare.ts
// checks that.
//
// Small changes to the tutorial's SQL: ::int on counts, because $queryRaw
// returns a bigint for count(*) and JSON cannot hold a bigint; a customer_id
// tie-breaker in ORDER BY, so that both versions sort ties the same way; and
// the changes noted in questions 3 and 8.

// 1. How many rentals has each staff member handled, per store?
export const rentalsPerStaff = {
  // Prisma counts a relation with _count and can sort by it. It starts from
  // staff, so it behaves like a LEFT JOIN: staff with no rentals would come
  // back with 0. The "some" filter keeps only staff who handled a rental,
  // like the INNER JOIN in the SQL.
  orm: async () => {
    const staff = await prisma.staff.findMany({
      where: { rental: { some: {} } },
      select: { store_id: true, first_name: true, last_name: true, _count: { select: { rental: true } } },
      orderBy: [{ store_id: "asc" }, { rental: { _count: "desc" } }],
    });
    return staff.map((s) => ({
      store_id: s.store_id,
      first_name: s.first_name,
      last_name: s.last_name,
      rentals: s._count.rental,
    }));
  },
  sql: () => prisma.$queryRaw`
    SELECT s.store_id, st.first_name, st.last_name, count(*)::int AS rentals
    FROM rental r
    JOIN staff st ON st.staff_id = r.staff_id
    JOIN store s  ON s.store_id  = st.store_id
    GROUP BY s.store_id, st.staff_id
    ORDER BY s.store_id, rentals DESC`,
};

// 2. Which customers rented more than 40 films? (HAVING)
export const frequentCustomers = {
  // groupBy + having produces GROUP BY ... HAVING, but groupBy cannot include
  // a relation, so the names need a second query and a merge in JavaScript.
  orm: async () => {
    const groups = await prisma.rental.groupBy({
      by: ["customer_id"],
      _count: { _all: true },
      having: { customer_id: { _count: { gt: 40 } } },
      orderBy: [{ _count: { customer_id: "desc" } }, { customer_id: "asc" }],
    });
    const customers = await prisma.customer.findMany({
      where: { customer_id: { in: groups.map((g) => g.customer_id) } },
      select: { customer_id: true, first_name: true, last_name: true },
    });
    const byId = new Map(customers.map((c) => [c.customer_id, c]));
    return groups.map((g) => ({ ...byId.get(g.customer_id)!, rentals: g._count._all }));
  },
  sql: () => prisma.$queryRaw`
    SELECT c.customer_id, c.first_name, c.last_name, count(*)::int AS rentals
    FROM customer c
    JOIN rental r ON r.customer_id = c.customer_id
    GROUP BY c.customer_id
    HAVING count(*) > 40
    ORDER BY rentals DESC, c.customer_id`,
};

// 3. How many rentals has each customer made, including customers with none?
// (LEFT JOIN, count(column))
export const rentalsPerCustomer = {
  // _count starts from customer, so customers with no rentals come back with 0,
  // like the LEFT JOIN. The log shows how: Prisma counts rentals per customer_id
  // in a subquery in FROM and LEFT JOINs that, with COALESCE(..., 0). There is no
  // joined row to count, so the SQL version leaves out the tutorial's
  // joined_rows (count(*)) column.
  orm: async () => {
    const customers = await prisma.customer.findMany({
      select: { customer_id: true, first_name: true, last_name: true, _count: { select: { rental: true } } },
      orderBy: [{ rental: { _count: "asc" } }, { customer_id: "asc" }],
    });
    return customers.map((c) => ({
      customer_id: c.customer_id,
      first_name: c.first_name,
      last_name: c.last_name,
      rentals: c._count.rental,
    }));
  },
  sql: () => prisma.$queryRaw`
    SELECT c.customer_id, c.first_name, c.last_name,
           count(r.rental_id)::int AS rentals
    FROM customer c
    LEFT JOIN rental r ON r.customer_id = c.customer_id
    GROUP BY c.customer_id
    ORDER BY rentals, c.customer_id`,
};

// 4. Which films have no copy in any store? (anti-join)
export const filmsWithoutInventory = {
  // "none" on a relation filter is Prisma's anti-join. Look at the log to see
  // the subquery it generates.
  orm: () =>
    prisma.film.findMany({
      where: { inventory: { none: {} } },
      select: { film_id: true, title: true },
      orderBy: { film_id: "asc" },
    }),
  sql: () => prisma.$queryRaw`
    SELECT f.film_id, f.title
    FROM film f
    WHERE NOT EXISTS (
        SELECT 1 FROM inventory i WHERE i.film_id = f.film_id
    )
    ORDER BY f.film_id`,
};

// 5. Which customers have never rented a film? (anti-join with LEFT JOIN)
export const customersWithoutRentals = {
  // The same "none" filter as question 4. Prisma writes it as a subquery, not as
  // LEFT JOIN ... IS NULL; the result is the same.
  orm: () =>
    prisma.customer.findMany({
      where: { rental: { none: {} } },
      select: { customer_id: true, first_name: true, last_name: true },
      orderBy: { customer_id: "asc" },
    }),
  sql: () => prisma.$queryRaw`
    SELECT c.customer_id, c.first_name, c.last_name
    FROM customer c
    LEFT JOIN rental r ON r.customer_id = c.customer_id
    WHERE r.rental_id IS NULL
    ORDER BY c.customer_id`,
};

// 6. Which customers share their first and last name with another customer?
// (self join)
export const duplicateCustomerNames = {
  // Prisma cannot join a model to itself on columns that are not a relation.
  // groupBy + having finds the names used more than once, a second query loads
  // those customers, and the pairs are built in JavaScript.
  orm: async () => {
    const names = await prisma.customer.groupBy({
      by: ["first_name", "last_name"],
      having: { customer_id: { _count: { gt: 1 } } },
    });
    const customers = await prisma.customer.findMany({
      where: { OR: names.map((n) => ({ first_name: n.first_name, last_name: n.last_name })) },
      select: { customer_id: true, first_name: true, last_name: true },
      orderBy: [{ last_name: "asc" }, { first_name: "asc" }, { customer_id: "asc" }],
    });
    return customers.flatMap((a, i) =>
      customers
        .slice(i + 1)
        .filter((b) => b.first_name === a.first_name && b.last_name === a.last_name)
        .map((b) => ({
          customer_id: a.customer_id,
          other_customer_id: b.customer_id,
          first_name: a.first_name,
          last_name: a.last_name,
        })),
    );
  },
  sql: () => prisma.$queryRaw`
    SELECT c1.customer_id, c2.customer_id AS other_customer_id, c1.first_name, c1.last_name
    FROM customer c1
    JOIN customer c2
      ON  c2.first_name  = c1.first_name
      AND c2.last_name   = c1.last_name
      AND c2.customer_id > c1.customer_id
    ORDER BY c1.last_name, c1.first_name, c1.customer_id, other_customer_id`,
};

// 7. Which films are longer than the average film? (subquery in WHERE)
export const filmsLongerThanAverage = {
  // Prisma has no subqueries in where, so the average is a first query. length
  // is an Int, and Prisma silently sends 115.27 as 115 in an Int filter. With gt
  // and whole lengths that gives the same films; Math.floor makes it visible.
  orm: async () => {
    const { _avg } = await prisma.film.aggregate({ _avg: { length: true } });
    return prisma.film.findMany({
      where: { length: { gt: Math.floor(_avg.length!) } },
      select: { film_id: true, title: true, length: true },
      orderBy: [{ length: "desc" }, { film_id: "asc" }],
    });
  },
  sql: () => prisma.$queryRaw`
    SELECT f.film_id, f.title, f.length
    FROM film f
    WHERE f.length > (SELECT avg(length) FROM film)
    ORDER BY f.length DESC, f.film_id`,
};

// 8. Which films are longer than the average film with the same rating?
// (correlated subquery)
export const filmsAboveRatingAverage = {
  // No correlated subqueries either: groupBy computes the average per rating,
  // then one OR condition per rating filters the films. rating is a PostgreSQL
  // enum; Prisma returns its own names (PG_13), so the SQL version casts to text
  // and the ORM version maps the names back with ratingLabel.
  orm: async () => {
    const averages = await prisma.film.groupBy({ by: ["rating"], _avg: { length: true } });
    const films = await prisma.film.findMany({
      where: { OR: averages.map((a) => ({ rating: a.rating, length: { gt: Math.floor(a._avg.length!) } })) },
      select: { film_id: true, title: true, rating: true, length: true },
      orderBy: [{ rating: "asc" }, { length: "desc" }, { film_id: "asc" }],
    });
    return films.map((f) => ({ ...f, rating: f.rating && ratingLabel[f.rating] }));
  },
  sql: () => prisma.$queryRaw`
    SELECT f.film_id, f.title, f.rating::text AS rating, f.length
    FROM film f
    WHERE f.length > (
        SELECT avg(f2.length) FROM film f2 WHERE f2.rating = f.rating
    )
    ORDER BY f.rating, f.length DESC, f.film_id`,
};

// The database values behind Prisma's enum names, as in @map in the schema.
const ratingLabel = { G: "G", PG: "PG", PG_13: "PG-13", R: "R", NC_17: "NC-17" } as const;

// 9. How many rentals has each customer made, and how much have they paid?
// (subqueries in FROM)
export const customerTotals = {
  // _count is already a subquery in FROM (see question 3). payment has no
  // relation in the schema, so its totals are a groupBy merged in JavaScript.
  // Prisma never joins rental and payment to customer in one query, so it cannot
  // multiply the rows the way the wrong SQL in the tutorial does.
  orm: async () => {
    const customers = await prisma.customer.findMany({
      select: { customer_id: true, first_name: true, last_name: true, _count: { select: { rental: true } } },
      orderBy: { customer_id: "asc" },
    });
    const payments = await prisma.payment.groupBy({ by: ["customer_id"], _sum: { amount: true } });
    const paid = new Map(payments.map((p) => [p.customer_id, p._sum.amount!]));
    return customers.map((c) => ({
      customer_id: c.customer_id,
      first_name: c.first_name,
      last_name: c.last_name,
      rentals: c._count.rental,
      paid: paid.get(c.customer_id) ?? new Prisma.Decimal(0),
    }));
  },
  sql: () => prisma.$queryRaw`
    SELECT c.customer_id, c.first_name, c.last_name,
           coalesce(r.rentals, 0)::int AS rentals,
           coalesce(p.paid, 0)         AS paid
    FROM customer c
    LEFT JOIN (
        SELECT customer_id, count(*) AS rentals FROM rental GROUP BY customer_id
    ) r ON r.customer_id = c.customer_id
    LEFT JOIN (
        SELECT customer_id, sum(amount) AS paid FROM payment GROUP BY customer_id
    ) p ON p.customer_id = c.customer_id
    ORDER BY c.customer_id`,
};

// 10. Which customers spent more than the average customer? (CTE in steps)
export const aboveAverageSpenders = {
  // Prisma has no CTEs. The ORM version runs the steps as separate queries and
  // computes the average in JavaScript, so every customer's total travels
  // from the database to the application first.
  orm: async () => {
    const spend = await prisma.payment.groupBy({ by: ["customer_id"], _sum: { amount: true } });
    const totals = spend.map((s) => ({ customer_id: s.customer_id, total: s._sum.amount! }));
    const average = totals.reduce((sum, t) => sum.plus(t.total), totals[0].total.minus(totals[0].total))
      .dividedBy(totals.length);
    const above = totals
      .filter((t) => t.total.greaterThan(average))
      .sort((a, b) => b.total.comparedTo(a.total) || a.customer_id - b.customer_id);
    const customers = await prisma.customer.findMany({
      where: { customer_id: { in: above.map((t) => t.customer_id) } },
      select: { customer_id: true, first_name: true, last_name: true },
    });
    const byId = new Map(customers.map((c) => [c.customer_id, c]));
    return above.map((t) => ({
      first_name: byId.get(t.customer_id)!.first_name,
      last_name: byId.get(t.customer_id)!.last_name,
      total: t.total,
    }));
  },
  sql: () => prisma.$queryRaw`
    WITH spend AS (
        SELECT customer_id, sum(amount) AS total
        FROM payment
        GROUP BY customer_id
    ),
    average AS (
        SELECT avg(total) AS avg_total FROM spend
    )
    SELECT c.first_name, c.last_name, s.total
    FROM spend s
    JOIN customer c ON c.customer_id = s.customer_id
    CROSS JOIN average a
    WHERE s.total > a.avg_total
    ORDER BY s.total DESC, c.customer_id`,
};

export const questions = {
  "rentals-per-staff": rentalsPerStaff,
  "frequent-customers": frequentCustomers,
  "rentals-per-customer": rentalsPerCustomer,
  "films-without-inventory": filmsWithoutInventory,
  "customers-without-rentals": customersWithoutRentals,
  "duplicate-customer-names": duplicateCustomerNames,
  "films-longer-than-average": filmsLongerThanAverage,
  "films-above-rating-average": filmsAboveRatingAverage,
  "customer-totals": customerTotals,
  "above-average-spenders": aboveAverageSpenders,
};

export type Implementation = { orm: () => Promise<unknown>; sql: () => Promise<unknown> };
