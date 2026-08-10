import { FC } from 'react';

interface BudgetToggleProps {
  budget: 'normal' | 'budget' | 'expensive';
  onChange: (b: 'normal' | 'budget' | 'expensive') => void;
}

const OPTIONS: { value: 'normal' | 'budget' | 'expensive'; label: string }[] = [
  { value: 'normal', label: 'Normal' },
  { value: 'budget', label: 'Budget' },
  { value: 'expensive', label: 'Caro' },
];

const BudgetToggle: FC<BudgetToggleProps> = ({ budget, onChange }) => {
  return (
    <div className="flex items-center gap-1 glass rounded-lg p-1">
      <span className="text-xs text-gray-500 mr-2 shrink-0">Presupuesto</span>
      {OPTIONS.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          className={`px-3 py-1 text-xs rounded-md transition-all ${
            budget === value
              ? 'bg-indigo-600 text-white shadow'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
};

export default BudgetToggle;
