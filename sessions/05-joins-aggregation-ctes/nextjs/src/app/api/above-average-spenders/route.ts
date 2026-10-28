import { aboveAverageSpenders } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/above-average-spenders?impl=orm|sql
export function GET(request: Request) {
  return answer(request, aboveAverageSpenders);
}
