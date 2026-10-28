import { frequentCustomers } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/frequent-customers?impl=orm|sql
export function GET(request: Request) {
  return answer(request, frequentCustomers);
}
