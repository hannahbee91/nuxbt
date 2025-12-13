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

# Vendor dependencies
echo "Vendoring dependencies..."
mkdir -p wheels
pip download -r <(pip freeze) poetry-core setuptools wheel pip --dest wheels/ || pip download . poetry-core setuptools wheel pip --dest wheels/
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
# -d: do not check build dependencies (dh-virtualenv might be missing locally)
echo "Building source package for version $VERSION..."
debuild -S -sa -k"$GPG_KEY_ID" -d

echo "Source package built in parent directory."
