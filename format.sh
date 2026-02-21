# Define colors
YELLOW='\033[0;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
RESET='\033[0m'

# First message in yellow
echo -e "${YELLOW}-----Formatting-----${RESET}"

# Messages in red
echo -e "${RED}-----remove_blank_lines-----${RESET}"
python remove_blank_lines.py app.py
echo -e "${RED}-----autopep8-----${RESET}"
autopep8 --recursive --aggressive --in-place .
echo -e "${RED}-----isort-----${RESET}"
isort .
echo -e "${RED}-----black-----${RESET}"
black .
echo -e "${RED}-----restore pgiud-----${RESET}"
git restore pgiud.py

# Last message in green
echo -e "${GREEN}-----Done formatting-----${RESET}"