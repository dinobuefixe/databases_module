import { filmsLongerThanAverage } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/films-longer-than-average?impl=orm|sql
export function GET(request: Request) {
  return answer(request, filmsLongerThanAverage);
}
