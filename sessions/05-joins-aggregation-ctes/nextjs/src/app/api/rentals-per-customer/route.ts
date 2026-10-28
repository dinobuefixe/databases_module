import { rentalsPerCustomer } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/rentals-per-customer?impl=orm|sql
export function GET(request: Request) {
  return answer(request, rentalsPerCustomer);
}
