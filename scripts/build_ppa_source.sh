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

# Remove these packages from requirements.txt so pip doesn't try to install them (or download them)
sed -i '/^[Pp]y[Gg][Oo]bject/Id' requirements.txt
sed -i '/^dbus-python/d' requirements.txt
sed -i '/^pycairo/d' requirements.txt
sed -i '/^evdev/d' requirements.txt

pip download --python-version 3.12 --only-binary=:all: --no-deps -r requirements.txt poetry-core setuptools wheel pip --dest wheels/ || pip download --python-version 3.12 --only-binary=:all: --no-deps . poetry-core setuptools wheel pip --dest wheels/

# Remove packages that we want to use from system (avoid building from sdist)
# (Though they shouldn't be downloaded now anyway)
rm -f wheels/PyGObject* wheels/dbus-python* wheels/pycairo* wheels/evdev*


# Get version from pyproject.toml
VERSION=$(grep "^version =" pyproject.toml | cut -d '"' -f 2)

# Use DISTRO env var if set, otherwise default to noble
DISTRO=${DISTRO:-noble}

# Use per-distro version suffix so each distro gets a unique .changes file
# e.g. 3.3.0-1~noble1 and 3.3.0-1~resolute1
DEBVERSION="${VERSION}-1~${DISTRO}1"

# Create debian/changelog entry for this distro if missing
if ! grep -q "($DEBVERSION)" debian/changelog; then
    echo "Updating changelog to $DEBVERSION ($DISTRO)"
    dch -v "$DEBVERSION" --distribution $DISTRO "New release $VERSION"
fi

# Build source package
# -S: source only
# Export DEBSIGN_KEYID to force debsign to use it, avoiding maintainer lookup
if [ -n "$GPG_KEY_ID" ]; then
    export DEBSIGN_KEYID="$GPG_KEY_ID"
fi
# Create orig tarball using the standard naming convention (shared across distros)
# Always use -sa so the orig tarball is included in every upload — Launchpad
# accepts duplicate uploads of the same tarball (matched by checksum) and this
# avoids a race where a later distro upload arrives before Launchpad has
# processed the first one and associated the orig.
TARBALL="../nuxbt_${VERSION}.orig.tar.gz"
if [ ! -f "$TARBALL" ]; then
    tar --exclude='./debian' --exclude='./.git' --exclude='./dist_ppa' --exclude='./dist' -czf "$TARBALL" .
fi

# -d: do not check build dependencies (dh-virtualenv might be missing locally)
echo "Building source package for version $VERSION ($DISTRO)..."
debuild -S -sa -k"$GPG_KEY_ID" -d

echo "Source package for $DISTRO built in parent directory."
