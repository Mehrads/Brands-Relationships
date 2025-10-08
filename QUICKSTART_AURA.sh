#!/bin/bash

echo "========================================="
echo "Brand Analysis Pipeline - Quick Start"
echo "Neo4j Aura Edition"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Run: cat SETUP_CREDENTIALS.md for instructions"
    exit 1
fi

# Check if API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  IMPORTANT: You need to add your OpenAI API key!"
    echo ""
    echo "1. Get your API key from: https://platform.openai.com/api-keys"
    echo "2. Edit .env file and replace 'your_openai_api_key_here' with your key"
    echo "3. Run this script again"
    echo ""
    echo "Command to edit: nano .env"
    echo ""
    exit 1
fi

echo "✓ .env file configured"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi
echo ""

# Activate virtual environment
echo "[2/4] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Check if dependencies are installed
if ! python -c "import openai" 2>/dev/null; then
    echo "[3/4] Installing dependencies (this may take a few minutes)..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    python -m spacy download en_core_web_lg > /dev/null 2>&1
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Test Neo4j Aura connection
echo "[4/4] Testing Neo4j Aura connection..."
python scripts/init_neo4j.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Setup Complete! You're ready to go!"
    echo "========================================="
    echo ""
    echo "Try these commands:"
    echo ""
    echo "1. Run example analysis:"
    echo "   python examples/sample_analysis.py"
    echo ""
    echo "2. Analyze your own text:"
    echo "   python main.py analyze --input yourfile.txt --subject-brand YourBrand"
    echo ""
    echo "3. Visualize the graph:"
    echo "   python main.py visualize"
    echo ""
    echo "4. Start the API server:"
    echo "   python api.py"
    echo ""
    echo "5. View your data in Neo4j Aura:"
    echo "   https://console.neo4j.io/"
    echo ""
else
    echo ""
    echo "========================================="
    echo "❌ Setup Failed"
    echo "========================================="
    echo ""
    echo "Possible issues:"
    echo "1. Check your OpenAI API key in .env"
    echo "2. Verify Neo4j Aura is accessible"
    echo "3. Check your internet connection"
    echo ""
fi

