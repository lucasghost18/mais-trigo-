#!/usr/bin/env bash
set -euo pipefail

# Create a tar.gz distribution from the project suitable for copying to servers.
# Usage: ./scripts/make_linux_tar.sh 1.0.0

VERSION=${1:-1.0.0}
ROOT_DIR=$(pwd)
OUT_DIR="$ROOT_DIR/dist"
TMPDIR=$(mktemp -d)
PKG_NAME=mais-trigo-$VERSION

mkdir -p "$OUT_DIR"
mkdir -p "$TMPDIR/$PKG_NAME"

# Copy project files excluding venv, dist and git
rsync -a --exclude='.venv' --exclude='dist' --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' "$ROOT_DIR/" "$TMPDIR/$PKG_NAME/"

# Create tarball
pushd "$TMPDIR"
 tar czf "$OUT_DIR/$PKG_NAME.tar.gz" "$PKG_NAME"
popd

rm -rf "$TMPDIR"

echo "Created $OUT_DIR/$PKG_NAME.tar.gz"
