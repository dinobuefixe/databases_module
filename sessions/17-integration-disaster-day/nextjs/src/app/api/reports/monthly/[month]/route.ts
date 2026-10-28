import { NextResponse } from "next/server";
import { MongoServerError } from "mongodb";
import { mongoDb } from "@/lib/mongo";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ month: string }> };
type Report = {
  _id: string;
  generated_at: Date;
  stores: { store_id: number; payments: number; revenue: string }[];
};

const reports = () => mongoDb().collection<Report>("monthly_reports");

// "2022-07" -> [2022-07-01, 2022-08-01), or null if the format is wrong.
function monthRange(month: string): [Date, Date] | null {
  const m = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(month);
  if (!m) return null;
  const [year, mon] = [Number(m[1]), Number(m[2])];
  return [new Date(Date.UTC(year, mon - 1, 1)), new Date(Date.UTC(year, mon, 1))];
}

// POST /api/reports/monthly/{YYYY-MM}: builds the report once; a second call gets 409.
export async function POST(_request: Request, { params }: Params) {
  const { month } = await params;
  const range = monthRange(month);
  if (!range) return NextResponse.json({ error: "month must be YYYY-MM" }, { status: 400 });

  // A date range rather than to_char(payment_date, 'YYYY-MM') = $1: the range lets
  // PostgreSQL read only that month's partition of payment and use indexes.
  const rows = await prisma.$queryRaw<{ store_id: number; payments: bigint; revenue: string }[]>`
    SELECT st.store_id, count(*) AS payments, sum(p.amount)::text AS revenue
    FROM payment p
    JOIN staff st ON st.staff_id = p.staff_id
    WHERE p.payment_date >= ${range[0]} AND p.payment_date < ${range[1]}
    GROUP BY st.store_id
    ORDER BY st.store_id`;
  if (rows.length === 0) {
    return NextResponse.json({ error: `No payments in ${month}; nothing to freeze` }, { status: 422 });
  }

  const report: Report = {
    _id: month, // deterministic: the month is the key, so the report can only be written once
    generated_at: new Date(),
    // Money as a string keeps the exact value PostgreSQL computed.
    stores: rows.map((r) => ({ store_id: r.store_id, payments: Number(r.payments), revenue: r.revenue })),
  };
  try {
    await reports().insertOne(report);
  } catch (err) {
    if (err instanceof MongoServerError && err.code === 11000) {
      return NextResponse.json({ error: `Report ${month} already exists and is frozen` }, { status: 409 });
    }
    throw err;
  }
  return NextResponse.json({ _id: month, stores: report.stores.length }, { status: 201 });
}

// GET /api/reports/monthly/{YYYY-MM}
export async function GET(_request: Request, { params }: Params) {
  const { month } = await params;
  const report = await reports().findOne({ _id: month });
  if (!report) return NextResponse.json({ error: `No report for ${month}` }, { status: 404 });
  return NextResponse.json(report);
}
