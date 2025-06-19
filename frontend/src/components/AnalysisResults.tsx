'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Download, ExternalLink, Star, DollarSign, TrendingUp, Target, Lightbulb, Package } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface AnalysisSession {
  sessionId: string
  status: 'started' | 'running' | 'completed' | 'failed'
  amazonUrl: string
  startedAt: string
  completedAt?: string
  result?: any // eslint-disable-line @typescript-eslint/no-explicit-any
  error?: string
}

interface AnalysisResultsProps {
  session: AnalysisSession
  result: any // eslint-disable-line @typescript-eslint/no-explicit-any
}

export function AnalysisResults({ session, result }: AnalysisResultsProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    productData: true,
    productAnalysis: false,
    competitorAnalysis: false,
    optimizationStrategy: false
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const formatJson = (data: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
    if (typeof data === 'string') {
      try {
        return JSON.parse(data)
      } catch {
        return data
      }
    }
    return data
  }

  const renderProductData = (productData: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
    if (!productData) return null

    const parsed = formatJson(productData)
    
    return (
      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Product Information</h4>
            <div className="space-y-2 text-sm">
              {parsed.title && (
                <div>
                  <span className="font-medium text-gray-700">Title:</span>
                  <p className="text-gray-600 mt-1">{parsed.title}</p>
                </div>
              )}
              {parsed.brand && (
                <div>
                  <span className="font-medium text-gray-700">Brand:</span>
                  <span className="text-gray-600 ml-2">{parsed.brand}</span>
                </div>
              )}
              {parsed.price && (
                <div className="flex items-center">
                  <DollarSign className="w-4 h-4 text-green-500 mr-1" />
                  <span className="font-medium text-gray-700">Price:</span>
                  <span className="text-gray-600 ml-2">{parsed.currency || '$'}{parsed.price}</span>
                </div>
              )}
              {parsed.asin && (
                <div>
                  <span className="font-medium text-gray-700">ASIN:</span>
                  <span className="text-gray-600 ml-2">{parsed.asin}</span>
                </div>
              )}
            </div>
          </div>

          {parsed.color && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Variant</h4>
              <span className="inline-block px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                {parsed.color}
              </span>
            </div>
          )}
        </div>

        <div className="space-y-4">
          {parsed.description && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Description</h4>
              <div className="text-sm text-gray-600 max-h-32 overflow-y-auto bg-gray-50 p-3 rounded">
                {parsed.description}
              </div>
            </div>
          )}

          {parsed.spec && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Specifications</h4>
              <div className="text-sm text-gray-600 max-h-32 overflow-y-auto bg-gray-50 p-3 rounded">
                <pre className="whitespace-pre-wrap">{parsed.spec}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderAnalysisSection = (title: string, content: string, icon: React.ReactNode) => {
    if (!content) return null

    return (
      <div className="prose prose-sm max-w-none">
        <div className="flex items-center mb-3">
          {icon}
          <h4 className="font-medium text-gray-900 ml-2">{title}</h4>
        </div>
        <div className="text-gray-700 bg-gray-50 p-4 rounded-lg">
          <div className="markdown-content">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
              // Style headings
              h1: ({children}) => <h1 className="text-xl font-bold text-gray-900 mb-3">{children}</h1>,
              h2: ({children}) => <h2 className="text-lg font-semibold text-gray-800 mb-2 mt-4">{children}</h2>,
              h3: ({children}) => <h3 className="text-base font-medium text-gray-700 mb-2 mt-3">{children}</h3>,
              // Style lists
              ul: ({children}) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
              li: ({children}) => <li className="text-gray-700">{children}</li>,
              // Style paragraphs
              p: ({children}) => <p className="mb-3 text-gray-700 leading-relaxed">{children}</p>,
              // Style strong/bold text
              strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
              // Style code
              code: ({children}) => <code className="bg-gray-200 px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    )
  }

  const downloadReport = () => {
    const reportData = {
      sessionId: session.sessionId,
      amazonUrl: session.amazonUrl,
      analyzedAt: session.completedAt,
      result: result
    }

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `amazon-analysis-${session.sessionId.slice(0, 8)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const sections = [
    {
      key: 'productData',
      title: 'Product Data',
      icon: <Package className="w-5 h-5 text-blue-500" />,
      content: result.main_product_data,
      render: renderProductData
    },
    {
      key: 'productAnalysis',
      title: 'Product Analysis',
      icon: <TrendingUp className="w-5 h-5 text-green-500" />,
      content: result.product_analysis,
      render: (content: string) => renderAnalysisSection('Market Position Analysis', content, <TrendingUp className="w-4 h-4 text-green-500" />)
    },
    {
      key: 'competitorAnalysis',
      title: 'Competitor Analysis',
      icon: <Target className="w-5 h-5 text-orange-500" />,
      content: result.competitor_analysis,
      render: (content: string) => renderAnalysisSection('Competitive Intelligence', content, <Target className="w-4 h-4 text-orange-500" />)
    },
    {
      key: 'optimizationStrategy',
      title: 'Optimization Strategy',
      icon: <Lightbulb className="w-5 h-5 text-yellow-500" />,
      content: result.optimization_strategy,
      render: (content: string) => renderAnalysisSection('Optimization Recommendations', content, <Lightbulb className="w-4 h-4 text-yellow-500" />)
    }
  ]

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Analysis Results</h2>
          <div className="text-sm text-gray-600">
            <div>Session: {session.sessionId}</div>
            <div>Completed: {session.completedAt ? new Date(session.completedAt).toLocaleString() : 'N/A'}</div>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={downloadReport}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4 mr-2" />
            Download Report
          </button>
          <a
            href={session.amazonUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            View Product
          </a>
        </div>
      </div>

      {/* Analysis Sections */}
      <div className="space-y-6">
        {sections.map((section) => {
          if (!section.content) return null

          const isExpanded = expandedSections[section.key]

          return (
            <div key={section.key} className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleSection(section.key)}
                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  {section.icon}
                  <span className="text-lg font-medium text-gray-900 ml-3">
                    {section.title}
                  </span>
                </div>
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-500" />
                )}
              </button>

              {isExpanded && (
                <div className="border-t border-gray-200 p-6">
                  {section.render(section.content)}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Success Message */}
      <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Star className="w-5 h-5 text-green-500" />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-green-800">
              Analysis Complete!
            </p>
            <p className="text-sm text-green-700 mt-1">
              Your Amazon product analysis has been completed successfully. Use the insights above to optimize your product listing and marketing strategy.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}