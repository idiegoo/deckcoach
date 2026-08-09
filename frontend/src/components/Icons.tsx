// DeckCoach logo icon — the only SVG icon we keep (rest are emoji)
export function IconWizard({ size = 28, className = '' }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8L19 13M5 5l2 2M12 12l-7 7M12 12l7-7" />
      <circle cx="12" cy="9" r="5" fill="currentColor" fillOpacity="0.15" />
    </svg>
  )
}
