import { customersWithoutRentals } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/customers-without-rentals?impl=orm|sql
export function GET(request: Request) {
  return answer(request, customersWithoutRentals);
}
