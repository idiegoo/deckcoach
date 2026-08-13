import { FC, useState, Dispatch, SetStateAction } from 'react'
import ManaText from './ManaText'
import FlipCardImage from './FlipCardImage'
import { useCardModal } from './CardModalContext'

interface ComboInfo {
  combo_id: string
  description: string
  how_to?: string
  edhrec_link?: string
  produces: string[]
  cards_in_deck: string[]
  missing_pieces: string[]
  is_complete: boolean
  mana_needed: string
  bracket: string
  prerequisites: string
  card_images?: Record<string, string>
  card_images_back?: Record<string, string>
}

interface ComboPanelProps {
  combos: ComboInfo[]
}

const ComboPanel: FC<ComboPanelProps> = ({ combos }) => {
  const [expanded, setExpanded] = useState<string | null>(null)
  const { open: openModal } = useCardModal()
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(5)
  const [activeBrackets, setActiveBrackets] = useState<Set<string>>(new Set())
  const [activeProduces, setActiveProduces] = useState<Set<string>>(new Set())
  const [showProduces, setShowProduces] = useState(true)

  if (!combos || combos.length === 0) {
    return (
      <div className="glass p-4 rounded-xl text-center text-gray-400 text-sm">
        No se encontraron combos conocidos para tu comandante. (Datos de EDHREC)
      </div>
    )
  }

  const hasDesc = (c: ComboInfo) => c.description && c.description.length > 60 && c.produces?.length > 0

  // Collect unique bracket tags from combos, ordered 1 → 2 → 2-3 → 3 → 3-4 → 4 → banned → sin bracket
  const BRACKET_ORDER = ['E', 'C', 'O', 'P', 'S', 'R', 'B', '']
  const availableBrackets = [...new Set(combos.map(c => c.bracket || ''))].sort((a, b) => {
    const ia = BRACKET_ORDER.indexOf(a)
    const ib = BRACKET_ORDER.indexOf(b)
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
  })

  // Collect unique produces from combos that match the active bracket filter
  const bracketFilteredCombos = activeBrackets.size === 0
    ? combos
    : combos.filter(c => activeBrackets.has(c.bracket || ''))
  const availableProduces = [...new Set(bracketFilteredCombos.flatMap(c => c.produces || []))].sort()

  const isFiltering = activeBrackets.size > 0 || activeProduces.size > 0
  const matchesFilter = (c: ComboInfo) => {
    const bracketOk = activeBrackets.size === 0 || activeBrackets.has(c.bracket || '')
    const producesOk = activeProduces.size === 0 || (c.produces || []).some(p => activeProduces.has(p))
    return bracketOk && producesOk
  }

  const toggleFilter = (setter: Dispatch<SetStateAction<Set<string>>>, value: string) => {
    setter(prev => {
      const next = new Set(prev)
      if (next.has(value)) next.delete(value)
      else next.add(value)
      return next
    })
    setPage(0)
  }

  const clearFilters = () => {
    setActiveBrackets(new Set())
    setActiveProduces(new Set())
    setPage(0)
  }

  const complete = combos.filter(c => c.is_complete && matchesFilter(c)).sort((a, b) => (hasDesc(b) ? 1 : 0) - (hasDesc(a) ? 1 : 0))
  const incomplete = combos.filter(c => !c.is_complete && matchesFilter(c)).sort((a, b) => (hasDesc(b) ? 1 : 0) - (hasDesc(a) ? 1 : 0))

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-red-400 text-lg">&#9889;</span>
        <h3 className="text-lg font-bold text-white">Combos detectados</h3>
        <span className="text-xs text-gray-500">(EDHREC + Commander Spellbook)</span>
      </div>

      {/* Bracket filters */}
      {availableBrackets.length > 0 && (
        <div className="glass rounded-xl p-3">
          <div className="flex items-center gap-2 flex-wrap min-w-0 mb-2">
            <span className="text-xs text-gray-400">Filtrar por bracket:</span>
            {activeBrackets.size > 0 ? (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-600 text-white font-semibold">
                {activeBrackets.size} activos
              </span>
            ) : (
              <span className="text-[11px] text-gray-600">({availableBrackets.length})</span>
            )}
            {activeBrackets.size > 0 && (
              <span
                onClick={() => { setActiveBrackets(new Set()); setPage(0) }}
                className="text-[10px] px-1.5 py-0.5 rounded-full border border-gray-600 text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors cursor-pointer"
                title="Quitar filtros de bracket"
              >
                ✕ Quitar
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {availableBrackets.map(b => {
              const info = BRACKET_MAP[b]
              const isActive = activeBrackets.has(b)
              const label = b === '' ? 'Sin bracket' : (info?.label || b)
              return (
                <button
                  key={b}
                  onClick={() => toggleFilter(setActiveBrackets, b)}
                  className={`text-[11px] px-2 py-0.5 rounded-full border transition-all ${
                    isActive
                      ? 'bg-indigo-600 border-indigo-500 text-white font-semibold'
                      : info
                        ? `${info.cls} hover:opacity-80`
                        : 'bg-gray-800/60 text-gray-400 border-gray-700/40 hover:bg-gray-800'
                  }`}
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Produces filters — collapsible accordion */}
      {availableProduces.length > 0 && (
        <div className="glass rounded-xl">
          <button
            onClick={() => setShowProduces(!showProduces)}
            className="w-full p-3 flex items-center justify-between gap-2 hover:bg-white/5 transition-colors rounded-xl"
          >
            <div className="flex items-center gap-2 flex-wrap min-w-0">
              <span className="text-xs text-gray-400">Combo tags:</span>
              {activeProduces.size > 0 ? (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-purple-600 text-white font-semibold">
                  {activeProduces.size} activos
                </span>
              ) : (
                <span className="text-[11px] text-gray-600">({availableProduces.length})</span>
              )}
              {activeProduces.size > 0 && (
                <span
                  onClick={(e) => { e.stopPropagation(); setActiveProduces(new Set()); setPage(0) }}
                  className="text-[10px] px-1.5 py-0.5 rounded-full border border-gray-600 text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors cursor-pointer"
                  title="Quitar filtros de combo tags"
                >
                  ✕ Quitar
                </span>
              )}
            </div>
            <span className={`text-sm text-gray-500 transition-transform shrink-0 ${showProduces ? 'rotate-180' : ''}`}>
              &#9660;
            </span>
          </button>
          <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
            showProduces ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
          }`}>
            <div className="px-3 pb-3 flex flex-wrap items-center gap-1.5">
              {availableProduces.map(p => {
                const isActive = activeProduces.has(p)
                return (
                  <button
                    key={p}
                    onClick={() => toggleFilter(setActiveProduces, p)}
                    className={`text-[11px] px-2 py-0.5 rounded-full border transition-all ${
                      isActive
                        ? 'bg-purple-600 border-purple-500 text-white font-semibold'
                        : 'bg-purple-500/15 text-purple-300 border-purple-500/20 hover:bg-purple-500/25'
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Clear filters row */}
      {isFiltering && (
        <div className="flex items-center gap-1.5">
          <button
            onClick={clearFilters}
            className="text-[11px] px-2 py-0.5 rounded-full border border-gray-600 text-gray-300 hover:bg-gray-800 transition-colors"
          >
            ✕ Quitar filtros
          </button>
          <button
            onClick={clearFilters}
            className="text-[11px] px-2 py-0.5 rounded-full border border-indigo-500/50 text-indigo-400 hover:bg-indigo-900/30 transition-colors"
          >
            Ver todos ({combos.length})
          </button>
        </div>
      )}

      {complete.length > 0 && (
        <div className="mb-3">
          <h4 className="text-sm font-semibold text-green-400 mb-2">
            &#9989; Combos completos ({complete.length})
          </h4>
          {complete.map(combo => (
            <ComboCard key={combo.combo_id} combo={combo} expanded={expanded} onToggle={setExpanded} />
          ))}
        </div>
      )}

      {incomplete.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-yellow-400 mb-2">
            &#128064; Casi completos — te falta al menos 1 pieza ({incomplete.length})
          </h4>
          {(() => {
            const totalPages = Math.ceil(Math.min(incomplete.length, 20) / pageSize)
            const start = page * pageSize
            const visible = incomplete.slice(start, start + pageSize)
            return (
              <>
                {visible.map(combo => (
                  <ComboCard key={combo.combo_id} combo={combo} expanded={expanded} onToggle={setExpanded} />
                ))}
                {incomplete.length > pageSize && (
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setPage(Math.max(0, page - 1))}
                        disabled={page === 0}
                        className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      >
                        ←
                      </button>
                      <span className="text-xs text-gray-500 px-2">
                        {start + 1}–{Math.min(start + pageSize, Math.min(incomplete.length, 20))} de {Math.min(incomplete.length, 20)}
                      </span>
                      <button
                        onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                        disabled={page >= totalPages - 1}
                        className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      >
                        →
                      </button>
                    </div>
                    <div className="flex items-center gap-1">
                      {[5, 10, 15, 20].map(n => (
                        <button
                          key={n}
                          onClick={() => { setPageSize(n); setPage(0); }}
                          className={`px-1.5 py-0.5 text-[10px] rounded transition-colors ${
                            pageSize === n
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                          }`}
                        >
                          {n}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )
          })()}
        </div>
      )}

    </div>
  )
}

// CSB bracket short codes → WotC bracket numbers (from Commander Spellbook syntax guide)
const BRACKET_MAP: Record<string, { label: string; cls: string }> = {
  'R': { label: 'Bracket 4+', cls: 'bg-red-500/20 text-red-400 border-red-500/40' },
  'S': { label: 'Bracket 3-4', cls: 'bg-orange-500/20 text-orange-400 border-orange-500/40' },
  'P': { label: 'Bracket 3', cls: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40' },
  'O': { label: 'Bracket 2-3', cls: 'bg-lime-500/20 text-lime-400 border-lime-500/40' },
  'C': { label: 'Bracket 2', cls: 'bg-green-500/20 text-green-400 border-green-500/40' },
  'E': { label: 'Bracket 1', cls: 'bg-blue-500/20 text-blue-400 border-blue-500/40' },
  'B': { label: 'Baneado', cls: 'bg-red-900/40 text-red-500 border-red-700/40' },
}

const ComboCard: FC<{
  combo: ComboInfo
  expanded: string | null
  onToggle: (id: string | null) => void
}> = ({ combo, expanded, onToggle }) => {
  const isOpen = expanded === combo.combo_id
  const hasCsbDesc = combo.description && combo.description.length > 60 && combo.produces?.length > 0
  const allCards = [...combo.cards_in_deck, ...combo.missing_pieces]
  const { open: openModal } = useCardModal()
  const bracket = BRACKET_MAP[combo.bracket]

  return (
    <div className="glass border border-gray-700 rounded-lg mb-2 overflow-hidden">
      <button
        onClick={() => onToggle(isOpen ? null : combo.combo_id)}
        className="w-full p-3 text-left flex items-center justify-between gap-2 hover:bg-white/5 transition-colors"
      >
        <div className="min-w-0 flex-1">
          <p className="text-sm text-white font-medium truncate">
            {allCards.join(' + ')}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-xs text-green-400">
              {combo.cards_in_deck.length} en mazo
            </span>
            {combo.missing_pieces.length > 0 && (
              <span className="text-xs text-red-400">
                {combo.missing_pieces.length} faltan
              </span>
            )}
            {combo.is_complete && (
              <span className="text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded font-bold">
                &#10003; Listo
              </span>
            )}
            {hasCsbDesc && (
              <span className="text-xs text-indigo-400">(Explicación disponible)</span>
            )}
            {bracket && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${bracket.cls}`}>
                {bracket.label}
              </span>
            )}
          </div>
        </div>
        <span className={`text-sm text-gray-500 transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`}>
          &#9660;
        </span>
      </button>

      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
        isOpen ? 'max-h-[4000px] opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="px-3 pb-3 space-y-4 text-sm border-t border-gray-700/50 pt-3">
          {/* CSB Description with mana symbols */}
          {combo.description && (
            <div className="glass rounded-lg p-3 border border-gray-700/50">
              <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
                <ManaText text={
                  (() => {
                    const lines = combo.description.split('\n').filter(l => l.trim())
                    if (lines.length <= 1) return combo.description
                    return lines.map((l, i) => `${i + 1}. ${l}`).join('\n')
                  })()
                } />
              </p>
            </div>
          )}

          {/* Produces */}
          {combo.produces && combo.produces.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {combo.produces.map((p, i) => (
                <span key={i} className="text-xs bg-purple-500/15 text-purple-300 rounded-full px-2 py-0.5 border border-purple-500/20">
                  {p}
                </span>
              ))}
            </div>
          )}

          {/* Meta: mana */}
          {combo.mana_needed && (
            <div className="flex items-center gap-3 flex-wrap text-xs">
              <span className="text-gray-400">
                Maná: <ManaText text={combo.mana_needed} />
              </span>
            </div>
          )}

          {/* Prerequisites */}
          {combo.prerequisites && (
            <div>
              <span className="text-xs text-gray-500">Requisitos:</span>
              <p className="text-xs text-gray-400 mt-0.5 whitespace-pre-line">{combo.prerequisites}</p>
            </div>
          )}

          {/* Cards in deck */}
          <div>
            <span className="text-xs text-gray-500 mb-2 block">Cartas en tu mazo:</span>
            <div className="flex flex-wrap gap-3">
              {combo.cards_in_deck.map(name => (
                <div key={name} className="flex flex-col items-center gap-1">
                  {combo.card_images?.[name] ? (
                    <FlipCardImage
                      frontUrl={combo.card_images[name]}
                      backUrl={combo.card_images_back?.[name]}
                      name={name}
                      className="w-36 sm:w-44"
                      onOpenModal={(current, back) => openModal(current, name, back)}
                    />
                  ) : (
                    <div className="w-36 sm:w-44 aspect-[5/7] glass rounded-lg flex items-center justify-center">
                      <span className="text-[10px] text-gray-500 text-center px-1">{name}</span>
                    </div>
                  )}
                  <a
                    href={`https://scryfall.com/search?q=!%22${encodeURIComponent(name)}%22`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-green-400 text-center leading-tight max-w-[112px] sm:max-w-[128px] hover:underline"
                  >{name}</a>
                </div>
              ))}
              {combo.cards_in_deck.length === 0 && (
                <span className="text-xs text-gray-500 italic">Ninguna carta de este combo está en tu mazo</span>
              )}
            </div>
          </div>

          {/* Missing pieces */}
          {combo.missing_pieces.length > 0 && (
            <div>
              <span className="text-xs text-gray-500 mb-2 block">Te falta:</span>
              <div className="flex flex-wrap gap-3">
                {combo.missing_pieces.map(name => (
                  <div key={name} className="flex flex-col items-center gap-1 opacity-70 hover:opacity-100 transition-opacity">
                    {combo.card_images?.[name] ? (
                      <FlipCardImage
                        frontUrl={combo.card_images[name]}
                        backUrl={combo.card_images_back?.[name]}
                        name={name}
                        className="w-36 sm:w-44"
                        onOpenModal={(current, back) => openModal(current, name, back)}
                      />
                    ) : (
                      <div className="w-36 sm:w-44 aspect-[5/7] glass rounded-lg flex items-center justify-center">
                        <span className="text-[10px] text-gray-500 text-center px-1">{name}</span>
                      </div>
                    )}
                    <a
                      href={`https://scryfall.com/search?q=!%22${encodeURIComponent(name)}%22`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-red-400 text-center leading-tight max-w-[112px] sm:max-w-[128px] hover:underline"
                    >{name}</a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* EDHREC link */}
          {combo.edhrec_link && (
            <a href={combo.edhrec_link} target="_blank" rel="noopener noreferrer"
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors inline-flex items-center gap-1">
              &#128279; Ver más combos en EDHREC
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default ComboPanel
