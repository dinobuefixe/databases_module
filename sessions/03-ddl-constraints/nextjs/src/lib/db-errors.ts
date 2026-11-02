import { Prisma } from "@/generated/prisma/client";
import { NextResponse } from "next/server";

// PostgreSQL error codes (SQLSTATE) for constraint violations, and the HTTP
// status we answer with. 409: the request conflicts with existing data.
// 422: the data itself breaks a rule.
const STATUS_BY_SQLSTATE: Record<string, number> = {
  "23505": 409, // unique_violation
  "23001": 409, // restrict_violation (ON DELETE RESTRICT)
  "23503": 422, // foreign_key_violation (the referenced row does not exist)
  "23514": 422, // check_violation
  "23502": 422, // not_null_violation
};

type AdapterCause = { originalCode?: string; originalMessage?: string };

export type ConstraintViolation = { status: number; sqlstate: string; constraint: string | null; message: string };

// With the PostgreSQL driver adapter, Prisma 7 keeps the database error in
// err.meta.driverAdapterError.cause. We read the SQLSTATE and the constraint
// name from it, whatever Prisma error code (P2002, P2003, P2039...) wraps it.
export function constraintViolation(err: unknown): ConstraintViolation | null {
  if (!(err instanceof Prisma.PrismaClientKnownRequestError)) return null;
  const cause = (err.meta?.driverAdapterError as { cause?: AdapterCause } | undefined)?.cause;
  const sqlstate = cause?.originalCode;
  if (!sqlstate || !(sqlstate in STATUS_BY_SQLSTATE)) return null;
  const message = cause.originalMessage ?? err.message;
  const constraint = /constraint "([^"]+)"/.exec(message)?.[1] ?? null;
  return { status: STATUS_BY_SQLSTATE[sqlstate], sqlstate, constraint, message };
}

// Turn a constraint violation into a JSON response, or rethrow anything else.
export function violationResponse(err: unknown): NextResponse {
  const v = constraintViolation(err);
  if (!v) throw err;
  return NextResponse.json({ error: v.message, constraint: v.constraint }, { status: v.status });
}
