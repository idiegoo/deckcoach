import { FC, useState } from 'react'

interface FlipCardImageProps {
  frontUrl: string
  backUrl?: string | null
  name: string
  className?: string
  onOpenModal?: (currentSrc: string, backSrc?: string) => void
}

const FlipCardImage: FC<FlipCardImageProps> = ({ frontUrl, backUrl, name, className = '', onOpenModal }) => {
  const [flipped, setFlipped] = useState(false)
  const canFlip = !!backUrl

  const handleClick = () => {
    if (onOpenModal) {
      const current = flipped && backUrl ? backUrl : frontUrl
      const otherSide = flipped ? frontUrl : (backUrl || undefined)
      onOpenModal(current, otherSide)
    }
  }

  const handleFlip = (e: React.MouseEvent) => {
    if (!canFlip) return
    e.stopPropagation()
    setFlipped(!flipped)
  }

  const currentSrc = flipped && backUrl ? backUrl : frontUrl

  return (
    <div className={`relative inline-block cursor-pointer group ${className}`} onClick={handleClick}>
      <div style={{ perspective: '800px' }}>
        <div
          className="relative w-full h-full"
          style={{
            transformStyle: 'preserve-3d',
            transition: 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
            transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
          }}
        >
          <img
            src={frontUrl}
            alt={name}
            className="w-full rounded-lg shadow-lg block"
            style={{ backfaceVisibility: 'hidden' }}
          />
          {backUrl && (
            <img
              src={backUrl}
              alt={`${name} (back)`}
              className="w-full rounded-lg shadow-lg block absolute inset-0"
              style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
            />
          )}
        </div>
      </div>
      {canFlip && (
        <span
          className="absolute top-1 left-1 flex items-center justify-center rounded bg-purple-500/60 text-white text-[10px] w-5 h-5 z-10 cursor-pointer hover:bg-purple-500/80 transition-colors"
          onClick={handleFlip}
          title="Carta de dos caras — click para girar"
        >
          &#8644;
        </span>
      )}
    </div>
  )
}

export default FlipCardImage
