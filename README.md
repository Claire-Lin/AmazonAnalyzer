# 🔍 Amazon Product Analyzer

A comprehensive AI-powered Amazon product analysis system with multi-agent workflow, real-time visualization, and optimization recommendations.

## 🎯 Overview

This system uses a sophisticated multi-agent architecture powered by LangGraph to analyze Amazon products and provide actionable insights:

- **Data Collection Agent**: Scrapes product details and automatically finds competitors with sequential processing
- **Market Analysis Agent**: Analyzes market positioning and competitive landscape  
- **Optimization Agent**: Generates specific optimization recommendations
- **Real-time WebSocket Updates**: Live progress tracking during analysis with robust error handling
- **Persistent Data Storage**: Redis caching + PostgreSQL database for reliability

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI        │    │  Multi-Agent    │
│   Frontend      │◄──►│   Backend        │◄──►│   Workflow      │
│                 │    │                  │    │                 │
│ • Real-time UI  │    │ • REST API       │    │ • LangGraph     │
│ • WebSocket     │    │ • WebSocket      │    │ • OpenAI GPT-4o │
│ • Error Recovery│    │ • Redis Cache    │    │ • Playwright    │
│ • JSON Handling │    │ • Session Mgmt   │    │ • Sequential    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │   + Redis Cache  │
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
   - **Sequential competitor discovery** to avoid Amazon blocking
   - **Smart rate limiting** with 2-4 second delays between requests
   - Automatically discovers 3-5 competitor products
   - Extracts detailed competitor data with **anti-bot protection**

2. **Market Analysis Phase**
   - Analyzes current product market position
   - Performs comprehensive competitive analysis
   - Identifies market opportunities and threats
   - **Database persistence** for all analysis results

3. **Optimization Phase**
   - Generates market positioning recommendations
   - Creates specific optimization strategies
   - Provides actionable implementation steps
   - **Session-based tracking** for result retrieval

### 💻 Frontend Features

- **Real-time Progress Tracking**: Live updates via WebSocket with **JSON concatenation handling**
- **Interactive Results Display**: Expandable analysis sections
- **Robust Error Handling**: Graceful recovery from network issues
- **Export Functionality**: Download complete analysis reports
- **Responsive Design**: Works on desktop and mobile
- **Updated Example Products**: Tamagotchi and Harry Potter interactive toy examples

### ⚡ Backend Features

- **FastAPI REST API**: Modern, fast API with automatic documentation
- **Redis + PostgreSQL Integration**: Fast caching with persistent storage
- **Enhanced WebSocket Support**: Message serialization to prevent JSON errors
- **Sequential Processing**: Prevents Amazon blocking with intelligent delays
- **Database Integration**: Complete session and result persistence
- **Advanced Error Handling**: Robust error recovery and retry mechanisms
- **Scalable Architecture**: Containerized and production-ready

## 🛠️ API Endpoints

### Main Endpoints

- `POST /api/analyze` - Start product analysis
- `GET /api/analysis/{session_id}/status` - Check analysis status
- `GET /api/analysis/{session_id}/result` - Get complete results
- `GET /api/analysis/{session_id}/detailed` - Get rich database data
- `GET /api/database/sessions` - List all analysis sessions
- `WS /ws/{session_id}` - Real-time progress updates

### Example Usage

```bash
# Start analysis
curl -X POST "http://localhost:8000/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{"amazon_url": "https://www.amazon.com/dp/B08N5WRWNW"}'

# Check status
curl "http://localhost:8000/api/analysis/{session_id}/status"

# Get detailed results from database
curl "http://localhost:8000/api/analysis/{session_id}/detailed"
```

## 🧪 Testing

### Example Products

Try these Amazon URLs in the application:

1. **Tamagotchi Nano Peanuts (Updated)**
   ```
   https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL/
   ```

2. **Harry Potter Hedwig Interactive Owl (New)**
   ```
   https://www.amazon.com/dp/B08SWDN5FS/ref=sspa_dk_detail_0?pd_rd_i=B08SWDN5FS&pd_rd_w=7ooYl&content-id=amzn1.sym.953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_p=953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_r=QB4D7523XBB2S2P11T3F&pd_rd_wg=eG4PU&pd_rd_r=92e66331-65b5-401b-99e2-b3cb92faefd6&s=toys-and-games&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWwy&th=1
   ```

3. **Echo Dot (Legacy)**
   ```
   https://www.amazon.com/dp/B08N5WRWNW
   ```

### Complete Workflow Test

1. Open the frontend at http://localhost:3000
2. Paste any Amazon product URL
3. Click "Start Analysis"
4. Watch real-time progress updates for all agents
5. Review comprehensive analysis results
6. Data is automatically saved to database

## 🔧 Configuration

### Environment Variables

The system uses the following environment variables (in `.env`):

```env
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/amazon_analyzer

# Redis Configuration (New)
REDIS_URL=redis://localhost:6379/0

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Docker Configuration

- **Backend**: Python 3.11 with Playwright
- **Frontend**: Node.js 18 with Next.js
- **Database**: PostgreSQL 15
- **Cache**: Redis 7 (integrated)

## 📁 Project Structure

```
AmazonAnalyzer/
├── backend/
│   ├── agents/
│   │   ├── supervisor.py          # LangGraph workflow coordinator
│   │   ├── data_collector.py      # Product data collection
│   │   ├── market_analyzer.py     # Market analysis
│   │   ├── optimization_advisor.py # Optimization recommendations
│   │   ├── tools.py               # Agent tools (sequential scraping)
│   │   ├── websocket_utils.py     # WebSocket utilities
│   │   ├── session_context.py     # Session management
│   │   └── prompts.py             # LLM prompts
│   ├── models/
│   │   ├── database.py            # SQLAlchemy models + DB manager
│   │   └── analysis.py            # Pydantic models
│   ├── services/
│   │   ├── websocket_manager.py   # Enhanced WebSocket manager
│   │   └── redis_manager.py       # Redis integration (NEW)
│   ├── utils/
│   │   ├── amazon_scraper.py      # Playwright scraper
│   │   └── amazon_search.py       # Product search utilities
│   ├── main.py                    # FastAPI application
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Backend container
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx           # Main app (enhanced error handling)
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
5. **Session Context**: Persistent session tracking across all agents

### Enhanced Real-time Communication

- **WebSocket Manager**: Handles multiple concurrent connections with message locks
- **JSON Concatenation Protection**: Prevents malformed JSON from concurrent sends
- **Progress Updates**: Granular progress tracking for each agent
- **Error Notifications**: Real-time error reporting and recovery
- **Message Persistence**: Database storage for reliability
- **Frontend JSON Recovery**: Handles concatenated messages gracefully

### Advanced Data Pipeline

- **Sequential Playwright Scraping**: Prevents Amazon blocking with intelligent delays
- **Anti-Detection**: Rotating user agents and request patterns
- **Rate Limiting**: 2-4 second delays between requests
- **Data Validation**: Comprehensive validation and normalization
- **Intelligent Competitor Discovery**: Sequential search across multiple keywords
- **Database Integration**: Full persistence with Redis caching

### New Performance Features

- **Redis Caching**: Fast session and result retrieval
- **PostgreSQL Storage**: Persistent data with rich querying
- **Sequential Processing**: `amazon_scraper_sequential()` and `amazon_search_sequential()`
- **Connection Pooling**: Optimized database connections
- **WebSocket Locks**: Prevents message concatenation issues

## 🚨 Important Notes

### Rate Limiting & Anti-Blocking

- **Sequential Processing**: All competitor scraping is done sequentially with delays
- **Smart Delays**: 2-4 second random delays between Amazon requests
- **Anti-Bot Protection**: Multiple user agents and headers
- **Respectful Scraping**: Follows rate limiting best practices
- Consider using proxy rotation for high-volume usage

### Data Privacy & Storage

- Session data stored in Redis (fast) and PostgreSQL (persistent)
- No personal data is stored permanently
- Session cleanup handled automatically
- All scraping follows robots.txt guidelines

### Performance & Reliability

- Analysis typically takes 2-5 minutes per product
- **Sequential scraping prevents blocking but increases time**
- WebSocket connections handle real-time updates efficiently
- Database connections are pooled for optimal performance
- **Enhanced error recovery** for network issues

## 🆕 Recent Updates

### Version 2.0 Features

- ✅ **Redis + PostgreSQL Integration**: Fast caching with persistent storage
- ✅ **Sequential Amazon Scraping**: Prevents blocking with `amazon_scraper_sequential()`
- ✅ **Enhanced WebSocket Manager**: Message serialization and JSON validation
- ✅ **Frontend Error Handling**: Graceful JSON concatenation recovery
- ✅ **Updated Example Products**: Tamagotchi and Harry Potter toys
- ✅ **Session Management**: Complete session tracking and persistence
- ✅ **Database APIs**: Rich data retrieval endpoints

### Bug Fixes

- 🐛 Fixed WebSocket JSON concatenation errors
- 🐛 Fixed Data Collector completion status
- 🐛 Improved Amazon blocking prevention
- 🐛 Enhanced error logging and debugging

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

1. **WebSocket JSON Errors (FIXED)**
   - ✅ Now handles concatenated JSON messages gracefully
   - ✅ Message serialization prevents concurrent send issues

2. **Amazon Blocking (IMPROVED)**
   - ✅ Sequential scraping with delays prevents most blocking
   - ✅ Use `amazon_scraper_sequential()` for multiple URLs
   - Try different user agents or increase delays if still blocked

3. **Data Collector Stuck (FIXED)**
   - ✅ Now properly sends completion notifications
   - ✅ Frontend correctly shows agent completion status

4. **Database Connection Issues**
   - Ensure PostgreSQL and Redis are running
   - Check DATABASE_URL and REDIS_URL format
   - Verify Docker containers are healthy

5. **Frontend Build Errors**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall
   - Check TypeScript errors in console

### Performance Tips

- **Use Sequential Tools**: `amazon_scraper_sequential()` for multiple URLs
- **Monitor Logs**: Check for rate limiting messages
- **Database Health**: Monitor Redis and PostgreSQL performance
- **WebSocket Status**: Watch for connection drops in browser console

### Getting Help

- Check the API documentation at http://localhost:8000/docs
- Review logs in Docker containers: `docker-compose logs [service_name]`
- Monitor Redis: `docker exec -it redis redis-cli monitor`
- Database queries: Check PostgreSQL logs for slow queries
- Open issues in the project repository

---

**Built with ❤️ using LangGraph, FastAPI, Next.js, Redis, PostgreSQL, and modern AI technologies**

*Last Updated: December 2024 - Version 2.0 with Enhanced Reliability & Performance*