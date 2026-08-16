#!/usr/bin/env bash
#
# Build and deploy the combined Cloudflare Pages site (project: kidzone).
#
#     /         KidZoneWeb
#     /arcade/  ArcadeWeb
#
#   ./deploy.sh                  build + deploy a preview
#   ./deploy.sh --production     build + deploy to production (branch main)
#   ./deploy.sh --branch NAME    build + deploy a named preview branch
#
# Four things this encodes, each of which has broken a deploy before:
#
#   * pygbag resolves default.tmpl relative to the *current directory*, not
#     the app directory. Building from the parent silently swaps the project's
#     custom shell for pygbag's stock one, so each app is built from inside
#     its own folder.
#   * A long-running `pygbag` dev server repacks the archive when it thinks
#     the tree changed, and that repack can emit a 2-file stub instead of the
#     full bundle. A stub deploys perfectly happily and the app never boots,
#     so the archive is checked before anything is uploaded.
#   * The .apk is only ever fetched by the loader on .itch.zone hosts; on
#     Pages the browser reads the .tar.gz. Uploading it wasted several MB per
#     deploy, so it is deliberately left out of the staging directory.
#   * Nothing used to run the test suite before shipping, so a change could
#     break games and only surface once a child hit the broken screen. Both
#     tests/quiz_behaviour.py (the eight shared-framework games, deeply) and
#     tests/game_smoke.py (the other 31, for crash-on-boot only) run here,
#     before either app is built, and abort the deploy on any failure.
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$REPO/pygbag_env/bin/python"
WRANGLER="npx wrangler@4.120.0"
PROJECT="kidzone"

# A stable preview alias (preview.kidzone-5fb.pages.dev) rather than a fresh
# one per run, so there is a single URL worth bookmarking on the test tablet.
BRANCH="preview"
while [ $# -gt 0 ]; do
    case "$1" in
        --production) BRANCH="main"; shift ;;
        --branch) BRANCH="$2"; shift 2 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

run_tests() {
    echo "==> running tests/quiz_behaviour.py"
    if ! "$PYTHON" "$REPO/tests/quiz_behaviour.py"; then
        echo "ABORT: quiz behaviour tests failed - fix them before deploying." >&2
        exit 1
    fi
    echo "==> running tests/game_smoke.py"
    if ! "$PYTHON" "$REPO/tests/game_smoke.py"; then
        echo "ABORT: a game crashed on boot - fix it before deploying." >&2
        exit 1
    fi
}

build() {  # build <app-dir> <archive-name> <min-entries>
    local dir="$1" archive="$2" min="$3"
    echo "==> building $dir"
    ( cd "$REPO/$dir" && "$PYTHON" -m pygbag --build . >/dev/null )

    local tarball="$REPO/$dir/build/web/$archive.tar.gz"
    local entries
    entries="$(tar tzf "$tarball" | wc -l)"
    if [ "$entries" -lt "$min" ]; then
        echo "ABORT: $archive.tar.gz has only $entries entries (expected >= $min)." >&2
        echo "       That is the stub-repack failure. Stop any running pygbag dev" >&2
        echo "       server and rebuild before deploying." >&2
        exit 1
    fi
    echo "    $entries files, $(du -h "$tarball" | cut -f1)"
}

stage() {  # stage <app-dir> <archive-name> <destination>
    local dir="$1" archive="$2" dest="$3"
    mkdir -p "$dest"
    # Deliberately not the .apk - see the header.
    cp "$REPO/$dir/build/web/index.html" \
       "$REPO/$dir/build/web/favicon.png" \
       "$REPO/$dir/build/web/$archive.tar.gz" "$dest/"
}

run_tests

build KidZoneWeb kidzoneweb 400
build ArcadeWeb arcadeweb 40

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
stage KidZoneWeb kidzoneweb "$STAGING"
stage ArcadeWeb arcadeweb "$STAGING/arcade"

echo "==> deploying to branch '$BRANCH' ($(du -sh "$STAGING" | cut -f1))"
$WRANGLER pages deploy "$STAGING" \
    --project-name "$PROJECT" --branch "$BRANCH" --commit-dirty=true
