#!/bin/bash

# MongoDB Local Installation Script for macOS
# This sets up a local MongoDB instance for development

echo "=========================================="
echo "  MongoDB Local Setup"
echo "=========================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "✗ Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install MongoDB
echo "📦 Installing MongoDB..."
brew tap mongodb/brew
brew install mongodb-community@7.0

echo "✓ MongoDB installed"
echo ""

# Create data directory
echo "📁 Creating data directory..."
mkdir -p ~/data/db
echo "✓ Data directory created at ~/data/db"
echo ""

# Instructions
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To start MongoDB locally:"
echo "  brew services start mongodb-community@7.0"
echo ""
echo "Or run manually:"
echo "  mongod --dbpath ~/data/db"
echo ""
echo "To stop MongoDB:"
echo "  brew services stop mongodb-community@7.0"
echo ""
echo "Default connection: mongodb://localhost:27017/"
echo ""
echo "=========================================="
