import { rentalsPerStaff } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/rentals-per-staff?impl=orm|sql
export function GET(request: Request) {
  return answer(request, rentalsPerStaff);
}
