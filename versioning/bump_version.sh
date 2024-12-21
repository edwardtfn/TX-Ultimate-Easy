#!/bin/bash

VERSION_FILE="./versioning/VERSION"
VERSION_YAML_FILE="./versioning/VERSION_YAML"

# Read the current version
if [ -f "$VERSION_FILE" ]; then
  CURRENT_VERSION=$(cat "$VERSION_FILE")
else
  CURRENT_VERSION="0.0.0" # Default if file doesn't exist
fi

# Extract components
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%-m) # Use %-m to avoid leading zero for the month
if ! [[ "$CURRENT_VERSION" =~ ^[0-9]{4}\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: Invalid version format in $VERSION_FILE"
  exit 1
fi
CURRENT_SEQ=$(echo "$CURRENT_VERSION" | awk -F. '{print $3}')

VERSION_YEAR=$(echo "$CURRENT_VERSION" | awk -F. '{print $1}')
VERSION_MONTH=$(echo "$CURRENT_VERSION" | awk -F. '{print $2}')

# Determine new version
if [[ "$CURRENT_YEAR" == "$VERSION_YEAR" && "$CURRENT_MONTH" == "$VERSION_MONTH" ]]; then
  NEXT_SEQ=$((CURRENT_SEQ + 1))
else
  NEXT_SEQ=1 # Reset sequence for a new month
fi

NEW_VERSION="${CURRENT_YEAR}.${CURRENT_MONTH}.${NEXT_SEQ}"

# Update the plain text VERSION file
echo "$NEW_VERSION" > "$VERSION_FILE"

# Update the YAML VERSION_YAML file
echo "version: $NEW_VERSION" > "$VERSION_YAML_FILE"

# Commit and tag
if ! git add "$VERSION_FILE" "$VERSION_YAML_FILE"; then
  echo "Error: Failed to stage version files"
  exit 1
fi
if ! git commit -m "Bump version to $NEW_VERSION"; then
  echo "Error: Failed to commit version bump"
  exit 1
fi
if ! git tag "v$NEW_VERSION"; then
  echo "Error: Failed to create version tag"
  exit 1
fi
