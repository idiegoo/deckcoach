interface DeckInputProps {
  decklist: string
  setDecklist: (v: string) => void
  onAnalyze: () => void
  loading: boolean
}

export default function DeckInput({
  decklist,
  setDecklist,
  onAnalyze,
  loading,
}: DeckInputProps) {
  return (
    <div className="glass rounded-2xl p-6 space-y-4">
      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">
          📜 Lista del mazo
        </label>
        <textarea
          placeholder="1 Sol Ring&#10;1 Arcane Signet&#10;1 Command Tower&#10;...&#10;&#10;1 Tivit, Seller of Secrets"
          rows={10}
          value={decklist}
          onChange={(e) => setDecklist(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 font-mono text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors resize-y"
        />
        <p className="text-xs text-gray-500 mt-1">
          Pega tu lista de 99 cartas. El comandante se detecta automáticamente al final separado por un espacio en blanco, o marcado con <code>*CMDR*</code>. Soporta Moxfield y Archidekt.
        </p>
      </div>

      <div className="flex items-center justify-between glass rounded-xl p-3 opacity-60">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-300">🧠 Análisis con IA</span>
          <span className="text-xs text-gray-500">(próximamente)</span>
        </div>
        <div className="relative w-12 h-6 rounded-full bg-gray-700 cursor-not-allowed">
          <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-gray-500 rounded-full shadow" />
        </div>
      </div>

      <button
        onClick={onAnalyze}
        disabled={loading}
        className="w-full py-3 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl text-white font-semibold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20 active:scale-[0.98]"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Analizando mazo...
          </span>
        ) : (
          '🔍 Analizar mazo'
        )}
      </button>
    </div>
  )
}
