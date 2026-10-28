import { duplicateCustomerNames } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/duplicate-customer-names?impl=orm|sql
export function GET(request: Request) {
  return answer(request, duplicateCustomerNames);
}
