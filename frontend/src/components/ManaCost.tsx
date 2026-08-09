const MANA_COLORS: Record<string, { bg: string; text: string }> = {
  W: { bg: '#FEFDE8', text: '#1A1714' },
  U: { bg: '#89CFF0', text: '#FFFFFF' },
  B: { bg: '#B0ABA8', text: '#FFFFFF' },
  R: { bg: '#F0A28E', text: '#FFFFFF' },
  G: { bg: '#A3D5A0', text: '#FFFFFF' },
  S: { bg: '#E0E8F4', text: '#2C3E50' },
}

function getManaColor(token: string) {
  return MANA_COLORS[token] || { bg: '#D4D0CD', text: '#1A1714' }
}

interface ManaCostProps {
  cost: string | null | undefined
  size?: 'sm' | 'md'
}

export default function ManaCost({ cost, size = 'sm' }: ManaCostProps) {
  if (!cost) return null

  const sizeNum = size === 'md' ? 22 : 17
  const fontSize = size === 'md' ? '11px' : '9px'

  const tokens = cost.match(/\{[^}]+\}/g) || []

  return (
    <span className="inline-flex items-center gap-[2px] align-middle">
      {tokens.map((token, i) => {
        const inner = token.replace(/[{}]/g, '')
        const { bg, text } = getManaColor(inner)
        return (
          <span
            key={i}
            style={{
              width: sizeNum,
              height: sizeNum,
              backgroundColor: bg,
              color: text,
              fontSize,
              fontWeight: 700,
              borderRadius: '50%',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              lineHeight: 1,
              fontFamily: '"Beleren", "Segoe UI", system-ui, sans-serif',
            }}
            title={token}
          >
            {inner === 'T' ? '↻' : inner}
          </span>
        )
      })}
    </span>
  )
}
