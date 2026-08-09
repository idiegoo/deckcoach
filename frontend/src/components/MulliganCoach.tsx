import { useState } from 'react'
import { getMulliganAdvice } from '../services/api'

interface MulliganCoachProps {
  decklist: string
  useAI: boolean
}

export default function MulliganCoach({ decklist, useAI }: MulliganCoachProps) {
  const [handInput, setHandInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!decklist.trim()) {
      setError('Primero pega tu lista de mazo en la pestaña Análisis.')
      return
    }
    const cards = handInput
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (cards.length !== 7) {
      setError(`Ingresa exactamente 7 cartas (ingresaste ${cards.length}). Sepáralas por coma o una por línea.`)
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await getMulliganAdvice(decklist, '', cards, useAI)
      setResult(data)
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Error al evaluar la mano.')
    } finally {
      setLoading(false)
    }
  }

  const decisionColor =
    result?.decision === 'keep'
      ? 'text-emerald-400'
      : result?.decision === 'mulligan'
      ? 'text-red-400'
      : 'text-gray-400'

  return (
    <div className="mt-6 space-y-6">
      <div className="glass rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            ✋ Tu mano inicial (7 cartas)
          </label>
          <textarea
            placeholder="Sol Ring&#10;Arcane Signet&#10;Command Tower&#10;Demonic Tutor&#10;Dark Ritual&#10;Vampiric Tutor&#10;Swamp"
            rows={5}
            value={handInput}
            onChange={(e) => setHandInput(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 font-mono text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors resize-y"
          />
          <p className="text-xs text-gray-500 mt-1">
            Escribe las 7 cartas (separadas por coma o una por línea). Usa el mismo deck de la
            pestaña Análisis.
          </p>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-3 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-xl text-white font-semibold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-600/20 active:scale-[0.98]"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Evaluando mano...
            </span>
          ) : (
            '🧐 Evaluar mulligan'
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-xl text-red-300 text-sm">
          {error}
        </div>
      )}

      {result && result.decision !== 'invalid' && (
        <div className="glass rounded-2xl p-6 space-y-6 animate-in fade-in">
          <div className={`p-6 rounded-xl text-center border-2 ${
            result.decision === 'keep'
              ? 'bg-emerald-900/20 border-emerald-700/50'
              : 'bg-red-900/20 border-red-700/50'
          }`}>
            <span className="text-5xl block mb-2">
              {result.decision === 'keep' ? '✅' : '🔄'}
            </span>
            <h2 className={`text-3xl font-bold ${decisionColor}`}>
              {result.decision === 'keep' ? '¡Quédate!' : '¡Haz Mulligan!'}
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              Confianza: <span className="font-semibold text-gray-300">{result.confidence}</span>
            </p>
          </div>

          <div className="glass rounded-xl p-5 bg-indigo-950/30">
            <p className="text-xs text-indigo-400 font-semibold mb-2 uppercase tracking-wider">
              {result.reasoning ? '🧠 El coach dice:' : '📋 Análisis heurístico:'}
            </p>
            <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
              {result.reasoning || (
                <ul className="list-disc list-inside space-y-1">
                  {result.hand_stats?.heuristic_reasons?.map((r: string, i: number) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {result.hand_stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-green-400">{result.hand_stats.land_count}</p>
                <p className="text-xs text-gray-500">Tierras en mano</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-blue-400">{result.hand_stats.avg_cmc_nonlands}</p>
                <p className="text-xs text-gray-500">CMC promedio</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className={`text-2xl font-bold ${result.hand_stats.has_ramp ? 'text-green-400' : 'text-red-400'}`}>
                  {result.hand_stats.has_ramp ? 'Sí' : 'No'}
                </p>
                <p className="text-xs text-gray-500">Tiene ramp</p>
              </div>
              <div className="glass rounded-xl p-3 text-center">
                <p className={`text-2xl font-bold ${result.hand_stats.has_draw ? 'text-green-400' : 'text-red-400'}`}>
                  {result.hand_stats.has_draw ? 'Sí' : 'No'}
                </p>
                <p className="text-xs text-gray-500">Tiene robo</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
