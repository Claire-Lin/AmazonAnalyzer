# 📡 API Documentation
## 主要 Endpoint 說明

### 🎯 API 概述 (API Overview)

Amazon Product Analyzer 提供一套完整的 RESTful API 與 WebSocket 接口，支援產品分析的完整生命週期管理。API 基於 FastAPI 框架構建，提供自動生成的 OpenAPI 文檔。

**API 基礎信息：**
- **Base URL**: `http://localhost:8000`
- **API 版本**: v1
- **文檔地址**: `http://localhost:8000/docs` (Swagger UI)
- **替代文檔**: `http://localhost:8000/redoc` (ReDoc)

---

## 🔐 認證與授權 (Authentication & Authorization)

目前系統採用無認證設計，適合內部使用或 Demo 環境。生產環境建議添加：

```python
# 未來擴展：JWT Token 認證
headers = {
    "Authorization": "Bearer <your-jwt-token>",
    "Content-Type": "application/json"
}
```

---

## 📋 核心 API 端點 (Core API Endpoints)

### 1. 分析管理 API (Analysis Management)

#### 🚀 啟動產品分析
```http
POST /api/analyze
```

**描述**: 啟動新的產品分析工作流程

**請求體 (Request Body)**:
```json
{
    "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW"
}
```

**請求參數 (Parameters)**:
| 參數 | 類型 | 必填 | 描述 |
|------|------|------|------|
| `amazon_url` | string | ✅ | Amazon 產品頁面完整 URL |

**成功響應 (200 OK)**:
```json
{
    "session_id": "uuid-string",
    "status": "started",
    "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
    "created_at": "2024-12-20T10:30:00Z",
    "message": "Analysis started successfully"
}
```

**錯誤響應 (400 Bad Request)**:
```json
{
    "detail": "Invalid Amazon URL format"
}
```

**使用範例 (curl)**:
```bash
curl -X POST "http://localhost:8000/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{"amazon_url": "https://www.amazon.com/dp/B08N5WRWNW"}'
```

**使用範例 (Python)**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/analyze",
    json={"amazon_url": "https://www.amazon.com/dp/B08N5WRWNW"}
)
data = response.json()
session_id = data["session_id"]
```

---

#### 📊 查詢分析狀態
```http
GET /api/analysis/{session_id}/status
```

**描述**: 查詢指定會話的分析進度和狀態

**路徑參數 (Path Parameters)**:
| 參數 | 類型 | 描述 |
|------|------|------|
| `session_id` | string | 分析會話的唯一識別碼 |

**成功響應 (200 OK)**:
```json
{
    "session_id": "uuid-string",
    "status": "running",  // started, running, completed, failed
    "progress": 0.65,     // 0.0 - 1.0
    "current_phase": "market_analysis",
    "started_at": "2024-12-20T10:30:00Z",
    "estimated_completion": "2024-12-20T10:35:00Z",
    "agents_status": {
        "data_collector": "completed",
        "market_analyzer": "running",
        "optimization_advisor": "pending"
    }
}
```

**使用範例**:
```bash
curl "http://localhost:8000/api/analysis/uuid-string/status"
```

---

#### 📈 獲取分析結果
```http
GET /api/analysis/{session_id}/result
```

**描述**: 獲取完整的分析結果（僅在分析完成後可用）

**成功響應 (200 OK)**:
```json
{
    "session_id": "uuid-string",
    "status": "completed",
    "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
    "started_at": "2024-12-20T10:30:00Z",
    "completed_at": "2024-12-20T10:34:30Z",
    "result": {
        "data_collection": {
            "main_product": {
                "title": "Echo Dot (4th Gen)",
                "price": 49.99,
                "brand": "Amazon",
                "asin": "B08N5WRWNW",
                "description": "...",
                "specifications": {...},
                "reviews_summary": {...}
            },
            "competitors": [
                {
                    "title": "Google Nest Mini",
                    "price": 49.99,
                    "brand": "Google",
                    "asin": "B07YXJ4KNF"
                }
            ]
        },
        "market_analysis": {
            "product_analysis": "詳細產品分析內容...",
            "competitor_analysis": "競爭對手分析內容...",
            "market_positioning": "市場定位建議..."
        },
        "optimization": {
            "positioning_strategy": "定位策略建議...",
            "optimization_recommendations": "優化建議..."
        }
    }
}
```

---

#### 🔍 獲取詳細數據庫資料
```http
GET /api/analysis/{session_id}/detailed
```

**描述**: 從數據庫獲取完整的結構化分析數據

**成功響應 (200 OK)**:
```json
{
    "session": {
        "id": 123,
        "session_id": "uuid-string",
        "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
        "status": "completed",
        "created_at": "2024-12-20T10:30:00Z",
        "completed_at": "2024-12-20T10:34:30Z"
    },
    "products": [
        {
            "id": 456,
            "asin": "B08N5WRWNW",
            "title": "Echo Dot (4th Gen)",
            "price": 49.99,
            "brand": "Amazon",
            "is_main": true,
            "specifications": {...},
            "reviews": [...]
        }
    ],
    "analysis_results": {
        "product_analysis": "...",
        "competitor_analysis": "...",
        "market_positioning": "...",
        "optimization_strategy": "..."
    },
    "agent_progress": [
        {
            "agent_name": "data_collector",
            "status": "completed",
            "progress": 1.0,
            "timestamp": "2024-12-20T10:32:00Z"
        }
    ]
}
```

---

### 2. 數據庫管理 API (Database Management)

#### 📋 獲取所有分析會話
```http
GET /api/database/sessions
```

**描述**: 獲取所有歷史分析會話列表

**查詢參數 (Query Parameters)**:
| 參數 | 類型 | 預設值 | 描述 |
|------|------|--------|------|
| `limit` | integer | 50 | 返回結果數量限制 |
| `offset` | integer | 0 | 分頁偏移量 |
| `status` | string | all | 過濾狀態 (all, completed, failed, running) |

**成功響應 (200 OK)**:
```json
{
    "total": 156,
    "limit": 50,
    "offset": 0,
    "sessions": [
        {
            "id": 123,
            "session_id": "uuid-string-1",
            "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW",
            "status": "completed",
            "created_at": "2024-12-20T10:30:00Z",
            "completed_at": "2024-12-20T10:34:30Z",
            "product_count": 4
        },
        {
            "id": 122,
            "session_id": "uuid-string-2",
            "amazon_url": "https://www.amazon.com/dp/B0BDHWDR12",
            "status": "failed",
            "created_at": "2024-12-20T09:15:00Z",
            "error_message": "Amazon blocking detected"
        }
    ]
}
```

**使用範例**:
```bash
# 獲取最近 10 個已完成的分析
curl "http://localhost:8000/api/database/sessions?limit=10&status=completed"
```

---

### 3. 系統狀態 API (System Status)

#### 🏥 健康檢查
```http
GET /health
```

**描述**: 系統健康狀態檢查

**成功響應 (200 OK)**:
```json
{
    "status": "healthy",
    "timestamp": "2024-12-20T10:30:00Z",
    "version": "2.0.0",
    "services": {
        "database": "connected",
        "redis": "connected",
        "openai": "available",
        "playwright": "ready"
    },
    "active_sessions": 3,
    "system_load": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 23.1
    }
}
```

#### 📊 系統統計
```http
GET /api/stats
```

**描述**: 系統使用統計信息

**成功響應 (200 OK)**:
```json
{
    "total_analyses": 1543,
    "completed_analyses": 1421,
    "failed_analyses": 122,
    "success_rate": 92.1,
    "average_duration": 180.5,
    "today_analyses": 87,
    "active_sessions": 3,
    "database_size": "2.3 GB",
    "cache_hit_rate": 89.4
}
```

---

## 🔌 WebSocket API

### 實時進度更新
```
WS /ws/{session_id}
```

**描述**: 建立 WebSocket 連接以接收實時分析進度更新

**連接範例 (JavaScript)**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${session_id}`);

ws.onopen = (event) => {
    console.log('WebSocket 連接已建立');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
    
    switch (message.type) {
        case 'agent_progress':
            updateProgress(message.data);
            break;
        case 'analysis_complete':
            showResults(message.data);
            break;
        case 'error':
            handleError(message.data);
            break;
    }
};
```

### WebSocket 消息格式

#### 智能體進度更新
```json
{
    "type": "agent_progress",
    "session_id": "uuid-string",
    "timestamp": "2024-12-20T10:32:15Z",
    "data": {
        "agent_name": "data_collector",
        "status": "working",        // working, completed, error
        "progress": 0.65,           // 0.0 - 1.0
        "current_task": "爬取競爭對手資料",
        "thinking_step": "正在搜尋相似產品...",
        "error_message": null,
        "result": null
    }
}
```

#### 分析完成通知
```json
{
    "type": "analysis_complete",
    "session_id": "uuid-string",
    "timestamp": "2024-12-20T10:34:30Z",
    "data": {
        "success": true,
        "result": {
            "summary": "分析已成功完成",
            "total_duration": 270.5,
            "products_analyzed": 4
        }
    }
}
```

#### 錯誤通知
```json
{
    "type": "error",
    "session_id": "uuid-string",
    "timestamp": "2024-12-20T10:33:45Z",
    "data": {
        "error_type": "scraping_blocked",
        "error_message": "Amazon 檢測到自動化請求",
        "agent_name": "data_collector",
        "retry_after": 300
    }
}
```

---

## 🛠️ 錯誤處理 (Error Handling)

### HTTP 狀態碼

| 狀態碼 | 描述 | 處理建議 |
|--------|------|----------|
| `200` | 請求成功 | 正常處理響應數據 |
| `201` | 資源創建成功 | 新分析會話已創建 |
| `400` | 請求參數錯誤 | 檢查請求格式和參數 |
| `404` | 資源不存在 | 檢查 session_id 是否正確 |
| `422` | 參數驗證失敗 | 檢查必填字段和數據格式 |
| `429` | 請求頻率限制 | 等待後重試 |
| `500` | 服務器內部錯誤 | 聯繫系統管理員 |

### 錯誤響應格式

#### 標準錯誤響應
```json
{
    "detail": "錯誤描述信息",
    "error_code": "INVALID_URL",
    "timestamp": "2024-12-20T10:30:00Z",
    "path": "/api/analyze",
    "session_id": "uuid-string"
}
```

#### 驗證錯誤響應
```json
{
    "detail": [
        {
            "loc": ["body", "amazon_url"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

### 常見錯誤代碼

| 錯誤代碼 | 描述 | 解決方案 |
|----------|------|----------|
| `INVALID_URL` | Amazon URL 格式無效 | 提供正確的 Amazon 產品 URL |
| `SESSION_NOT_FOUND` | 會話不存在 | 檢查 session_id 是否正確 |
| `ANALYSIS_IN_PROGRESS` | 分析正在進行中 | 等待當前分析完成 |
| `SCRAPING_BLOCKED` | 爬蟲被阻擋 | 等待一段時間後重試 |
| `RATE_LIMIT_EXCEEDED` | 超過請求頻率限制 | 降低請求頻率 |
| `SERVICE_UNAVAILABLE` | 服務暫時不可用 | 稍後重試 |

---

## 📝 使用範例 (Usage Examples)

### 完整分析流程範例

#### Python 客戶端
```python
import requests
import websocket
import json
import time

class AmazonAnalyzerClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def start_analysis(self, amazon_url):
        """啟動分析"""
        response = requests.post(
            f"{self.base_url}/api/analyze",
            json={"amazon_url": amazon_url}
        )
        return response.json()
    
    def get_status(self, session_id):
        """查詢狀態"""
        response = requests.get(
            f"{self.base_url}/api/analysis/{session_id}/status"
        )
        return response.json()
    
    def get_result(self, session_id):
        """獲取結果"""
        response = requests.get(
            f"{self.base_url}/api/analysis/{session_id}/result"
        )
        return response.json()
    
    def listen_progress(self, session_id, callback):
        """監聽進度更新"""
        ws_url = f"ws://localhost:8000/ws/{session_id}"
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=lambda ws, msg: callback(json.loads(msg)),
            on_error=lambda ws, error: print(f"WebSocket 錯誤: {error}")
        )
        ws.run_forever()

# 使用範例
client = AmazonAnalyzerClient()

# 1. 啟動分析
result = client.start_analysis("https://www.amazon.com/dp/B08N5WRWNW")
session_id = result["session_id"]
print(f"分析已啟動，會話ID: {session_id}")

# 2. 監聽進度
def progress_callback(message):
    if message["type"] == "agent_progress":
        data = message["data"]
        print(f"{data['agent_name']}: {data['current_task']} ({data['progress']*100:.1f}%)")
    elif message["type"] == "analysis_complete":
        print("分析完成！")

# 在後台線程中監聽進度
import threading
progress_thread = threading.Thread(
    target=client.listen_progress,
    args=(session_id, progress_callback)
)
progress_thread.daemon = True
progress_thread.start()

# 3. 等待完成
while True:
    status = client.get_status(session_id)
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print("分析失敗")
        break
    time.sleep(5)

# 4. 獲取結果
final_result = client.get_result(session_id)
print("分析結果:", final_result["result"])
```

#### JavaScript 客戶端
```javascript
class AmazonAnalyzerClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async startAnalysis(amazonUrl) {
        const response = await fetch(`${this.baseUrl}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amazon_url: amazonUrl })
        });
        return await response.json();
    }
    
    async getStatus(sessionId) {
        const response = await fetch(`${this.baseUrl}/api/analysis/${sessionId}/status`);
        return await response.json();
    }
    
    async getResult(sessionId) {
        const response = await fetch(`${this.baseUrl}/api/analysis/${sessionId}/result`);
        return await response.json();
    }
    
    listenProgress(sessionId, callback) {
        const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            callback(message);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket 錯誤:', error);
        };
        
        return ws;
    }
}

// 使用範例
const client = new AmazonAnalyzerClient();

async function analyzeProduct(amazonUrl) {
    try {
        // 1. 啟動分析
        const result = await client.startAnalysis(amazonUrl);
        const sessionId = result.session_id;
        console.log(`分析已啟動，會話ID: ${sessionId}`);
        
        // 2. 監聽進度
        const ws = client.listenProgress(sessionId, (message) => {
            if (message.type === 'agent_progress') {
                const data = message.data;
                console.log(`${data.agent_name}: ${data.current_task} (${(data.progress * 100).toFixed(1)}%)`);
            } else if (message.type === 'analysis_complete') {
                console.log('分析完成！');
                ws.close();
            }
        });
        
        // 3. 等待完成並獲取結果
        while (true) {
            const status = await client.getStatus(sessionId);
            if (status.status === 'completed') {
                const finalResult = await client.getResult(sessionId);
                console.log('分析結果:', finalResult.result);
                break;
            } else if (status.status === 'failed') {
                console.log('分析失敗');
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
        
    } catch (error) {
        console.error('分析過程發生錯誤:', error);
    }
}

// 執行分析
analyzeProduct('https://www.amazon.com/dp/B08N5WRWNW');
```

---

## 🚀 最佳實踐 (Best Practices)

### 1. API 使用建議

#### 請求頻率控制
```python
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    """API 請求頻率限制裝飾器"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 60.0 / calls_per_minute - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(calls_per_minute=30)
def api_call():
    # 控制 API 調用頻率
    pass
```

#### 錯誤重試機制
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    """創建帶重試機制的 HTTP 會話"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,                    # 總重試次數
        backoff_factor=1,           # 重試間隔倍數
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重試的狀態碼
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

### 2. WebSocket 連接管理

#### 自動重連機制
```javascript
class ReconnectingWebSocket {
    constructor(url, protocols = []) {
        this.url = url;
        this.protocols = protocols;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.reconnectDecay = 1.5;
        this.connect();
    }
    
    connect() {
        this.ws = new WebSocket(this.url, this.protocols);
        
        this.ws.onopen = (event) => {
            console.log('WebSocket 連接已建立');
            this.reconnectDelay = 1000; // 重置重連延遲
            if (this.onopen) this.onopen(event);
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket 連接已關閉，嘗試重連...');
            setTimeout(() => {
                this.reconnectDelay = Math.min(
                    this.maxReconnectDelay,
                    this.reconnectDelay * this.reconnectDecay
                );
                this.connect();
            }, this.reconnectDelay);
        };
        
        this.ws.onmessage = (event) => {
            if (this.onmessage) this.onmessage(event);
        };
        
        this.ws.onerror = (event) => {
            console.error('WebSocket 錯誤:', event);
            if (this.onerror) this.onerror(event);
        };
    }
    
    send(data) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            console.warn('WebSocket 未連接，無法發送數據');
        }
    }
    
    close() {
        this.ws.close();
    }
}
```

### 3. 性能優化

#### 批量查詢優化
```python
def get_multiple_sessions_status(session_ids, batch_size=10):
    """批量查詢多個會話狀態"""
    results = {}
    
    for i in range(0, len(session_ids), batch_size):
        batch = session_ids[i:i + batch_size]
        
        # 並發查詢
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {
                executor.submit(get_session_status, sid): sid 
                for sid in batch
            }
            
            for future in as_completed(futures):
                session_id = futures[future]
                try:
                    results[session_id] = future.result()
                except Exception as e:
                    results[session_id] = {"error": str(e)}
    
    return results
```

#### 緩存策略
```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    """結果緩存裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成緩存鍵
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 嘗試從緩存獲取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 執行函數並緩存結果
            result = func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                expiration, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

@cache_result(expiration=600)  # 緩存 10 分鐘
def get_analysis_result(session_id):
    # 獲取分析結果
    pass
```

---

## 📊 API 性能指標 (Performance Metrics)

### 響應時間基準

| API 端點 | 平均響應時間 | 95% 響應時間 | 99% 響應時間 |
|----------|--------------|--------------|--------------|
| `POST /api/analyze` | 150ms | 300ms | 500ms |
| `GET /api/analysis/{id}/status` | 50ms | 100ms | 200ms |
| `GET /api/analysis/{id}/result` | 200ms | 400ms | 800ms |
| `GET /api/database/sessions` | 100ms | 250ms | 500ms |
| `GET /health` | 20ms | 50ms | 100ms |

### 併發處理能力

- **最大併發連接數**: 1000
- **WebSocket 連接數**: 500
- **每秒請求數 (RPS)**: 100
- **數據庫連接池**: 20

---

## 🔧 故障排除 (Troubleshooting)

### 常見問題解決

#### 1. 分析卡住不動
```bash
# 檢查會話狀態
curl "http://localhost:8000/api/analysis/{session_id}/status"

# 如果狀態異常，可以查看系統日誌
docker-compose logs backend

# 檢查資源使用情況
curl "http://localhost:8000/health"
```

#### 2. WebSocket 連接失敗
```javascript
// 檢查連接狀態
ws.readyState === WebSocket.CONNECTING  // 0: 正在連接
ws.readyState === WebSocket.OPEN        // 1: 已連接
ws.readyState === WebSocket.CLOSING     // 2: 正在關閉
ws.readyState === WebSocket.CLOSED      // 3: 已關閉

// 連接失敗處理
ws.onerror = (error) => {
    console.error('WebSocket 連接失敗:', error);
    // 檢查服務器是否正常運行
    fetch('http://localhost:8000/health')
        .then(response => response.json())
        .then(data => console.log('服務器狀態:', data))
        .catch(err => console.error('服務器無響應:', err));
};
```

#### 3. 分析結果不完整
```python
# 檢查詳細數據庫數據
response = requests.get(f"http://localhost:8000/api/analysis/{session_id}/detailed")
detailed_data = response.json()

# 檢查各個智能體的執行狀態
for progress in detailed_data.get("agent_progress", []):
    print(f"{progress['agent_name']}: {progress['status']}")
    if progress['status'] == 'error':
        print(f"錯誤: {progress.get('error_message', 'Unknown error')}")
```

---

## 🔄 API 版本管理 (API Versioning)

### 當前版本
- **API 版本**: v1
- **最後更新**: 2024-12-20
- **兼容性**: 向後兼容

### 未來版本規劃
- **v1.1**: 添加批量分析功能
- **v1.2**: 增加歷史數據比較 API
- **v2.0**: GraphQL 支持，微服務架構

### 版本變更通知
系統會在響應頭中包含版本信息：
```http
X-API-Version: 1.0.0
X-API-Deprecated: false
X-API-Sunset: null
```

---

*本文檔持續更新，如有疑問請參考 [Swagger UI](http://localhost:8000/docs)*
*最後更新：2024年12月*