#!/bin/bash

# Define colors
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

# Initialize fail count
fail_count=0

# Function to run commands quietly and log errors with color if they fail
run_command() {
  command="$1"
  name="$2"

  # Print the running message in yellow
  echo -e "${YELLOW}[INFO]: ${name}: Running...${RESET}"

  # Run command, suppressing output, check if it fails
  if $command &>/dev/null; then
    # If command runs successfully, print success message in green
    echo -e "${GREEN}[SUCCESS]: ${name}: Ran successfully${RESET}"
  else
    # If command fails, print error message in red and increment fail count
    echo -e "${RED}[ERROR]: ${name}: Failed to run${RESET}"
    ((fail_count++))
  fi
}

# First message in blue (Start)
echo -e "${BLUE}[START]: Formatting started${RESET}"

# Run the commands with quiet output and error logging
run_command "python rbl.py app.py" "rbl"
run_command "autopep8 --recursive --aggressive --in-place ." "autopep8"
run_command "isort ." "isort"
run_command "black ." "black"
run_command "git restore pgiud.py" "restore pgiud"

# Last message in blue (Finish)
echo -e "${BLUE}[FINISH]: Formatting finished${RESET}"

# Print the fail count
if [ "$fail_count" -gt 0 ]; then
  echo -e "${RED}[INFO]: ${fail_count} command(s) failed${RESET}"
else
  echo -e "${GREEN}[INFO]: All commands ran successfully${RESET}"
fi