import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const PROFILE_TTL_SECONDS = 600;

export const profileKey = (customerId: number) => `profile:${customerId}`;

export type Profile = { customer_id: number; first_name: string; last_name: string; email: string | null };

export function loadProfile(customerId: number): Promise<Profile | null> {
  return prisma.customer.findUnique({
    where: { customer_id: customerId },
    select: { customer_id: true, first_name: true, last_name: true, email: true },
  });
}

export async function getProfile(customerId: number): Promise<Profile | null> {
  const redis = await getRedis();
  const cached = await redis.get(profileKey(customerId));
  if (cached) return JSON.parse(cached);

  const profile = await loadProfile(customerId);
  if (profile) {
    await redis.set(profileKey(customerId), JSON.stringify(profile), {
      expiration: { type: "EX", value: PROFILE_TTL_SECONDS },
    });
  }
  return profile;
}
