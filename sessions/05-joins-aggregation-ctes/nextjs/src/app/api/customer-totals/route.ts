import { customerTotals } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/customer-totals?impl=orm|sql
export function GET(request: Request) {
  return answer(request, customerTotals);
}
