import { filmsWithoutInventory } from "@/lib/questions";
import { answer } from "@/lib/respond";

export const dynamic = "force-dynamic";

// GET /api/films-without-inventory?impl=orm|sql
export function GET(request: Request) {
  return answer(request, filmsWithoutInventory);
}
