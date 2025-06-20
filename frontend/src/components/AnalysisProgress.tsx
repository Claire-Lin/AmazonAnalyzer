'use client'

import { useEffect, useRef } from 'react'
import { Loader2, CheckCircle, AlertCircle, Clock, Bot, Search, TrendingUp, Lightbulb } from 'lucide-react'

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

interface AnalysisProgressProps {
  session: AnalysisSession | null
  agentProgress: AgentProgress[]
  currentAgent: string | null
  isAnalyzing: boolean
}

export function AnalysisProgress({ session, agentProgress, currentAgent, isAnalyzing }: AnalysisProgressProps) {
  const activityLogRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages appear
  useEffect(() => {
    if (activityLogRef.current) {
      activityLogRef.current.scrollTop = activityLogRef.current.scrollHeight
    }
  }, [agentProgress])

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case 'data_collector':
        return <Search className="w-5 h-5 text-blue-500" />
      case 'market_analyzer':
        return <TrendingUp className="w-5 h-5 text-green-500" />
      case 'optimization_advisor':
        return <Lightbulb className="w-5 h-5 text-yellow-500" />
      case 'supervisor':
        return <Bot className="w-5 h-5 text-purple-500" />
      default:
        return <Bot className="w-5 h-5 text-gray-500" />
    }
  }

  const getAgentName = (agentName: string) => {
    if (!agentName) return 'Unknown Agent'
    
    switch (agentName) {
      case 'data_collector':
        return 'Data Collector'
      case 'market_analyzer':
        return 'Market Analyzer'
      case 'optimization_advisor':
        return 'Optimization Advisor'
      case 'supervisor':
        return 'Supervisor'
      default:
        return agentName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'working':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getProgressColor = (progress: number, status: string) => {
    if (status === 'error') return 'bg-red-500'
    if (status === 'completed') return 'bg-green-500'
    return 'bg-blue-500'
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  if (!session && !isAnalyzing) return null

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Analysis Progress</h2>
        {session && (
          <div className="text-sm text-gray-500">
            Session: {session.sessionId.slice(0, 8)}...
          </div>
        )}
      </div>

      {/* Overall Progress */}
      {session && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Overall Status</span>
            <span className={`text-sm px-2 py-1 rounded ${
              session.status === 'completed' ? 'bg-green-100 text-green-800' :
              session.status === 'failed' ? 'bg-red-100 text-red-800' :
              'bg-blue-100 text-blue-800'
            }`}>
              {session.status.toUpperCase()}
            </span>
          </div>
          <div className="text-sm text-gray-600 mb-2">
            Analyzing: {session.amazonUrl}
          </div>
          <div className="text-xs text-gray-500">
            Started: {formatTimestamp(session.startedAt)}
            {session.completedAt && ` • Completed: ${formatTimestamp(session.completedAt)}`}
          </div>
        </div>
      )}

      {/* Agent Progress Timeline */}
      <div className="space-y-4">
        {agentProgress.length === 0 && isAnalyzing && (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <Loader2 className="w-6 h-6 animate-spin mr-3" />
            <span>Initializing analysis workflow...</span>
          </div>
        )}

        {/* Progress Summary by Agent */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {Array.from(new Set(agentProgress.map(p => p.agentName))).map(agentName => {
            const latestProgress = agentProgress
              .filter(p => p.agentName === agentName)
              .slice(-1)[0]
            
            if (!latestProgress) return null

            return (
              <div
                key={agentName}
                className={`border rounded-lg p-3 ${
                  currentAgent === agentName
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getAgentIcon(agentName)}
                    <span className="text-sm font-medium">{getAgentName(agentName)}</span>
                  </div>
                  {getStatusIcon(latestProgress.status)}
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-300 ${getProgressColor(latestProgress.progress, latestProgress.status)}`}
                    style={{ width: `${latestProgress.progress * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>

        {/* Message Timeline */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Activity Log</h3>
          <div 
            ref={activityLogRef}
            className="space-y-2 max-h-96 overflow-y-auto scroll-smooth"
          >
            {agentProgress.map((message, index) => (
              <div
                key={`${message.agentName}-${index}-${message.timestamp}`}
                className={`flex items-start space-x-3 p-2 rounded ${
                  currentAgent === message.agentName ? 'bg-white' : ''
                }`}
              >
                {/* Timestamp */}
                <div className="flex-shrink-0 text-xs text-gray-500 w-16">
                  {formatTimestamp(message.timestamp)}
                </div>

                {/* Agent Icon */}
                <div className="flex-shrink-0">
                  {getAgentIcon(message.agentName)}
                </div>

                {/* Message Content */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm">
                    <span className="font-medium text-gray-700">
                      {getAgentName(message.agentName)}
                    </span>
                    {message.status === 'error' && (
                      <span className="ml-2 text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded">
                        ERROR
                      </span>
                    )}
                    {message.status === 'completed' && (
                      <span className="ml-2 text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded">
                        COMPLETED
                      </span>
                    )}
                  </div>
                  
                  {/* Current Task */}
                  {message.currentTask && (
                    <p className="text-sm text-gray-700 mt-1">
                      {message.currentTask}
                    </p>
                  )}
                  
                  {/* Thinking Step */}
                  {message.thinkingStep && (
                    <p className="text-sm text-gray-600 italic mt-1">
                      💭 {message.thinkingStep}
                    </p>
                  )}
                  
                  {/* Error Message */}
                  {message.errorMessage && (
                    <p className="text-sm text-red-600 mt-1">
                      ❌ {message.errorMessage}
                    </p>
                  )}
                  
                  {/* Result Preview */}
                  {message.result && message.status === 'completed' && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                        View result preview
                      </summary>
                      <div className="mt-1 p-2 bg-gray-100 rounded text-xs text-gray-700">
                        {typeof message.result === 'string' 
                          ? message.result.slice(0, 200) + (message.result.length > 200 ? '...' : '')
                          : JSON.stringify(message.result).slice(0, 200) + '...'
                        }
                      </div>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Updates Indicator */}
      {isAnalyzing && (
        <div className="mt-6 flex items-center justify-center text-sm text-gray-500">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>Real-time updates via WebSocket</span>
          </div>
        </div>
      )}
    </div>
  )
}