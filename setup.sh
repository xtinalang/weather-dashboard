#!/bin/bash
# Weather Dashboard Setup Script

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌤️  Weather Dashboard Setup${NC}"
echo "================================"

# Check Python version
python_version=$(python --version 2>&1)
echo -e "Detected ${YELLOW}$python_version${NC}"

if [[ $python_version != *"3."* ]]; then
    echo -e "${RED}Error: Python 3 is required (detected $python_version)${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${GREEN}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python -m venv venv
fi

# Activate virtual environment
echo -e "\n${GREEN}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # macOS/Linux
    source venv/bin/activate
fi

# Install dependencies
echo -e "\n${GREEN}Installing dependencies...${NC}"
pip install -e .

# Initialize database
echo -e "\n${GREEN}Initializing database...${NC}"
python init_database.py

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "${YELLOW}To run the app:${NC}"
echo "--------------------------------"
echo -e "1. Activate the virtual environment:"
echo -e "   ${YELLOW}source venv/bin/activate${NC} (Linux/macOS)"
echo -e "   ${YELLOW}venv\\Scripts\\activate${NC} (Windows)"
echo -e "2. Run the app:"
echo -e "   ${YELLOW}python -m weather_app interactive${NC}"
echo -e "3. Or try the diagnostics:"
echo -e "   ${YELLOW}python -m weather_app diagnostics${NC}"
echo "--------------------------------"
