# Sourced by the other scripts: paths, .env and a docker compose helper.
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="$(cd "$project_dir/../../.." && pwd)"
set -a; source "$project_dir/.env"; set +a

# docker compose from the repository root, wherever the script is called from.
compose() { docker compose --project-directory "$repo_root" "$@"; }

latest_backup() { ls -td "$project_dir"/backups/*/ 2>/dev/null | head -n 1; }

# Python from this project's .venv (uv run), started in the project folder so
# `python -m scripts.x` can import `app`.
py() { (cd "$project_dir" && uv run --quiet python "$@"); }
