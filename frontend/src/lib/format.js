import { formatDistanceToNow, parseISO } from 'date-fns'

/**
 * "2 minutes ago", "yesterday", etc.
 * Falls back gracefully if the input is malformed.
 */
export function relativeTime(isoString) {
  try {
    return formatDistanceToNow(parseISO(isoString), { addSuffix: true })
  } catch {
    return ''
  }
}
