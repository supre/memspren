export const DETAILS_THRESHOLD = 300

export function shouldExpand(details: string): boolean {
  return details.length > DETAILS_THRESHOLD
}

export interface Update {
  id: string
  date: string
  title: string
  summary: string
  details: string
}
