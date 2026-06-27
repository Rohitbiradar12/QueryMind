import { useState, useEffect } from 'react'
import Chart from './Chart'

export default function InsightPanel({ latestResponse, isLoading, animateInsight = false }) {
  const insightText = latestResponse?.insight ?? ''

  // Typewriter reveal for the insight text. Only animates when a fresh insight
  // arrives (animateInsight=true). History/chat-switch sets it instantly.
  const [displayedInsight, setDisplayedInsight] = useState(insightText)
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    if (!animateInsight) {
      setDisplayedInsight(insightText)
      setIsTyping(false)
      return
    }

    setDisplayedInsight('')
    setIsTyping(true)
    let i = 0
    const interval = setInterval(() => {
      i += 1
      setDisplayedInsight(insightText.slice(0, i))
      if (i >= insightText.length) {
        clearInterval(interval)
        setIsTyping(false)
      }
    }, 12)

    return () => clearInterval(interval)
    // Re-run whenever the insight text changes (a new insight arrived).
  }, [insightText, animateInsight])

  if (isLoading && !latestResponse) {
    return (
      <div className="h-full flex items-center justify-center text-white/40">
        <div className="text-sm font-mono">analyzing...</div>
      </div>
    )
  }

  if (!latestResponse) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-8 text-center">
        <div className="text-sm text-white/40 mb-1">
          Insights appear here
        </div>
        <div className="text-xs text-white/30 font-mono">
          waiting for first message
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-y-auto animate-fade-in">
      {/* Insight card */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-5">
        <div className="text-[10px] uppercase tracking-wider font-mono text-white/40 mb-3">
          Insight
        </div>
        <div className="text-white/90 leading-relaxed text-[15px]">
          {displayedInsight}
          {isTyping && (
            <span className="inline-block w-[2px] h-[1em] -mb-[2px] ml-0.5 bg-white/60 animate-pulse" />
          )}
        </div>
      </div>

      {/* Chart card */}
      {latestResponse.chart_type !== 'none' && latestResponse.chart_data?.length > 0 && (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-5 flex-1 min-h-[340px]">
          <div className="text-[10px] uppercase tracking-wider font-mono text-white/40 mb-4">
            {latestResponse.chart_type === 'line' ? 'Trend' : 'Distribution'}
          </div>
          <Chart
            chartType={latestResponse.chart_type}
            chartData={latestResponse.chart_data}
          />
        </div>
      )}
    </div>
  )
}
