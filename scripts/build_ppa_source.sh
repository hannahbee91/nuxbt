#!/bin/bash
set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Clean previous builds
rm -rf dist_ppa
mkdir -p dist_ppa

# Export packaging identity
export DEBEMAIL="nuxbt@hannahis.gay"
export DEBFULLNAME="NUXBT Releases"

# Ensure source format is 3.0 (quilt) to support binary vendoring
mkdir -p debian/source
echo "3.0 (quilt)" > debian/source/format

# Vendor dependencies
echo "Vendoring dependencies..."
mkdir -p wheels
poetry export --without-hashes --format=requirements.txt > requirements.txt
pip download -r requirements.txt poetry-core setuptools wheel pip --dest wheels/ || pip download . poetry-core setuptools wheel pip --dest wheels/
# Remove packages that we want to use from system (avoid building from sdist)
rm -f wheels/PyGObject* wheels/dbus-python* wheels/pycairo* wheels/evdev*

# Get version from pyproject.toml
VERSION=$(grep "^version =" pyproject.toml | cut -d '"' -f 2)

# Create debian/changelog if it doesn't match
# Note: This is a simple check, in CI we might force update it.
if ! grep -q "($VERSION" debian/changelog; then
    echo "Updating changelog to $VERSION-1"
    dch -v "$VERSION-1" "New release $VERSION"
fi

# Build source package
# -S: source only
# -sa: include original source
# Export DEBSIGN_KEYID to force debsign to use it, avoiding maintainer lookup
if [ -n "$GPG_KEY_ID" ]; then
    export DEBSIGN_KEYID="$GPG_KEY_ID"
fi
# Create orig tarball
# We need to include the vendored wheels in the tarball so they are available for the build
tar --exclude='./debian' --exclude='./.git' --exclude='./dist_ppa' --exclude='./dist' -czf "../nuxbt_$VERSION.orig.tar.gz" .

# -d: do not check build dependencies (dh-virtualenv might be missing locally)
echo "Building source package for version $VERSION..."
debuild -S -sa -k"$GPG_KEY_ID" -d

echo "Source package built in parent directory."
