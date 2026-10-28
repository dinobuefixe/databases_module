# Session 18: Cross-group review

The tutorial from [session 18](../../README.md#session-18-cross-group-review-and-documentation), written three times as independent projects.

Each project is a small film review app on top of Pagila that works and has problems. Review it as if it were another group's repository:

1. Go through `REVIEW_CHECKLIST.md` one item at a time.
2. Open one issue per problem with the template in `.github/ISSUE_TEMPLATE/review.md` (Problem, Where, Why it matters, Suggestion).
3. Fix each issue on its own branch, with a pull request that uses `.github/pull_request_template.md` and says `Fixes #N`.

The app's README is part of the review: compare it with the list of what a project README must contain in the session tutorial.

| Project | Port |
|---------|------|
| [fastapi](fastapi/) | 8000 |
| [django](django/) | 8001 |
| [nextjs](nextjs/) | 3000 |

GitHub only reads issue and pull request templates from the `.github/` folder at the root of a repository. To use these templates in your group repository, copy them there.
