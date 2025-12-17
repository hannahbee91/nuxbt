#!/bin/bash
set -e

# Default version is None, will try to grab from pyproject.toml if not set
# Use this script to build a deb package of NuxBT for local testing (debian-based systems only)
# Usage: ./scripts/build_deb.sh --version=1.2.3
VERSION=""

# Parse arguments
for i in "$@"; do
  case $i in
    --version=*)
      VERSION="${i#*=}"
      shift # past argument=value
      ;;
    *)
      # unknown option
      ;;
  esac
done

# If VERSION is not set, get it from pyproject.toml
if [ -z "$VERSION" ]; then
    VERSION=$(grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2)
fi

echo "Building version: $VERSION"

# Clean dist
rm -rf dist requirements.txt

# Build the python package (sdist and wheel)
echo "Building python package..."
poetry build

# Export requirements
echo "Exporting requirements..."
poetry self add poetry-plugin-export 2>/dev/null || true
poetry export --without-hashes --format=requirements.txt > requirements.txt

# Create directory structure for nfpm
echo "Preparing directory structure and virtual environment..."
mkdir -p dist/usr/lib/nuxbt

# Create venv in the temporary location
python3 -m venv --copies dist/usr/lib/nuxbt

# Install the package and dependencies into the venv
# Using a subshell to avoid messing with current shell environment
(
    source dist/usr/lib/nuxbt/bin/activate
    # Install dependencies first from the locked requirements
    pip install -r requirements.txt
    # Then install the package itself
    pip install dist/*.whl
)

# Fix shebangs to point to the target location /usr/lib/nuxbt
# This ensures that when installed, they look for python in the right place
echo "Fixing shebangs..."
# we use | as delimiter to avoid escaping /
sed -i 's|#!'"$PWD"'/dist/usr/lib/nuxbt|#!/usr/lib/nuxbt|g' dist/usr/lib/nuxbt/bin/*

# Clean up __pycache__ inside the venv to reduce size
find dist/usr/lib/nuxbt -name "__pycache__" -type d -exec rm -rf {} +

# Prepare NFPM config without signing
# We create a temporary config file that strips out the signature section for deb
# The signature block is standardly 3 lines in the yaml: signature, method, key_id
echo "Preparing nfpm configuration..."
sed '/signature:/,+2d' nfpm.yaml > nfpm_nosign.yaml

# Run nfpm
# We assume nfpm is installed and available in PATH
if ! command -v nfpm &> /dev/null; then
    echo "nfpm not found. Please install it."
    rm nfpm_nosign.yaml
    exit 1
fi

export VERSION
echo "Packaging DEB..."
nfpm pkg --config nfpm_nosign.yaml --packager deb --target dist/

# Cleanup
rm nfpm_nosign.yaml requirements.txt

echo "Build complete. DEB file is in dist/"
