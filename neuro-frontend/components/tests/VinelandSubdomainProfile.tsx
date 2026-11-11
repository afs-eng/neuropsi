import { useId } from 'react'

type Subdomain = { scale: string; domain: string; label: string; v_scale: number; display_code: string }

export function VinelandSubdomainProfile({ rows, form }: { rows: Subdomain[]; form?: string }) {
  const gridId = useId()
  const groups = [
    { code: 'COM', label: 'Comunicação', lines: ['COMUNICAÇÃO'], scales: ['rec', 'exp', 'esc'] },
    { code: 'AVD', label: 'Atividades da Vida Diária', lines: ['ATIVIDADES DE VIDA', 'DIÁRIA'], scales: form === 'professores' ? ['pes', 'num', 'cme'] : ['pes', 'dom', 'com'] },
    { code: 'SOC', label: 'Socialização', lines: ['SOCIALIZAÇÃO'], scales: ['rin', 'bri', 'enf'] },
    { code: 'HMOT', label: 'Habilidades Motoras', lines: ['HABILIDADES', 'MOTORAS'], scales: ['cmg', 'cmf'] },
  ]
  const columns = groups.flatMap(group => group.scales.map(scale => ({ scale, row: rows.find(row => row.scale === scale) })))
  const y = (score: number) => 364 - (score - 1) * 12
  const segments: string[][] = [[]]
  columns.forEach(({ row }, index) => {
    if (row) segments[segments.length - 1].push(`${70 + index * 44},${y(row.v_scale)}`)
    else if (segments[segments.length - 1].length) segments.push([])
  })
  return <div className="overflow-x-auto">
    <svg viewBox="12 0 556 390" role="img" aria-label="Perfil de escala-v dos subdomínios agrupados por domínio" className="w-full min-w-[580px]">
      <defs><pattern id={gridId} x="48" y="82" width="44" height="12" patternUnits="userSpaceOnUse"><circle cx="22" cy="6" r="1.2" fill="#143d70" /></pattern></defs>
      <rect x="12" y="0" width="556" height="370" fill="white" stroke="#cbd5e1" />
      <rect x="12" y="0" width="556" height="76" fill="#EFF6FF" stroke="#cbd5e1" />
      <line x1="12" x2="568" y1="22" y2="22" stroke="#cbd5e1" />
      <text x="290" y="15" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#082d5f">Subdomínio do Perfil da Pontuação da Vineland-3</text>
      {groups.map((group, index) => { const x = 48 + index * 132; const width = group.scales.length * 44; return <g key={group.code}>
        <title>{group.label}</title><rect x={x} y="22" width={width} height="34" fill="#EFF6FF" stroke="#cbd5e1" />
        <text x={x + width / 2} y={group.lines.length === 1 ? 43 : 36} textAnchor="middle" fontSize="10" fontWeight="bold" fill="#082d5f">{group.lines.map((line, i) => <tspan key={line} x={x + width / 2} dy={i ? 12 : 0}>{line}</tspan>)}</text>
      </g> })}
      <rect x="12" y={y(15) - 6} width="556" height="12" fill="#EFF6FF" />
      <rect x="48" y="82" width="484" height="288" fill={`url(#${gridId})`} aria-hidden="true" />
      {Array.from({ length: 12 }, (_, index) => <line key={index} x1={48 + index * 44} x2={48 + index * 44} y1="76" y2="370" stroke="#cbd5e1" strokeWidth="0.7" />)}
      {Array.from({ length: 24 }, (_, i) => i + 1).map(score => { const reference = [15, 12, 9, 6].includes(score); return <g key={score}>
        {reference && <line x1="48" x2="532" y1={y(score)} y2={y(score)} stroke="#2278b5" strokeDasharray="6 4" strokeWidth="1" />}<text x="39" y={y(score) + 4} textAnchor="end" fontSize="10" fill="#082d5f">{score}</text><text x="541" y={y(score) + 4} fontSize="10" fill="#082d5f">{score}</text>
      </g> })}
      <line x1="12" x2="568" y1="370" y2="370" stroke="#cbd5e1" />
      {segments.filter(segment => segment.length).map((points, i) => <polyline key={i} points={points.join(' ')} fill="none" stroke="#0e7490" strokeWidth="2.5" />)}
      {columns.map(({ scale, row }, index) => { const x = 70 + index * 44; return <g key={scale}>
        <rect x={x - 22} y="56" width="44" height="20" fill="#EFF6FF" stroke="#cbd5e1" />
        <text x={x} y="70" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#082d5f">{scale === 'com' ? 'CMD' : scale.toUpperCase()}</text>
        {row ? <><title>{row.display_code} · {row.label}: {row.v_scale}</title><circle cx={x} cy={y(row.v_scale)} r="3" fill="#0e7490" /><text x={x} y={y(row.v_scale) - 7} textAnchor="middle" fontSize="10">{row.v_scale}</text></> : <text x={x} y="383" textAnchor="middle" fontSize="9">—</text>}
      </g> })}
    </svg>
    <p className="text-sm text-slate-600">COM: Comunicação · AVD: Atividades da Vida Diária · SOC: Socialização · HMOT: Habilidades Motoras. Pontos pequenos: grade de referência; linha e marcadores maiores: resultados. Faixa azul: média normativa 15. Tracejados em 15, 12, 9 e 6 são referências visuais, não pontos de corte diagnósticos. — = ausente/sem norma; interrompe o traçado.</p>
  </div>
}
