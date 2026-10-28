import type { RedisClientType } from "redis";

// Two weeks from the first write, so last week's board can still be read during this week.
export const LEADERBOARD_TTL = 14 * 24 * 60 * 60;

// ISO week of a date, e.g. 2026-W41. The week belongs to the year of its Thursday.
function isoWeek(day: Date): string {
  const d = new Date(Date.UTC(day.getFullYear(), day.getMonth(), day.getDate()));
  const weekday = d.getUTCDay() || 7; // Monday = 1 ... Sunday = 7
  d.setUTCDate(d.getUTCDate() + 4 - weekday); // move to the Thursday of the same week
  const firstDay = Date.UTC(d.getUTCFullYear(), 0, 1);
  const week = Math.ceil(((d.getTime() - firstDay) / 86_400_000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

// One sorted set per ISO week: leaderboard:customers:2026-W41.
export const leaderboardKey = (week: string = isoWeek(new Date())) => `leaderboard:customers:${week}`;

// Adds one rental to the customer's score this week. Returns the key and the new score.
export async function recordRental(redis: RedisClientType, customerId: number) {
  const key = leaderboardKey();
  // MULTI/EXEC: the two commands run together, nothing in between.
  const [score] = await redis
    .multi()
    .zIncrBy(key, 1, `customer:${customerId}`)
    // NX: only set the expiry if the key has none, which is on the first write of the week.
    .expire(key, LEADERBOARD_TTL, "NX")
    .exec();
  return { key, score: Number(score) };
}
