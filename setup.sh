#!/bin/bash

# Advanced RAG System Setup Script
echo "🚀 Setting up Advanced RAG System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 is not installed. Please install Python 3.9+ and try again."
        exit 1
    fi
}

# Check if Node.js is installed
check_node() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js $NODE_VERSION found"
    else
        print_error "Node.js is not installed. Please install Node.js 16+ and try again."
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    print_status "Checking npm installation..."
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm $NPM_VERSION found"
    else
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
}

# Setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    print_success "Python dependencies installed"
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
        print_success "Node.js dependencies installed"
    else
        print_warning "Node.js dependencies already installed"
    fi
    
    cd ..
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << EOF
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: OpenAI API (if using OpenAI embeddings)
OPENAI_API_KEY=your_openai_api_key_here
EOF
        print_success "Environment file created at backend/.env"
        print_warning "Please update the API keys in backend/.env"
    else
        print_warning "Environment file already exists"
    fi
}

# Create directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p backend/uploads
    mkdir -p backend/downloads
    mkdir -p backend/services/__pycache__
    
    print_success "Directories created"
}

# Main setup function
main() {
    echo "=========================================="
    echo "🚀 Advanced RAG System Setup"
    echo "=========================================="
    
    # Check prerequisites
    check_python
    check_node
    check_npm
    
    # Setup components
    create_directories
    setup_python_env
    setup_frontend
    create_env_file
    
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    
    echo ""
    print_status "Next steps:"
    echo "1. Update API keys in backend/.env"
    echo "2. Start Neo4j database"
    echo "3. Run: source venv/bin/activate && cd backend && python main.py"
    echo "4. Run: cd frontend && npm start"
    echo "5. Open http://localhost:3000 in your browser"
    echo ""
    print_warning "Make sure to read the README.md for detailed instructions!"
}

# Run main function
main
