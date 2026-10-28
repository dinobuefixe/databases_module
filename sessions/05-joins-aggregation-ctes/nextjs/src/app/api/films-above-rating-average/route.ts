import { filmsAboveRatingAverage } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/films-above-rating-average?impl=orm|sql
export function GET(request: Request) {
  return answer(request, filmsAboveRatingAverage);
}
