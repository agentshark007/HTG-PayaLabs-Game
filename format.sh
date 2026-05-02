#!/usr/bin/env bash

set -euo pipefail

#######################################
# CONFIGURATION (EDIT THIS SECTION)
#######################################

# Files to format (relative or absolute paths)
TARGET_FILES=(
  "app.py"
  "editor.py"
  "main.py"
  # "another_file.py"
  # "src/module/*.py"
)

# Enable/disable tools
USE_ISORT=true
USE_BLACK=true

#######################################
# COLORS
#######################################
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

#######################################
# INTERNAL STATE
#######################################
fail_count=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# UTIL FUNCTIONS
#######################################

log_info() {
  echo -e "${YELLOW}[INFO]: $1${RESET}"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]: $1${RESET}"
}

log_error() {
  echo -e "${RED}[ERROR]: $1${RESET}"
}

run_command() {
  local name="$1"
  shift

  log_info "${name}: Running..."

  if "$@" &>/dev/null; then
    log_success "${name}: Completed"
  else
    log_error "${name}: Failed"
    ((fail_count++))
  fi
}

#######################################
# FILE RESOLUTION
#######################################

resolve_files() {
  local resolved=()

  for pattern in "${TARGET_FILES[@]}"; do
    # Expand glob relative to script directory
    for file in "$SCRIPT_DIR"/$pattern; do
      if [[ -f "$file" ]]; then
        resolved+=("$file")
      else
        log_error "File not found: $pattern"
        ((fail_count++))
      fi
    done
  done

  # Sort files for deterministic order
  IFS=$'\n' resolved=($(sort <<<"${resolved[*]}"))
  unset IFS

  echo "${resolved[@]}"
}

#######################################
# MAIN
#######################################

echo -e "${BLUE}[START]: Formatting started${RESET}"

FILES=($(resolve_files))

if [ ${#FILES[@]} -eq 0 ]; then
  log_error "No valid files to process"
  exit 1
fi

for file in "${FILES[@]}"; do
  log_info "Processing: $file"

  if [ "$USE_ISORT" = true ]; then
    run_command "isort ($file)" python3 -m isort --profile black "$file"
  fi

  if [ "$USE_BLACK" = true ]; then
    run_command "black ($file)" python3 -m black --quiet "$file"
  fi
done

echo -e "${BLUE}[FINISH]: Formatting finished${RESET}"

if [ "$fail_count" -gt 0 ]; then
  log_error "${fail_count} command(s) failed"
  exit 1
else
  log_success "All commands ran successfully"
fi