type Subdomain = { scale: string; domain: string; label: string; v_scale: number; display_code: string }

export function VinelandSubdomainProfile({ rows, form }: { rows: Subdomain[]; form?: string }) {
  const groups = [
    { code: 'COM', label: 'Comunicação', scales: ['rec', 'exp', 'esc'] },
    { code: 'AVD', label: 'Atividades da Vida Diária', scales: form === 'professores' ? ['pes', 'num', 'cme'] : ['pes', 'dom', 'com'] },
    { code: 'SOC', label: 'Socialização', scales: ['rin', 'bri', 'enf'] },
    { code: 'HMOT', label: 'Habilidades Motoras', scales: ['cmg', 'cmf'] },
  ]
  const columns = groups.flatMap(group => group.scales.map(scale => ({ scale, row: rows.find(row => row.scale === scale) })))
  const y = (score: number) => 340 - (score - 1) * 12
  const segments: string[][] = [[]]
  columns.forEach(({ row }, index) => {
    if (row) segments[segments.length - 1].push(`${70 + index * 44},${y(row.v_scale)}`)
    else if (segments[segments.length - 1].length) segments.push([])
  })
  return <div className="overflow-x-auto">
    <svg viewBox="0 0 600 385" role="img" aria-label="Perfil de escala-v dos subdomínios agrupados por domínio" className="mx-auto w-full min-w-[580px] max-w-4xl">
      {groups.map((group, index) => { const x = 48 + index * 132; const width = group.scales.length * 44; return <g key={group.code}>
        <title>{group.label}</title><rect x={x} y="15" width={width} height="30" fill="#eff4f8" stroke="#94a3b8" /><text x={x + width / 2} y="34" textAnchor="middle" fontSize="11">{group.code}</text><line x1={x} x2={x} y1="45" y2="340" stroke="#94a3b8" />
      </g> })}
      {Array.from({ length: 24 }, (_, i) => i + 1).map(score => { const reference = [15, 12, 9, 6].includes(score); return <g key={score}>
        <line x1="48" x2="532" y1={y(score)} y2={y(score)} stroke={reference ? '#475569' : '#e2e8f0'} strokeDasharray={reference ? '6 4' : undefined} strokeWidth={reference ? 1.5 : 1} /><text x="39" y={y(score) + 4} textAnchor="end" fontSize="10">{score}</text>
      </g> })}
      {segments.filter(segment => segment.length).map((points, i) => <polyline key={i} points={points.join(' ')} fill="none" stroke="#0e7490" strokeWidth="2.5" />)}
      {columns.map(({ scale, row }, index) => { const x = 70 + index * 44; return <g key={scale}>
        <text x={x} y="357" textAnchor="middle" fontSize="10">{scale === 'com' ? 'CMD' : scale.toUpperCase()}</text>
        {row ? <><title>{row.display_code} · {row.label}: {row.v_scale}</title><circle cx={x} cy={y(row.v_scale)} r="3" fill="#0e7490" /><text x={x} y={y(row.v_scale) - 7} textAnchor="middle" fontSize="10">{row.v_scale}</text></> : <text x={x} y="374" textAnchor="middle" fontSize="9">—</text>}
      </g> })}
    </svg>
    <p className="text-sm text-slate-600">COM: Comunicação · AVD: Atividades da Vida Diária · SOC: Socialização · HMOT: Habilidades Motoras. Tracejados em 15, 12, 9 e 6 são referências visuais, não pontos de corte diagnósticos. — = ausente/sem norma; interrompe o traçado.</p>
  </div>
}
