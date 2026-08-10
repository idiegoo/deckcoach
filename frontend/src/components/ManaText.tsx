const MANA_BG: Record<string, string> = {
  W: '#FFFDE6', U: '#AADDF8', B: '#C4B7B0', R: '#F5A89A', G: '#9ED3A0',
  C: '#D4D8E0', S: '#D4D8E0', T: '#CCC',
}

interface ManaTextProps {
  text: string
  size?: 'sm' | 'md'
}

export default function ManaText({ text, size = 'sm' }: ManaTextProps) {
  if (!text) return null

  const px = size === 'md' ? 18 : 13
  const parts = text.split(/(\{[^}]+\})/g)

  return (
    <span className="inline leading-relaxed">
      {parts.map((part, i) => {
        const match = part.match(/^\{([^}]+)\}$/)
        if (!match) return <span key={i}>{part}</span>

        const inner = match[1]
        const upper = inner.toUpperCase()
        const color = MANA_BG[upper]

        if (color) {
          return (
            <span
              key={i}
              className="inline-flex items-center justify-center rounded-full shrink-0 align-middle mx-[1px]"
              style={{
                width: px, height: px, backgroundColor: color,
                boxShadow: '0 0 0 0.5px rgba(0,0,0,0.25)',
              }}
            >
              <img
                src={`/svg/${upper === 'T' ? 'tap' : upper.toLowerCase()}.svg`}
                alt={inner}
                width={px - 3}
                height={px - 3}
                style={{ filter: 'brightness(0.2) contrast(1.3)' }}
              />
            </span>
          )
        }

        // Generic/cost numbers
        return (
          <span
            key={i}
            className="inline-flex items-center justify-center rounded-full shrink-0 align-middle mx-[1px] font-bold"
            style={{
              width: px, height: px, backgroundColor: '#D4D0CD', color: '#1A1714',
              fontSize: size === 'md' ? '10px' : '7.5px',
              boxShadow: '0 0 0 0.5px rgba(0,0,0,0.25)',
            }}
          >
            {inner}
          </span>
        )
      })}
    </span>
  )
}
