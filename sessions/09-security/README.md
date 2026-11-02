# Session 09: Security

The tutorial from [session 09](../../README.md#session-09-security), written three times as independent projects.

Least privilege on the three engines and the two injection attacks from the tutorial. PostgreSQL gets the `migrations`, `app` and `readonly` roles, MongoDB a user limited to one database, Redis an ACL user that cannot run dangerous commands. Two endpoints are vulnerable on purpose, next to their safe versions, and passwords are stored as hashes.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | argon2 hashes | 8000 |
| [django](django/) | argon2 or bcrypt hashes | 8001 |
| [nextjs](nextjs/) | bcrypt hashes | 3000 |

The unsafe endpoints exist only to run the attacks locally. Each README shows the payloads.
