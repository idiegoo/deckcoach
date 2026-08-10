const MANA_BG: Record<string, string> = {
  W: '#FFFDE6',
  U: '#AADDF8',
  B: '#C4B7B0',
  R: '#F5A89A',
  G: '#9ED3A0',
  C: '#D4D8E0',
  S: '#D4D8E0',
}
const MANA_SVG: Record<string, string> = {
  W: '/svg/w.svg', U: '/svg/u.svg', B: '/svg/b.svg', R: '/svg/r.svg', G: '/svg/g.svg',
  C: '/svg/c.svg', S: '/svg/c.svg',
  T: '/svg/tap.svg', Q: '/svg/untap.svg',
  X: '/svg/x.svg', Y: '/svg/y.svg', Z: '/svg/z.svg',
}

interface ManaCostProps {
  cost: string | null | undefined
  size?: 'sm' | 'md'
}

export default function ManaCost({ cost, size = 'sm' }: ManaCostProps) {
  if (!cost) return null

  const sz = size === 'md' ? 22 : 15
  const innerPad = size === 'md' ? 5 : 3

  const tokens = cost.match(/\{[^}]+\}/g) || []

  return (
    <span className="inline-flex items-center gap-[1px] align-middle">
      {tokens.map((token, i) => {
        const inner = token.replace(/[{}]/g, '')
        const upper = inner.toUpperCase()
        const bg = MANA_BG[upper]
        const svg = MANA_SVG[upper] || MANA_SVG[inner] || `/svg/${inner.toLowerCase()}.svg`

        if (bg) {
          return (
            <span
              key={i}
              className="inline-flex items-center justify-center rounded-full shrink-0"
              style={{ width: sz, height: sz, backgroundColor: bg, boxShadow: '0 0 0 0.5px rgba(0,0,0,0.3)' }}
            >
              <img
                src={svg}
                alt={inner}
                width={sz - innerPad}
                height={sz - innerPad}
                style={{ filter: 'brightness(0.25) contrast(1.2)' }}
                className="inline-block"
              />
            </span>
          )
        }

        // Generic / colorless / numbers
        return (
          <span
            key={i}
            className="inline-flex items-center justify-center rounded-full shrink-0 font-bold"
            style={{
              width: sz,
              height: sz,
              backgroundColor: '#D4D0CD',
              color: '#1A1714',
              fontSize: size === 'md' ? '11px' : '8.5px',
              boxShadow: '0 0 0 0.5px rgba(0,0,0,0.3)',
            }}
          >
            {inner === 'T' ? '↻' : inner}
          </span>
        )
      })}
    </span>
  )
}
