import { FC, useState, useMemo } from 'react';
import FlipCardImage from './FlipCardImage';
import { useCardModal } from './CardModalContext';

interface StapleCard {
  name: string;
  inclusion_pct: number;
  category: string;
  image_url?: string;
}

interface StaplesPanelProps {
  suggestions: Record<string, StapleCard[]>;
}

const TYPE_ICONS: Record<string, { icon: string; label: string; color: string }> = {
  'Top Cards': { icon: '/svg/multiple.svg', label: 'Top Cards', color: '#818cf8' },
  'New Cards': { icon: '/svg/multiple.svg', label: 'Nuevas', color: '#34d399' },
  'Game Changers': { icon: '/svg/multiple.svg', label: 'Game Changers', color: '#f472b6' },
  'Creatures': { icon: '/svg/creature.svg', label: 'Criaturas', color: '#fbbf24' },
  'Instants': { icon: '/svg/instant.svg', label: 'Instants', color: '#22d3ee' },
  'Sorceries': { icon: '/svg/sorcery.svg', label: 'Sorcerías', color: '#fb7185' },
  'Artifacts': { icon: '/svg/artifact.svg', label: 'Artefactos', color: '#94a3b8' },
  'Utility Artifacts': { icon: '/svg/artifact.svg', label: 'Artefactos', color: '#94a3b8' },
  'Mana Artifacts': { icon: '/svg/artifact.svg', label: 'Maná Art.', color: '#94a3b8' },
  'Enchantments': { icon: '/svg/enchantment.svg', label: 'Encantamientos', color: '#c084fc' },
  'Planeswalkers': { icon: '/svg/planeswalker.svg', label: 'Planeswalkers', color: '#f97316' },
  'Lands': { icon: '/svg/land.svg', label: 'Tierras', color: '#34d399' },
  'Utility Lands': { icon: '/svg/land.svg', label: 'T. Utilidad', color: '#34d399' },
  'Battles': { icon: '/svg/multiple.svg', label: 'Batallas', color: '#a78bfa' },
};

const StaplesPanel: FC<StaplesPanelProps> = ({ suggestions }) => {
  const categories = useMemo(() => {
    if (!suggestions) return [];
    return Object.keys(suggestions);  // Show all, even empty ones
  }, [suggestions]);

  const [activeCat, setActiveCat] = useState<string>(categories[0] || '');
  const { open: openModal } = useCardModal();

  if (!suggestions || Object.keys(suggestions).length === 0) {
    return (
      <div className="glass p-4 rounded-xl text-center text-gray-400 text-sm">
        Cargando sugerencias de EDHREC...
      </div>
    );
  }

  const currentCards = suggestions[activeCat] || [];
  const typeInfo = TYPE_ICONS[activeCat] || { icon: '/svg/multiple.svg', label: activeCat, color: '#818cf8' };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-purple-400 text-lg">&#9733;</span>
        <h3 className="text-lg font-bold text-white">Staples que te faltan</h3>
        <span className="text-xs text-gray-500">(según EDHREC)</span>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        {/* Sidebar — vertical on desktop, horizontal scroll on mobile */}
        <div className="sm:w-36 shrink-0 flex sm:flex-col gap-0.5 overflow-x-auto sm:overflow-x-visible pb-1 sm:pb-0 -mx-1 px-1">
          {categories.map(cat => {
            const info = TYPE_ICONS[cat] || { icon: '/svg/multiple.svg', label: cat, color: '#94a3b8' };
            const isActive = activeCat === cat;
            const count = suggestions[cat]?.length || 0;
            return (
              <button
                key={cat}
                onClick={() => setActiveCat(cat)}
                className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-all text-xs whitespace-nowrap shrink-0 sm:w-full ${
                  isActive
                    ? 'bg-indigo-600/20 border border-indigo-500/40 shadow-sm'
                    : 'hover:bg-gray-800/50 border border-transparent text-gray-400'
                }`}
              >
                <span
                  className="inline-flex items-center justify-center rounded-full shrink-0"
                  style={{
                    backgroundColor: isActive ? info.color : (info.color + '20'),
                    width: 28,
                    height: 28,
                    padding: 4,
                  }}
                >
                  <img
                    src={info.icon}
                    alt=""
                    width={20}
                    height={20}
                    style={{
                      filter: isActive
                        ? 'brightness(0) invert(1)'
                        : 'none',
                    }}
                    className="inline-block"
                  />
                </span>
                <span className={`truncate hidden sm:inline flex-1 ${isActive ? 'text-white font-medium' : ''}`}>
                  {info.label}
                </span>
                <span className={`text-[10px] font-mono ${isActive ? 'text-indigo-400' : 'text-gray-600'} ${count === 0 && !isActive ? 'opacity-40' : ''}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Cards List */}
        <div className="flex-1 min-w-0">
          {/* Selected category header */}
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-700/50">
            <span
              className="inline-flex items-center justify-center rounded-full"
              style={{ backgroundColor: typeInfo.color, width: 28, height: 28, padding: 4 }}
            >
              <img
                src={typeInfo.icon}
                alt=""
                width={20}
                height={20}
                style={{ filter: 'brightness(0) invert(1)' }}
                className="inline-block"
              />
            </span>
            <span className="text-sm font-semibold text-white">{typeInfo.label}</span>
            <span className="text-xs text-gray-500">{currentCards.length} faltantes</span>
          </div>

          <div className="flex flex-wrap gap-3 max-h-[420px] overflow-y-auto pr-1">
            {currentCards.length > 0 ? currentCards.map((card) => (
              <div key={card.name} className="flex flex-col items-center gap-1">
                {card.image_url ? (
                  <FlipCardImage
                    frontUrl={card.image_url}
                    backUrl={null}
                    name={card.name}
                    className="w-36 sm:w-44"
                    onOpenModal={(current, back) => openModal(current, card.name, back)}
                  />
                ) : (
                  <div className="w-36 sm:w-44 aspect-[5/7] glass rounded-lg flex flex-col items-center justify-center gap-1">
                    <span className="text-[10px] text-gray-500 text-center px-1">{card.name}</span>
                  </div>
                )}
                <a
                  href={`https://scryfall.com/search?q=!%22${encodeURIComponent(card.name)}%22`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-gray-300 text-center leading-tight max-w-[144px] sm:max-w-[176px] hover:underline"
                >{card.name}</a>
                <div className="flex items-center gap-1.5">
                  <div className="w-14 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(card.inclusion_pct, 100)}%`,
                        backgroundColor: typeInfo.color,
                      }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-gray-400">
                    {card.inclusion_pct}%
                  </span>
                </div>
              </div>
            )) : (
              <p className="text-sm text-gray-500 italic py-4 w-full text-center">
                No hay recomendaciones para esta categoría
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StaplesPanel;
