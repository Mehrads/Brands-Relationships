#!/bin/bash

# Setup script for Brand Analysis Pipeline

echo "========================================="
echo "Brand Analysis Pipeline Setup"
echo "========================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Create virtual environment
echo "[2/6] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "[3/6] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "[4/6] Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Download spaCy model
echo "[5/6] Downloading spaCy language model..."
python -m spacy download en_core_web_lg > /dev/null 2>&1
echo "✓ spaCy model downloaded"
echo ""

# Setup environment file
echo "[6/6] Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - Add your OpenAI or Anthropic API key"
    echo "   - Set Neo4j connection details"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and Neo4j credentials"
echo "2. Start Neo4j database (see README for instructions)"
echo "3. Initialize Neo4j: python scripts/init_neo4j.py"
echo "4. Run examples: python examples/sample_analysis.py"
echo ""
echo "For CLI usage: python main.py --help"
echo "For API usage: python api.py"
echo ""

