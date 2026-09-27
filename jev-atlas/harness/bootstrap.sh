#!/usr/bin/env bash
# Get the patched jev-ultrafast harness ready for the ADIT demo.
#
#   jev-atlas/harness/bootstrap.sh              # the copy vendored in this repository
#   jev-atlas/harness/bootstrap.sh TARGET_DIR   # or build a fresh copy elsewhere, without git
#
# The vendored copy (jev-atlas/vendor/jev-ultrafast) is already patched, so for it this
# only installs the locked dependencies with uv and runs the test suite. For a TARGET_DIR
# that does not exist yet, it first downloads the pinned upstream commit as a tarball and
# applies local-changes.patch, which gives the same tree.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target="${1:-$here/../vendor/jev-ultrafast}"
repo="$(grep -v '^#' "$here/UPSTREAM" | sed -n 1p)"
commit="$(grep -v '^#' "$here/UPSTREAM" | sed -n 2p)"

if [ -f "$target/pyproject.toml" ] && [ -f "$target/jev_ultrafast/atlas.py" ]; then
  echo "Using the patched harness already in $target"
elif [ -e "$target" ]; then
  echo "Refusing to overwrite existing $target" >&2
  exit 1
else
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  echo "Downloading $repo at $commit"
  curl -fsSL -o "$tmp/upstream.tar.gz" "$repo/archive/$commit.tar.gz"
  tar -xzf "$tmp/upstream.tar.gz" -C "$tmp"
  mv "$tmp/$(basename "$repo")-$commit" "$target"
  echo "Applying local changes"
  patch -p1 -d "$target" --forward --batch < "$here/local-changes.patch"
fi

cd "$target"
# --frozen: install exactly what uv.lock pins and never rewrite the lock, whatever
# package index this machine's own uv configuration points at.
uv sync --frozen
uv run --frozen pytest -q

cat <<MSG

Ready: $(pwd)
Next: cp .env.example .env and fill in TYPESAFE_API_KEY (and the text-model keys).
MSG
