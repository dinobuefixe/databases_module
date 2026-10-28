import type { Document } from "mongodb";

// Rentals per month from the rentals embedded in customers. Used by GET /api/rentals/per-month
// and by POST /api/reports/rentals-per-month, which materialises it with $merge.
export const rentalsPerMonth: Document[] = [
  { $unwind: "$recent_rentals" },
  {
    $group: {
      _id: { $dateTrunc: { date: "$recent_rentals.rental_date", unit: "month" } },
      rentals: { $sum: 1 },
    },
  },
];
