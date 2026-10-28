import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const ratingKey = (filmId: number) => `film:${filmId}:rating`;

export async function refreshFilmRating(filmId: number) {
  const summary = await prisma.film_rating.aggregate({
    where: { film_id: filmId },
    _avg: { stars: true },
    _count: { stars: true },
  });
  const redis = await getRedis();
  await redis.hSet(ratingKey(filmId), {
    average: (summary._avg.stars ?? 0).toFixed(2),
    count: summary._count.stars,
  });
}
