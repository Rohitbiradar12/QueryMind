import { useState, useEffect } from 'react'

export default function Message({ role, content, animate = false }) {
  const isUser = role === 'user'

  // Typewriter reveal: only when `animate` is true (a freshly arrived message).
  // Otherwise the full content is shown immediately.
  const [displayed, setDisplayed] = useState(animate ? '' : content)
  const [isTyping, setIsTyping] = useState(animate)

  useEffect(() => {
    if (!animate) {
      setDisplayed(content)
      setIsTyping(false)
      return
    }

    setDisplayed('')
    setIsTyping(true)
    let i = 0
    const interval = setInterval(() => {
      i += 1
      setDisplayed(content.slice(0, i))
      if (i >= content.length) {
        clearInterval(interval)
        setIsTyping(false)
      }
    }, 12)

    return () => clearInterval(interval)
  }, [animate, content])

  return (
    <div className={`animate-slide-up ${isUser ? 'flex justify-end' : 'flex justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-white/[0.06] text-white border border-white/[0.06]'
            : 'text-white/90'
        }`}
      >
        <div className="text-[10px] uppercase tracking-wider font-mono mb-1.5 text-white/40">
          {isUser ? 'You' : 'Assistant'}
        </div>
        <div className="whitespace-pre-wrap">
          {displayed}
          {isTyping && (
            <span className="inline-block w-[2px] h-[1em] -mb-[2px] ml-0.5 bg-white/60 animate-pulse" />
          )}
        </div>
      </div>
    </div>
  )
}
