import { FC } from 'react';

interface SvgIconProps {
  name:
    | 'w' | 'u' | 'b' | 'r' | 'g' | 'c' | 's'
    | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
    | '10' | '11' | '12' | '13' | '14' | '15' | '16' | '17' | '18' | '19' | '20'
    | '100' | '1000000'
    | 'x' | 'y' | 'z'
    | 't' // tap
    | 'q' // untap
    | 'infinity' | 'half'
    | 'creature' | 'instant' | 'sorcery' | 'enchantment'
    | 'artifact' | 'land' | 'planeswalker'
    | 'token' | 'multiple' | 'chaos' | 'acorn'
    | 'flashback' | 'saga' | 'power' | 'toughness'
    | 'tap' | 'untap' | 'ticket' | 'rarity';
  size?: number;
  className?: string;
}

const SvgIcon: FC<SvgIconProps> = ({ name, size = 20, className = '' }) => {
  return (
    <img
      src={`/svg/${name}.svg`}
      alt={name}
      width={size}
      height={size}
      className={`inline-block align-middle ${className}`}
      style={{ filter: className ? undefined : 'invert(0.6)' }}
    />
  );
};

export default SvgIcon;
