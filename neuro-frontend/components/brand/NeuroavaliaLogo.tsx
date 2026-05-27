import React from "react";

type NeuroavaliaLogoProps = {
  compact?: boolean;
  className?: string;
};

export function NeuroavaliaLogo({ compact = false, className }: NeuroavaliaLogoProps) {
  const viewBox = compact ? "18 24 164 162" : "0 8 760 176";

  return (
    <svg viewBox={viewBox} xmlns="http://www.w3.org/2000/svg" aria-label="Neuroavalia" role="img" className={className}>
      <g transform="translate(100 105)">
        <line x1="0" y1="0" x2="-46" y2="-48" stroke="#9EB4C2" strokeWidth="1.8" />
        <line x1="0" y1="0" x2="18" y2="-62" stroke="#9EB4C2" strokeWidth="1.8" />
        <line x1="0" y1="0" x2="58" y2="-42" stroke="#9EB4C2" strokeWidth="1.8" />
        <line x1="0" y1="0" x2="68" y2="4" stroke="#9EB4C2" strokeWidth="1.8" />
        <line x1="0" y1="0" x2="34" y2="56" stroke="#9EB4C2" strokeWidth="1.8" />
        <line x1="0" y1="0" x2="-32" y2="54" stroke="#9EB4C2" strokeWidth="1.8" />
        <line x1="0" y1="0" x2="-66" y2="12" stroke="#9EB4C2" strokeWidth="1.8" />

        <path d="M-46 -48 L18 -62 L58 -42 L68 4 L34 56 L-32 54 L-66 12 Z" fill="none" stroke="#D6E2E8" strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M-46 -48 C-20 -72, 25 -84, 58 -42" fill="none" stroke="#D6E2E8" strokeWidth="1.4" strokeLinecap="round" />
        <path d="M-66 12 C-42 38, -5 70, 34 56" fill="none" stroke="#D6E2E8" strokeWidth="1.4" strokeLinecap="round" />

        <circle cx="0" cy="0" r="8.5" fill="#123A5A" />
        <circle cx="-46" cy="-48" r="7" fill="#CBD6DE" />
        <circle cx="18" cy="-62" r="7" fill="#27BBD0" />
        <circle cx="58" cy="-42" r="7" fill="#CBD6DE" />
        <circle cx="68" cy="4" r="7" fill="#123A5A" />
        <circle cx="34" cy="56" r="7" fill="#CBD6DE" />
        <circle cx="-32" cy="54" r="7" fill="#27BBD0" />
        <circle cx="-66" cy="12" r="7" fill="#CBD6DE" />

        <circle cx="1" cy="-35" r="4" fill="#D6E2E8" />
        <circle cx="38" cy="-7" r="4" fill="#D6E2E8" />
        <circle cx="8" cy="36" r="4" fill="#D6E2E8" />
        <circle cx="-36" cy="-8" r="4" fill="#D6E2E8" />
      </g>

      {!compact && (
        <>
          <text x="212" y="112" fontFamily="Arial, Helvetica, sans-serif" fontSize="70" fontWeight="700" letterSpacing="-2.4">
            <tspan fill="#123A5A">Neuro</tspan>
            <tspan fill="#1B7F8C">avalia</tspan>
          </text>
          <text x="216" y="149" fontFamily="Arial, Helvetica, sans-serif" fontSize="15" fontWeight="700" letterSpacing="5.2" fill="#7E929F">
            AVALIAÇÃO NEUROPSICOLÓGICA
          </text>
        </>
      )}
    </svg>
  );
}
