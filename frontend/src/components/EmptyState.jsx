const SUGGESTIONS = [
  'Tell me the summary of my last benchmark',
  'Compare runs R007 and R008',
  'Which run had the worst tail latency?',
  'Is performance improving over the last 5 runs?',
]

export default function EmptyState({ onSuggestion, disabled }) {
  return (
    <div className="h-full flex items-center justify-center px-8">
      <div className="max-w-md text-center animate-fade-in">
        <div className="text-2xl font-medium tracking-tight mb-2">
          Ask anything about your benchmarks
        </div>
        <div className="text-sm text-white/50 mb-8">
          QueryMind analyzes performance data and surfaces insights you'd otherwise hunt for in tables.
        </div>

        <div className="space-y-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => onSuggestion(s)}
              disabled={disabled}
              className="w-full text-left px-4 py-3 text-sm rounded-md bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.06] hover:border-white/[0.12] text-white/80 hover:text-white transition-all disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
