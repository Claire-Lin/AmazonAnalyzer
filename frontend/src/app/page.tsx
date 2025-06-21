
'use client'

import { useState, useRef, useEffect } from 'react'
import { Loader2, Search, TrendingUp, Lightbulb, Play } from 'lucide-react'
import { AnalysisProgress } from '@/components/AnalysisProgress'
import { AnalysisResults } from '@/components/AnalysisResults'

interface AnalysisSession {
  sessionId: string
  status: 'started' | 'running' | 'completed' | 'failed'
  amazonUrl: string
  startedAt: string
  completedAt?: string
  result?: any // eslint-disable-line @typescript-eslint/no-explicit-any
  error?: string
}

interface AgentProgress {
  agentName: string
  status: 'working' | 'completed' | 'error'
  progress: number
  currentTask: string
  thinkingStep?: string
  errorMessage?: string
  result?: any // eslint-disable-line @typescript-eslint/no-explicit-any
  timestamp: string
}

export default function Home() {
  const [amazonUrl, setAmazonUrl] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisSession, setAnalysisSession] = useState<AnalysisSession | null>(null)
  const [agentProgress, setAgentProgress] = useState<AgentProgress[]>([])
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)
  const [, setWebsocket] = useState<WebSocket | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)

  const connectWebSocket = (sessionId: string) => {
    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setWebsocket(ws)
        wsRef.current = ws
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('WebSocket message received:', message)
          console.log('Message type:', message.type)
          console.log('Message data:', message.data)
          
          switch (message.type) {
            case 'agent_progress':
              const rawData = message.data
              // Transform snake_case fields from backend to camelCase for frontend
              const progressData = {
                agentName: rawData.agent_name || rawData.agentName,
                status: rawData.status,
                progress: rawData.progress,
                currentTask: rawData.current_task || rawData.currentTask,
                thinkingStep: rawData.thinking_step || rawData.thinkingStep,
                errorMessage: rawData.error_message || rawData.errorMessage,
                result: rawData.result,
                timestamp: rawData.timestamp || new Date().toISOString()
              }
              // Add new progress message to the history (accumulate all messages)
              setAgentProgress(prev => [...prev, progressData])
              setCurrentAgent(progressData.agentName)
              break
              
            case 'analysis_complete':
              setAnalysisSession(prev => prev ? {
                ...prev,
                status: 'completed',
                completedAt: new Date().toISOString(),
                result: message.data.result
              } : null)
              setIsAnalyzing(false)
              break
              
            case 'error':
              setError(message.data.errorMessage || 'An error occurred')
              setIsAnalyzing(false)
              break
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setWebsocket(null)
        wsRef.current = null
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection failed')
      }
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      setError('Failed to establish real-time connection')
    }
  }

  const checkAnalysisResult = async (sessionId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/analysis/${sessionId}/result`)
      if (response.ok) {
        const data = await response.json()
        if (data.status === 'completed' && data.result) {
          setAnalysisSession(prev => prev ? {
            ...prev,
            status: 'completed',
            completedAt: data.completed_at || new Date().toISOString(),
            result: data.result
          } : null)
          setIsAnalyzing(false)
          return true
        }
      }
    } catch (error) {
      console.error('Error checking analysis result:', error)
    }
    return false
  }

  const startAnalysis = async () => {
    if (!amazonUrl.trim()) {
      setError('Please enter a valid Amazon product URL')
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setAgentProgress([]) // Clear previous messages
    setCurrentAgent(null)
    setAnalysisSession(null)

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amazon_url: amazonUrl
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Analysis started:', data)
      
      setAnalysisSession({
        sessionId: data.session_id,
        status: data.status,
        amazonUrl: data.amazon_url,
        startedAt: new Date().toISOString()
      })

      // Connect WebSocket for real-time updates
      connectWebSocket(data.session_id)

      // Fallback polling mechanism in case WebSocket fails
      const pollInterval = setInterval(async () => {
        const completed = await checkAnalysisResult(data.session_id)
        if (completed) {
          clearInterval(pollInterval)
        }
      }, 3000) // Check every 3 seconds

      // Clear polling after 5 minutes to prevent infinite polling
      setTimeout(() => clearInterval(pollInterval), 300000)

    } catch (error) {
      console.error('Failed to start analysis:', error)
      setError('Failed to start analysis. Please check your connection and try again.')
      setIsAnalyzing(false)
    }
  }

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAmazonUrl(e.target.value)
    setError(null)
  }

  const isValidAmazonUrl = (url: string) => {
    return url.includes('amazon.com') || url.includes('amazon.')
  }

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🔍 Amazon Product Analyzer
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            AI-powered product analysis with multi-agent workflow. Get comprehensive market insights, 
            competitive analysis, and optimization recommendations for any Amazon product.
          </p>
        </div>

        {/* Features Overview */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="flex items-center mb-3">
              <Search className="w-6 h-6 text-blue-500 mr-2" />
              <h3 className="text-lg font-semibold">Data Collection</h3>
            </div>
            <p className="text-gray-600">
              Scrapes product details, reviews, and automatically finds competitor products
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="flex items-center mb-3">
              <TrendingUp className="w-6 h-6 text-green-500 mr-2" />
              <h3 className="text-lg font-semibold">Market Analysis</h3>
            </div>
            <p className="text-gray-600">
              Analyzes market positioning, competitive landscape, and pricing strategies
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="flex items-center mb-3">
              <Lightbulb className="w-6 h-6 text-yellow-500 mr-2" />
              <h3 className="text-lg font-semibold">Optimization</h3>
            </div>
            <p className="text-gray-600">
              Provides actionable recommendations for product optimization and growth
            </p>
          </div>
        </div>

        {/* Analysis Input */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-6 text-center">Start Your Analysis</h2>
          
          <div className="max-w-2xl mx-auto">
            <div className="flex flex-col space-y-4">
              <div>
                <label htmlFor="amazon-url" className="block text-sm font-medium text-gray-700 mb-2">
                  Amazon Product URL
                </label>
                <input
                  id="amazon-url"
                  type="url"
                  value={amazonUrl}
                  onChange={handleUrlChange}
                  placeholder="https://www.amazon.com/dp/..."
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                    error ? 'border-red-300' : 'border-gray-300'
                  }`}
                  disabled={isAnalyzing}
                />
                {amazonUrl && !isValidAmazonUrl(amazonUrl) && (
                  <p className="text-sm text-yellow-600 mt-1">
                    ⚠️ Please enter a valid Amazon product URL
                  </p>
                )}
              </div>
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}
              
              <button
                onClick={startAnalysis}
                disabled={isAnalyzing || !amazonUrl.trim() || !isValidAmazonUrl(amazonUrl)}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Analyzing Product...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    <span>Start Analysis</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Analysis Progress */}
        {(isAnalyzing || analysisSession) && (
          <AnalysisProgress
            session={analysisSession}
            agentProgress={agentProgress}
            currentAgent={currentAgent}
            isAnalyzing={isAnalyzing}
          />
        )}

        {/* Analysis Results */}
        {analysisSession?.status === 'completed' && analysisSession.result && (
          <AnalysisResults
            session={analysisSession}
            result={analysisSession.result}
          />
        )}

        {/* Example URLs */}
        <div className="bg-gray-50 rounded-lg p-6 mt-12">
          <h3 className="text-lg font-semibold mb-4">Try These Example Products:</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded p-4">
              <h4 className="font-medium text-gray-900">Tamagotchi Nano Peanuts</h4>
              <p className="text-sm text-gray-600 mb-2">Digital pet toy with silicone case</p>
              <button
                onClick={() => setAmazonUrl('https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL/?_encoding=UTF8&pd_rd_w=z2Ksk&content-id=amzn1.sym.0ee7ac10-1e05-43b4-8708-e2b0e6430ef1&pf_rd_p=0ee7ac10-1e05-43b4-8708-e2b0e6430ef1&pf_rd_r=CH7HD7239THZ01SHTZ6N&pd_rd_wg=2kLkB&pd_rd_r=9344b5f4-da0d-45b3-b124-2e19d8d944eb&ref_=pd_hp_d_btf_exports_top_sellers_unrec')}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                disabled={isAnalyzing}
              >
                Use This URL
              </button>
            </div>
            <div className="bg-white rounded p-4">
              <h4 className="font-medium text-gray-900">Harry Potter Hedwig Interactive Owl</h4>
              <p className="text-sm text-gray-600 mb-2">Interactive owl with 15+ sounds and movements</p>
              <button
                onClick={() => setAmazonUrl('https://www.amazon.com/dp/B08SWDN5FS/ref=sspa_dk_detail_0?pd_rd_i=B08SWDN5FS&pd_rd_w=7ooYl&content-id=amzn1.sym.953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_p=953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_r=QB4D7523XBB2S2P11T3F&pd_rd_wg=eG4PU&pd_rd_r=92e66331-65b5-401b-99e2-b3cb92faefd6&s=toys-and-games&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWwy&th=1')}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                disabled={isAnalyzing}
              >
                Use This URL
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
