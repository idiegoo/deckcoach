import { useState, useEffect, useRef } from 'react'
import DeckInput from './components/DeckInput'
import AnalysisReport from './components/AnalysisReport'
import MulliganCoach from './components/MulliganCoach'
import BudgetToggle from './components/BudgetToggle'
import { CardModalProvider } from './components/CardModalContext'
import { analyzeDeck } from './services/api'
import { IconWizard } from './components/Icons'

type Tab = 'analyze' | 'mulligan'
type BudgetOption = 'normal' | 'budget' | 'expensive'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('analyze')
  const [decklist, setDecklist] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState('')
  const [budget, setBudget] = useState<BudgetOption>('normal')
  const budgetRef = useRef(budget)
  const resultsRef = useRef(results)
  resultsRef.current = results

  // Re-analyze when budget changes (if decklist is already loaded)
  useEffect(() => {
    if (budgetRef.current !== budget && decklist.trim() && resultsRef.current) {
      budgetRef.current = budget
      handleAnalyze()
    } else {
      budgetRef.current = budget
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [budget])

  const handleAnalyze = async () => {
    if (!decklist.trim()) {
      setError('Pega tu lista de mazo para analizarla.')
      return
    }
    setLoading(true)
    setError('')
    setResults(null)
    try {
      const data = await analyzeDeck(decklist, '', false, budget === 'normal' ? undefined : budget)
      setResults(data)
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Error al analizar el mazo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <CardModalProvider>
    <div className="min-h-screen flex flex-col">
      <header className="glass sticky top-0 z-50 border-b border-gray-700/50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-indigo-400"><IconWizard size={30} /></span>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 text-transparent bg-clip-text">
              DeckCoach
            </h1>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">EDH</span>
          </div>

          <nav className="flex gap-1 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('analyze')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === 'analyze'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Análisis
            </button>
            <button
              onClick={() => setActiveTab('mulligan')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === 'mulligan'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Mulligan
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        <DeckInput
          decklist={decklist}
          setDecklist={setDecklist}
          onAnalyze={handleAnalyze}
          loading={loading}
        />

        {activeTab === 'analyze' && (
          <div className="flex justify-end mt-3">
            <BudgetToggle budget={budget} onChange={setBudget} />
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-900/30 border border-red-700/50 rounded-xl text-red-300 text-sm">
            {error}
          </div>
        )}

        {activeTab === 'analyze' && results && (
          <AnalysisReport
            stats={results.stats}
            aiReport={results.ai_report}
            budget={budget}
          />
        )}

        {activeTab === 'mulligan' && (
          <MulliganCoach decklist={decklist} useAI={false} />
        )}
      </main>

      <footer className="text-center py-4 text-gray-600 text-xs border-t border-gray-800">
        DeckCoach · Datos de cartas vía Scryfall y EDHREC · Combos vía Commander Spellbook · Hecho por <a href="https://idiegoo.vercel.app" className="text-indigo-400 hover:text-indigo-300">idiegoo</a> · <a href="https://github.com/idiegoo/deckcoach" className="text-indigo-400 hover:text-indigo-300">GitHub</a>
      </footer>
    </div>
    </CardModalProvider>
  )
}
