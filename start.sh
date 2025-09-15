#!/bin/bash

# Advanced RAG System Startup Script

echo "🚀 Starting Advanced RAG System..."

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
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check if Neo4j is running
print_status "Checking Neo4j connection..."
if ! nc -z localhost 7687 2>/dev/null; then
    print_warning "Neo4j is not running on localhost:7687"
    print_status "Please start Neo4j database before continuing."
    print_status "You can download Neo4j from: https://neo4j.com/download/"
    read -p "Press Enter when Neo4j is running, or Ctrl+C to exit..."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd frontend
npm install
if [ $? -eq 0 ]; then
    print_success "Node.js dependencies installed"
else
    print_error "Failed to install Node.js dependencies"
    exit 1
fi

# Install additional Tailwind CSS plugins
npm install @tailwindcss/forms @tailwindcss/typography
cd ..

# Check for environment file
if [ ! -f "backend/.env" ] && [ ! -f ".env" ]; then
    print_warning "No .env file found. Creating example environment file..."
    cat > backend/.env << EOL
# Gemini API Configuration
GEMINI_API_KEY=AIzaSyDlFW2XcEnaF848zdj5td1xOL3mjDowkuc

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Application Configuration
DEBUG=True
LOG_LEVEL=INFO
EOL
    print_warning "Please update backend/.env with your actual Gemini API key and Neo4j credentials"
fi

# Create necessary directories
mkdir -p backend/downloads
mkdir -p backend/uploads

print_success "Setup completed successfully!"
echo ""
print_status "🎯 Starting the application..."
echo ""

# Function to handle cleanup
cleanup() {
    print_status "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start backend
print_status "Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
print_status "Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

print_success "🎉 Advanced RAG System is now running!"
echo ""
echo "📊 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 System Components:"
echo "   ✅ FastAPI Backend"
echo "   ✅ React Frontend"
echo "   ✅ Neo4j Database"
echo "   ✅ Gemini API Integration"
echo "   ✅ Sentence Transformers"
echo ""
echo "📖 Features Available:"
echo "   • PDF Processing & Text Extraction"
echo "   • Hybrid RAG (Vector + Keyword Search)"
echo "   • Step-back RAG with Parent-Child Chunking"
echo "   • Text-to-Cypher Query Generation"
echo "   • Entity Extraction & Knowledge Graphs"
echo "   • Contract Information Extraction"
echo "   • Advanced Graph RAG with Communities"
echo ""
print_status "Press Ctrl+C to stop all services"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
