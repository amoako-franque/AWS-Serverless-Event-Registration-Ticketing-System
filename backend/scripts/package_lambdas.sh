#!/usr/bin/env bash
# Packages each Lambda function directory into build/<name>.zip,
# bundling in lambda/shared/utils.py alongside the handler.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAMBDA_DIR="$ROOT_DIR/lambda"
BUILD_DIR="$ROOT_DIR/build"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

FUNCTIONS=(register list_events get_registrations cancel_registration)

for fn in "${FUNCTIONS[@]}"; do
  echo "Packaging $fn..."
  STAGE_DIR=$(mktemp -d)

  cp "$LAMBDA_DIR/$fn/handler.py" "$STAGE_DIR/"
  cp "$LAMBDA_DIR/shared/utils.py" "$STAGE_DIR/"

  # NOTE: boto3/botocore are NOT installed here - they already ship with the
  # AWS Lambda Python runtime. requirements.txt is for local dev/testing only.
  # If you add a third-party dependency Lambda doesn't provide, install it
  # explicitly here with `pip install <pkg> -t "$STAGE_DIR"`.

  (cd "$STAGE_DIR" && zip -r "$BUILD_DIR/$fn.zip" . -x "*.pyc" "__pycache__/*" > /dev/null)
  rm -rf "$STAGE_DIR"
  echo "  -> $BUILD_DIR/$fn.zip"
done

echo "All functions packaged in $BUILD_DIR"
