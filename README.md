# 🔍 Amazon Product Analyzer

A comprehensive AI-powered Amazon product analysis system with multi-agent workflow, real-time visualization, and optimization recommendations.

## 🎯 Overview

This system uses a sophisticated multi-agent architecture powered by LangGraph to analyze Amazon products and provide actionable insights:

- **Data Collection Agent**: Scrapes product details and automatically finds competitors
- **Market Analysis Agent**: Analyzes market positioning and competitive landscape  
- **Optimization Agent**: Generates specific optimization recommendations
- **Real-time WebSocket Updates**: Live progress tracking during analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI        │    │  Multi-Agent    │
│   Frontend      │◄──►│   Backend        │◄──►│   Workflow      │
│                 │    │                  │    │                 │
│ • Real-time UI  │    │ • REST API       │    │ • LangGraph     │
│ • WebSocket     │    │ • WebSocket      │    │ • OpenAI GPT-4o │
│ • Tailwind CSS  │    │ • SQLAlchemy     │    │ • Playwright    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │   Database       │
                    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key (provided in project)

### Quick Start Options

#### Option 1: Local Development (Recommended for Testing)

1. **Run the test script:**
   ```bash
   cd AmazonAnalyzer
   python test-system.py
   ```

2. **Start the backend:**
   ```bash
   ./run-local.sh
   ```

3. **Access the application:**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Option 2: Docker Deployment (Full Stack)

1. **Start with development configuration:**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Or start with full production setup:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000 (if using full setup)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (Development)

#### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

4. **Start the backend:**
   ```bash
   python main.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

## 📊 Features

### 🤖 Multi-Agent Analysis Workflow

1. **Data Collection Phase**
   - Scrapes main product information (title, price, specs, reviews)
   - Automatically discovers 3-5 competitor products
   - Extracts detailed competitor data

2. **Market Analysis Phase**
   - Analyzes current product market position
   - Performs comprehensive competitive analysis
   - Identifies market opportunities and threats

3. **Optimization Phase**
   - Generates market positioning recommendations
   - Creates specific optimization strategies
   - Provides actionable implementation steps

### 💻 Frontend Features

- **Real-time Progress Tracking**: Live updates via WebSocket
- **Interactive Results Display**: Expandable analysis sections
- **Export Functionality**: Download complete analysis reports
- **Responsive Design**: Works on desktop and mobile
- **Example Products**: Pre-loaded Amazon URLs for testing

### ⚡ Backend Features

- **FastAPI REST API**: Modern, fast API with automatic documentation
- **WebSocket Support**: Real-time agent progress updates
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **Error Handling**: Robust error recovery and retry mechanisms
- **Scalable Architecture**: Containerized and production-ready

## 🛠️ API Endpoints

### Main Endpoints

- `POST /api/analyze` - Start product analysis
- `GET /api/analysis/{session_id}/status` - Check analysis status
- `GET /api/analysis/{session_id}/result` - Get complete results
- `WS /ws/{session_id}` - Real-time progress updates

### Example Usage

```bash
# Start analysis
curl -X POST "http://localhost:8000/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{"amazon_url": "https://www.amazon.com/dp/B08N5WRWNW"}'

# Check status
curl "http://localhost:8000/api/analysis/{session_id}/status"
```

## 🧪 Testing

### Example Products

Try these Amazon URLs in the application:

1. **Echo Dot (4th Gen)**
   ```
   https://www.amazon.com/dp/B08N5WRWNW
   ```

2. **AirPods Pro (2nd Generation)**
   ```
   https://www.amazon.com/dp/B0BDHWDR12
   ```

3. **Tamagotchi Nano**
   ```
   https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL
   ```

### Complete Workflow Test

1. Open the frontend at http://localhost:3000
2. Paste any Amazon product URL
3. Click "Start Analysis"
4. Watch real-time progress updates
5. Review comprehensive analysis results

## 🔧 Configuration

### Environment Variables

The system uses the following environment variables (in `.env`):

```env
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/amazon_analyzer

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Docker Configuration

- **Backend**: Python 3.11 with Playwright
- **Frontend**: Node.js 18 with Next.js
- **Database**: PostgreSQL 15
- **Cache**: Redis 7 (optional)

## 📁 Project Structure

```
AmazonAnalyzer/
├── backend/
│   ├── agents/
│   │   ├── supervisor.py          # LangGraph workflow coordinator
│   │   ├── data_collector.py      # Product data collection
│   │   ├── market_analyzer.py     # Market analysis
│   │   ├── optimization_advisor.py # Optimization recommendations
│   │   ├── tools.py               # Agent tools and utilities
│   │   └── prompts.py             # LLM prompts
│   ├── models/
│   │   ├── database.py            # SQLAlchemy models
│   │   └── analysis.py            # Pydantic models
│   ├── services/
│   │   └── websocket_manager.py   # Real-time communication
│   ├── utils/
│   │   ├── amazon_scraper.py      # Playwright scraper
│   │   └── amazon_search.py       # Product search utilities
│   ├── main.py                    # FastAPI application
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Backend container
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx           # Main application page
│   │   └── components/
│   │       ├── AnalysisProgress.tsx
│   │       └── AnalysisResults.tsx
│   ├── package.json               # Node.js dependencies
│   └── Dockerfile                 # Frontend container
├── docker-compose.yml             # Multi-service orchestration
├── .env                          # Environment variables
└── README.md                     # This file
```

## 🔍 Technical Details

### Multi-Agent Workflow (LangGraph)

The system uses LangGraph to orchestrate a sophisticated multi-agent workflow:

1. **Supervisor Agent**: Coordinates the entire workflow and manages state
2. **Specialized Agents**: Each agent has specific tools and prompts
3. **State Management**: Shared state across all agents with proper typing
4. **Error Recovery**: Automatic retry mechanisms and error handling

### Real-time Communication

- **WebSocket Manager**: Handles multiple concurrent connections
- **Progress Updates**: Granular progress tracking for each agent
- **Error Notifications**: Real-time error reporting and recovery
- **Message Persistence**: Database storage for reliability

### Data Pipeline

- **Playwright Scraping**: Robust Amazon product data extraction
- **Anti-Detection**: Rotating user agents and request patterns
- **Data Validation**: Comprehensive validation and normalization
- **Competitor Discovery**: Intelligent competitor identification

## 🚨 Important Notes

### Rate Limiting

- The system implements respectful rate limiting for Amazon scraping
- Requests are spaced to avoid overwhelming target servers
- Consider using proxy rotation for high-volume usage

### Data Privacy

- No personal data is stored permanently
- Session data is cleaned up automatically
- All scraping follows robots.txt guidelines

### Performance

- Analysis typically takes 2-5 minutes per product
- WebSocket connections handle real-time updates efficiently
- Database connections are pooled for optimal performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and demonstration purposes. Please ensure compliance with Amazon's Terms of Service when using this tool.

## 🆘 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if backend is running on port 8000
   - Verify CORS settings allow frontend domain

2. **Scraping Errors**
   - Amazon may block requests if rate limits are exceeded
   - Try different user agents or add delays

3. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL format

4. **Frontend Build Errors**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

### Getting Help

- Check the API documentation at http://localhost:8000/docs
- Review logs in Docker containers: `docker-compose logs [service_name]`
- Open issues in the project repository

---

**Built with ❤️ using LangGraph, FastAPI, Next.js, and modern AI technologies**