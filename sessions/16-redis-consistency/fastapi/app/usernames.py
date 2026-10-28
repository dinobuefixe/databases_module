"""Change a customer's username only if the new one is free: WATCH version and Lua version.

Keys: `usernames` (set of every username taken) and `customer:{id}` (hash with a
`username` field). Both must change together, or two customers can end up with
the same name.

Both versions read the old name inside the transaction or the script. Read before
it, two changes to the same customer can remove the same old name, and the name the
first one set stays in `usernames` with nobody using it.
"""

import redis

from app.clients import r


def change_username_watch(customer_id: int, new: str) -> bool:
    customer_key = f"customer:{customer_id}"
    with r.pipeline() as pipe:
        while True:
            try:
                # If anyone changes a watched key between WATCH and EXEC, EXEC fails
                # with WatchError and we try again with fresh data.
                pipe.watch("usernames", customer_key)
                old = pipe.hget(customer_key, "username")
                if old == new:
                    pipe.unwatch()
                    return True
                if pipe.sismember("usernames", new):
                    pipe.unwatch()
                    return False
                pipe.multi()
                if old:
                    pipe.srem("usernames", old)
                pipe.sadd("usernames", new)
                pipe.hset(customer_key, "username", new)
                pipe.execute()
                return True
            except redis.WatchError:
                continue


# The same logic runs inside Redis in one step: no other command can run in between,
# so no WATCH and no retry loop. It reads the old name itself instead of receiving it.
_change = r.register_script("""
if redis.call('SISMEMBER', KEYS[1], ARGV[1]) == 1 then
    return redis.call('HGET', KEYS[2], 'username') == ARGV[1] and 1 or 0
end
local old = redis.call('HGET', KEYS[2], 'username')
if old then redis.call('SREM', KEYS[1], old) end
redis.call('SADD', KEYS[1], ARGV[1])
redis.call('HSET', KEYS[2], 'username', ARGV[1])
return 1
""")


def change_username_lua(customer_id: int, new: str) -> bool:
    return _change(keys=["usernames", f"customer:{customer_id}"], args=[new]) == 1
