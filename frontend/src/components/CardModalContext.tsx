import { createContext, useContext, useState, FC, ReactNode, useEffect, useCallback } from 'react'

interface CardModalState {
  src: string
  name: string
}

interface CardModalContextType {
  open: (src: string, name: string, backSrc?: string) => void
  close: () => void
}

const CardModalContext = createContext<CardModalContextType>({
  open: () => {},
  close: () => {},
})

export const useCardModal = () => useContext(CardModalContext)

export const CardModalProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [modal, setModal] = useState<CardModalState | null>(null)
  const [modalBack, setModalBack] = useState<string | null>(null)
  const [modalFlipped, setModalFlipped] = useState(false)

  const open = useCallback((src: string, name: string, backSrc?: string) => {
    setModal({ src, name })
    setModalBack(backSrc || null)
    setModalFlipped(false)
  }, [])
  const close = useCallback(() => setModal(null), [])

  useEffect(() => {
    if (!modal) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') close() }
    document.addEventListener('keydown', handler)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = ''
    }
  }, [modal, close])

  return (
    <CardModalContext.Provider value={{ open, close }}>
      {children}
      {modal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm"
          onClick={close}
        >
          <div onClick={e => e.stopPropagation()} style={{ maxWidth: 'min(95vw, 680px)' }}>
            <img
              src={modalFlipped && modalBack ? modalBack : modal.src}
              alt={modal.name}
              className="w-full h-auto max-h-[92vh] rounded-xl shadow-2xl object-contain"
            />
            <p className="text-center text-sm text-gray-300 mt-2">{modal.name}</p>
          </div>
          {modalBack && (
            <button
              onClick={(e) => { e.stopPropagation(); setModalFlipped(!modalFlipped); }}
              className="absolute top-4 left-4 bg-black/60 hover:bg-black/80 text-white text-lg px-3 py-2 rounded-lg transition-colors"
              title="Girar carta"
            >
              &#8644;
            </button>
          )}
          <button
            onClick={close}
            className="absolute top-4 right-4 text-gray-400 hover:text-white text-3xl leading-none transition-colors"
          >
            ✕
          </button>
        </div>
      )}
    </CardModalContext.Provider>
  )
}
