import { FC, useState } from 'react'
import FlipCardImage from './FlipCardImage'
import { useCardModal } from './CardModalContext';

interface DeckComparisonProps {
  comparison: {
    similarity_pct: number;
    avg_lands: number;
    user_lands: number;
    missing_common: string[];
    unique_user_cards: string[];
  };
  budget?: string | null;
  cardImages?: Record<string, string>;
  cardImagesBack?: Record<string, string>;
}

const DeckComparison: FC<DeckComparisonProps> = ({ comparison, budget, cardImages, cardImagesBack }) => {
  const { open: openModal } = useCardModal()
  const [isOpen, setIsOpen] = useState(false)

  if (!comparison || (comparison.similarity_pct === 0 && comparison.avg_lands === 0)) {
    return (
      <div className="glass p-4 rounded-xl text-center text-gray-400 text-sm">
        Cargando comparación con el mazo promedio de EDHREC...
      </div>
    );
  }

  const budgetLabel = budget === 'budget' ? '(versión budget)' : budget === 'expensive' ? '(versión expensive)' : '';

  const getSimilarityColor = (pct: number) => {
    if (pct >= 60) return 'text-green-400';
    if (pct >= 35) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {/* Header — always visible with summary */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-blue-400 text-lg shrink-0">&#8962;</span>
            <h3 className="text-lg font-bold text-white truncate">
              Comparación vs. mazo promedio {budgetLabel}
            </h3>
          </div>
          <span className={`text-sm text-gray-500 transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`}>
            &#9660;
          </span>
        </div>

        {/* Summary: similarity + land cards */}
        <div className="mt-3">
          <div className="text-center">
            <span className={`text-3xl font-bold ${getSimilarityColor(comparison.similarity_pct)}`}>
              {comparison.similarity_pct}%
            </span>
            <p className="text-sm text-gray-400 mt-1">de similitud con el promedio de EDHREC</p>
          </div>

          {/* Land comparison */}
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div className="glass rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500">Tus tierras</p>
              <p className="text-xl font-bold text-green-400">{comparison.user_lands}</p>
            </div>
            <div className="glass rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500">Tierras (promedio)</p>
              <p className="text-xl font-bold text-blue-400">{comparison.avg_lands}</p>
            </div>
          </div>
        </div>
      </button>

      {/* Expandable content */}
      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
        isOpen ? 'max-h-[4000px] opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="px-4 pb-4 space-y-4 border-t border-gray-700/50 pt-3">
          {/* Missing common cards */}
          {comparison.missing_common.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-yellow-400 mb-2">
                &#9888; Cartas comunes que NO tienes
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {comparison.missing_common.map(name => (
                  <div
                    key={name}
                    className={`flex items-center gap-2 glass border border-yellow-500/20 rounded-lg px-2 py-1.5`}
                  >
                    {cardImages?.[name] && (
                      <FlipCardImage
                        frontUrl={cardImages[name]} backUrl={cardImagesBack?.[name]} name={name}
                        className="w-8 shrink-0"
                        onOpenModal={(current, back) => openModal(current, name, back)}
                      />
                    )}
                    <span className="text-xs text-gray-300 truncate">{name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unique user cards */}
          {comparison.unique_user_cards.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-purple-400 mb-2">
                &#10024; Cartas únicas de tu mazo
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {comparison.unique_user_cards.map(name => (
                  <div
                    key={name}
                    className={`flex items-center gap-2 glass border border-purple-500/20 rounded-lg px-2 py-1.5`}
                  >
                    {cardImages?.[name] && (
                      <FlipCardImage
                        frontUrl={cardImages[name]} backUrl={cardImagesBack?.[name]} name={name}
                        className="w-8 shrink-0"
                        onOpenModal={(current, back) => openModal(current, name, back)}
                      />
                    )}
                    <span className="text-xs text-gray-300 truncate">{name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {comparison.missing_common.length === 0 && comparison.unique_user_cards.length === 0 && (
            <p className="text-sm text-gray-500 italic text-center py-2">
              Sin diferencias notables con el mazo promedio
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeckComparison;
