import { useState } from 'react'
import ManaCost from './ManaCost'

interface AnalysisReportProps {
  stats: any
  aiReport: string
}

const curveIcons: Record<string, string> = {
  '0-1': '①',
  '2-3': '③',
  '4-5': '⑤',
  '6+': '⑥',
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="glass rounded-xl p-4 flex flex-col items-center text-center">
      <span className={`text-3xl font-bold ${color}`}>{value}</span>
      <span className="text-xs text-gray-400 mt-1">{label}</span>
    </div>
  )
}

function DiagnosticBadge({
  label,
  value,
  good,
  warn,
  bad,
  unit,
  invert,
  hasCards,
  isSelected,
  onClick,
}: {
  label: string
  value: number
  good: [number, number]
  warn: [number, number]
  bad: [number, number]
  unit?: string
  invert?: boolean
  hasCards: boolean
  isSelected: boolean
  onClick: () => void
}) {
  let status: 'good' | 'warn' | 'bad' = 'good'
  if (value >= bad[0] && value <= bad[1]) status = invert ? 'good' : 'bad'
  else if (value >= warn[0] && value <= warn[1]) status = invert ? 'good' : 'warn'
  else if (value >= good[0] && value <= good[1]) status = invert ? 'warn' : 'good'

  const colors = {
    good: isSelected ? 'bg-emerald-900/50 border-emerald-500/60 text-emerald-200 ring-1 ring-emerald-500/50' : 'bg-emerald-900/30 border-emerald-600/40 text-emerald-300',
    warn: isSelected ? 'bg-yellow-900/40 border-yellow-500/60 text-yellow-200 ring-1 ring-yellow-500/50' : 'bg-yellow-900/20 border-yellow-600/40 text-yellow-300',
    bad: isSelected ? 'bg-red-900/40 border-red-500/60 text-red-200 ring-1 ring-red-500/50' : 'bg-red-900/20 border-red-600/40 text-red-300',
  }
  const icons = { good: '✅', warn: '⚠️', bad: '❌' }
  const labels = { good: 'Óptimo', warn: 'Aceptable', bad: 'Mejorable' }

  return (
    <button
      onClick={onClick}
      disabled={!hasCards}
      className={`rounded-xl p-4 border text-left transition-all duration-200 ${
        colors[status]
      } ${hasCards ? 'cursor-pointer hover:scale-[1.02] active:scale-[0.98]' : 'cursor-default opacity-60'}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs opacity-70">{icons[status]} {labels[status]}</span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <p className="text-2xl font-bold">
          {value}
          {unit ? <span className="text-sm font-normal opacity-70"> {unit}</span> : null}
        </p>
        {hasCards && (
          <svg
            className={`w-4 h-4 transition-transform duration-300 text-gray-400 ${isSelected ? 'rotate-180' : ''}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </div>
      <p className="text-xs mt-1 opacity-70">
        Recomendado: {good[0]}–{good[1]}{unit ? ` ${unit}` : ''}
      </p>
    </button>
  )
}

function DiagnosticPanel({ stats }: { stats: any }) {
  const cat = stats.categories || {}
  const catCards = stats.category_cards || {}
  const [selected, setSelected] = useState<string | null>(null)
  const archetype = stats.archetype || 'General / Midrange'
  const archetypes = stats.archetypes || []
  const thresholds = stats.archetype_thresholds || {}

  type Item = {
    label: string
    value: number
    good: [number, number]
    warn: [number, number]
    bad: [number, number]
    cards: string[]
    key: string
  }

  function getThreshold(key: string, def: [number, number]): [number, number] {
    const t = thresholds[key]
    if (t && Array.isArray(t) && t.length === 2) return [t[0], t[1]]
    return def
  }

  function getThresholdExt(key: string, gd: [number,number], wn: [number,number], bd: [number,number]) {
    const t = thresholds[key]
    if (t && Array.isArray(t) && t.length === 2) {
      const [lo, hi] = t
      const span = hi - lo
      return {
        good: [lo, hi] as [number, number],
        warn: [Math.max(0, lo - Math.ceil(span*0.4)), lo - 1] as [number, number],
        bad: [0, Math.max(0, lo - Math.ceil(span*0.4)) - 1] as [number, number],
      }
    }
    return { good: gd, warn: wn, bad: bd }
  }

  const items: Item[] = [
    { label: 'Ramp / Aceleración', value: cat.ramp, ...getThresholdExt('ramp', [10, 14], [7, 9], [0, 6]), cards: catCards.ramp || [], key: 'ramp' },
    { label: 'Robo de cartas (Draw)', value: cat.draw, ...getThresholdExt('draw', [10, 15], [6, 9], [0, 5]), cards: catCards.draw || [], key: 'draw' },
    { label: 'Removal / Bajas', value: cat.removal, ...getThresholdExt('removal', [8, 14], [5, 7], [0, 4]), cards: catCards.removal || [], key: 'removal' },
    { label: 'Wipes (limpieza global)', value: cat.wipes, ...getThresholdExt('wipes', [2, 5], [1, 1], [0, 0]), cards: catCards.wipes || [], key: 'wipes' },
    { label: 'Interacción / respuestas', value: cat.interaction, ...getThresholdExt('interaction', [6, 12], [3, 5], [0, 2]), cards: catCards.interaction || [], key: 'interaction' },
    { label: 'Tutores', value: cat.tutors, ...getThresholdExt('tutors', [2, 6], [1, 1], [0, 0]), cards: catCards.tutors || [], key: 'tutors' },
  ]

  const activeItem = items.find((i) => i.key === selected)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        🔎
        <h3 className="text-lg font-semibold text-gray-200">Diagnóstico rápido</h3>
        {archetypes.map((a: any, i: number) => (
          <span
            key={a.name}
            className={`text-xs px-2.5 py-0.5 rounded-full border font-medium whitespace-nowrap ${
              i === 0
                ? 'bg-indigo-900/60 text-indigo-300 border-indigo-700/50'
                : 'bg-gray-800/50 text-gray-400 border-gray-700/30'
            }`}
          >
            {a.name} {a.weight < 0.99 ? `${Math.round(a.weight * 100)}%` : ''}
          </span>
        ))}
        <span className="text-xs text-gray-500 font-normal">(umbrales combinados)</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map((item) => (
          <DiagnosticBadge
            key={item.label}
            label={item.label}
            value={item.value}
            good={item.good}
            warn={item.warn}
            bad={item.bad}
            hasCards={item.cards.length > 0}
            isSelected={selected === item.key}
            onClick={() => setSelected(selected === item.key ? null : item.key)}
          />
        ))}
      </div>

      {/* Expandable card list below grid */}
      <div
        className={`overflow-hidden transition-all duration-400 ease-in-out ${
          activeItem ? 'max-h-[3000px] opacity-100 mt-3' : 'max-h-0 opacity-0'
        }`}
      >
        {activeItem && (
          <div className="glass rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-200">
                📋 {activeItem.label} — {activeItem.cards.length} cartas
              </h4>
              <button
                onClick={() => setSelected(null)}
                className="text-gray-500 hover:text-gray-300 transition-colors text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {activeItem.cards.map((card, i) => (
                <div
                  key={i}
                  className="text-xs px-2 py-1.5 rounded-lg border border-gray-700/50 bg-gray-800/50 text-gray-300 truncate hover:border-gray-500/50 transition-colors"
                  title={card}
                >
                  {card}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tierras + CMC recomendados (no expandibles) */}
      {thresholds.lands && thresholds.cmc && (() => {
        const landStatus = cat.lands >= thresholds.lands[0] && cat.lands <= thresholds.lands[1]
          ? 'good' : cat.lands >= thresholds.lands[0] - 5 && cat.lands <= thresholds.lands[1] + 3
          ? 'warn' : 'bad'
        const cmcStatus = stats.average_cmc >= thresholds.cmc[0] && stats.average_cmc <= thresholds.cmc[1]
          ? 'good' : stats.average_cmc >= thresholds.cmc[0] - 0.5 && stats.average_cmc <= thresholds.cmc[1] + 0.5
          ? 'warn' : 'bad'

        const statusColors: Record<string, string> = {
          good: 'bg-emerald-900/30 border-emerald-600/40',
          warn: 'bg-yellow-900/20 border-yellow-600/40',
          bad: 'bg-red-900/20 border-red-600/40',
        }
        const statusIcons: Record<string, string> = {
          good: '✅',
          warn: '⚠️',
          bad: '❌',
        }
        const statusLabels: Record<string, string> = { good: 'Óptimo', warn: 'Aceptable', bad: 'Mejorable' }

        return (
        <div className="grid grid-cols-2 gap-3">
          <div className={`rounded-xl p-4 border ${statusColors[landStatus]}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-300 flex items-center gap-1">🌳 Tierras recomendadas</span>
              <span className="text-xs opacity-70">{statusIcons[landStatus]} {statusLabels[landStatus]}</span>
            </div>
            <p className="text-2xl font-bold text-green-400 mt-1">
              {thresholds.lands[0]}–{thresholds.lands[1]}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Tus tierras: <span className="font-semibold">{cat.lands}</span>
            </p>
          </div>
          <div className={`rounded-xl p-4 border ${statusColors[cmcStatus]}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-300 flex items-center gap-1">📊 CMC recomendado</span>
              <span className="text-xs opacity-70">{statusIcons[cmcStatus]} {statusLabels[cmcStatus]}</span>
            </div>
            <p className="text-2xl font-bold text-pink-400 mt-1">
              {thresholds.cmc[0]?.toFixed(1)}–{thresholds.cmc[1]?.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Tu CMC: <span className="font-semibold">{stats.average_cmc}</span>
            </p>
          </div>
        </div>
        )
      })()}

      <div className="glass rounded-xl p-4 text-xs text-gray-400 leading-relaxed space-y-2">
        <p>
          <strong className="text-gray-300 flex items-center gap-1">💡 Cómo leer esto:</strong> Estos valores son guías generales para
          Commander casual. Mazos competitivos (cEDH) o temáticos (tribal, spellslinger, voltron) pueden variar
          mucho.
        </p>
        <ul className="list-disc list-inside space-y-1 text-gray-500">
          <li>Land count bajo + ramp bajo = tu mazo sufrirá de <em>mana screw</em> frecuentemente.</li>
          <li>CMC alto + poco ramp = no jugarás nada hasta turno 4-5.</li>
          <li>Poco draw = te quedarás sin cartas rápido y dependerás del top-deck.</li>
          <li>Sin removal = no podrás responder a las amenazas de tus oponentes.</li>
          <li>Sin wipes = si la mesa se te va de control, no tienes botón de reset.</li>
        </ul>
      </div>

      {stats.opening_hand_simulation && (
        <div className="glass rounded-xl p-4 bg-gray-800/50">
          <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">🎲 Resultado de 1000 simulaciones de mano inicial:</p>
          <p className="text-sm text-gray-300">
            De cada 1000 manos, <span className="text-emerald-400 font-bold">{stats.opening_hand_simulation.keep_rate}%</span> son
            jugables (2-5 tierras).{' '}
            <span className="text-red-400 font-bold">{stats.opening_hand_simulation.mulligan_rate}%</span> requieren
            mulligan. Promedio de tierras en mano: <span className="text-white">{stats.opening_hand_simulation.average_lands}</span>.
          </p>
        </div>
      )}
    </div>
  )
}

export default function AnalysisReport({ stats, aiReport }: AnalysisReportProps) {
  if (!stats) return null;

  if (stats.error) {
    return (
      <div className="mt-6 p-6 glass rounded-2xl border border-red-700/50 bg-red-900/20">
          <h3 className="text-lg font-semibold text-red-400 mb-2 flex items-center gap-1.5">⚠️ Error del servidor</h3>
        <p className="text-sm text-red-300 font-mono">{stats.error}</p>
        <p className="text-xs text-gray-500 mt-3">Revisa la consola del backend para más detalles.</p>
      </div>
    )
  }

  const curve: Record<string, number> = stats.curve || {}
  const cat = stats.categories || {}
  const cmdr = stats.commander || {}
  const sim = stats.opening_hand_simulation || {}
  const maxCurve = Math.max(...Object.values(curve) as number[], 1)

  return (
    <div className="mt-6 space-y-6 animate-in fade-in">
      {/* Commander banner */}
      <div className="glass rounded-2xl p-6 bg-gradient-to-r from-indigo-900/30 to-purple-900/30">
        <div className="flex items-center gap-4">
          👑
          <div className="flex-1">
            <h2 className="text-xl font-bold text-white">{cmdr.name || 'Comandante'}</h2>
            <p className="text-sm text-gray-400 flex items-center gap-2 flex-wrap">
              <ManaCost cost={cmdr.mana_cost} />
              <span>· CMC {cmdr.cmc}</span>
              <span>· {cmdr.type}</span>
              <span>· <ManaCost cost={(cmdr.color_identity || []).map((c: string) => `{${c}}`).join('')} /></span>
            </p>
          </div>
          {stats.archetypes && stats.archetypes.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {stats.archetypes.map((a: any, i: number) => (
                <span
                  key={a.name}
                  className={`text-xs px-2.5 py-1 rounded-full whitespace-nowrap border flex items-center gap-1 ${
                    i === 0
                      ? 'bg-indigo-900/60 text-indigo-300 border-indigo-700/40 font-semibold'
                      : 'bg-gray-800/60 text-gray-400 border-gray-700/40'
                  }`}
                >
                  🎯 {a.name} {a.weight < 0.99 ? `(${Math.round(a.weight * 100)}%)` : ''}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Illegal cards warning */}
      {stats.illegal_cards?.length > 0 && (
        <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-xl">
          <p className="text-red-300 font-semibold text-sm flex items-center gap-1">⚠️ Cartas fuera de identidad de color:</p>
          <ul className="list-disc list-inside text-red-400 text-sm mt-1">
            {stats.illegal_cards.map((c: string) => <li key={c}>{c}</li>)}
          </ul>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-7 gap-3">
        <StatCard label="Tierras" value={cat.lands} color="text-green-400" />
        <StatCard label="Criaturas" value={cat.creatures} color="text-amber-400" />
        <StatCard label="Artifacts" value={cat.artifacts} color="text-gray-200" />
        <StatCard label="Encant" value={cat.enchantments} color="text-purple-400" />
        <StatCard label="Instants" value={cat.instants} color="text-cyan-400" />
        <StatCard label="Conjuros" value={cat.sorceries} color="text-rose-400" />
        <StatCard label="CMC prom" value={stats.average_cmc} color="text-pink-400" />
      </div>

      {/* Functional categories */}
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-1.5">
        🧰 Roles funcionales
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        <StatCard label="Ramp" value={cat.ramp} color="text-emerald-400" />
        <StatCard label="Robo (Draw)" value={cat.draw} color="text-blue-400" />
        <StatCard label="Removal" value={cat.removal} color="text-red-400" />
        <StatCard label="Wipes" value={cat.wipes} color="text-orange-400" />
        <StatCard label="Tutores" value={cat.tutors} color="text-yellow-400" />
        <StatCard label="Interacción" value={cat.interaction} color="text-sky-400" />
      </div>

      {/* Mana curve */}
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-1.5">
        📈 Curva de maná (CMC: {stats.average_cmc})
      </h3>
      <div className="glass rounded-2xl p-6 space-y-3">
        {Object.entries(curve).map(([key, value]) => (
          <div key={key} className="flex items-center gap-3">
            <span className="text-sm text-gray-400 w-10 text-right">{curveIcons[key]} {key}</span>
            <div className="flex-1 bg-gray-800 rounded-full h-6 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-700"
                style={{ width: `${((value as number) / maxCurve) * 100}%`, minWidth: '2px' }}
              />
            </div>
            <span className="text-sm text-gray-300 w-10 font-mono">{value}</span>
          </div>
        ))}
      </div>

      {/* Opening hand simulation */}
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-1.5">
        🎲 Simulación de manos iniciales
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Manos simuladas" value={sim.iterations} color="text-gray-200" />
        <StatCard label="Tierras promedio" value={sim.average_lands} color="text-green-400" />
        <StatCard label="% Keep" value={sim.keep_rate} color="text-emerald-400" />
        <StatCard label="% Mulligan" value={sim.mulligan_rate} color="text-red-400" />
      </div>

      {/* AI Report or Diagnostic Panel */}
      {aiReport ? (
        <div className="glass rounded-2xl p-6 bg-gradient-to-br from-indigo-950/50 to-gray-900">
          <h3 className="text-lg font-semibold text-indigo-300 mb-4 flex items-center gap-1.5">
            🧠 Análisis del Coach (IA)
          </h3>
          <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
            {aiReport}
          </div>
        </div>
      ) : (
        <div className="glass rounded-2xl p-6">
          <DiagnosticPanel stats={stats} />
        </div>
      )}
    </div>
  )
}
