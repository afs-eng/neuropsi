export interface VinelandNormativeScore {
  code: string; scale: string; label: string; raw_score: number | null; standard_score: number | null
  percentile: string | null; confidence_interval: number[] | null; classification: string | null
  unavailable_reason: string | null; v_scale?: number | null; sum_standard_scores?: number | null
  sum_v_scale?: number | null
}

interface Strength { scale: string; label?: string; score?: number | null; standard_score: number | null; difference: number | null; critical_value: number | null; finding: string; base_rate: string | null }
interface Pair { first: string; second: string; first_score?: number | null; second_score?: number | null; relation?: string | null; difference: number | null; critical_value: number | null; significant: boolean | null; base_rate: string | null; within_domain?: boolean }

export interface VinelandNormativeResultsData {
  form_label?: string; table_codes?: string; form?: string
  form_level?: string
  error?: string; normative_scoring: boolean; confidence_level: number; significance_level: number
  age_months: number; population: string; adaptive: VinelandNormativeScore[]; cca: VinelandNormativeScore
  behavior: VinelandNormativeScore[]; mean_standard_score: number | null; mean_domain_count: number
  strengths: Strength[]
  pairs: Pair[]
  subdomains?: { scale: string; display_code: string; domain: string; label: string; raw_score: number; v_scale: number; age_equivalent: string | null; growth_value: number | null }[]
  subdomain_strengths?: Strength[]; subdomain_pairs?: Pair[]; subdomain_mean_v_scale?: number | null; subdomain_count?: number
}

const number = (value: number | null) => value === null ? '—' : value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
const cell = 'border border-slate-200 px-3 py-3'
const heading = 'bg-blue-50 text-blue-950'
const scaleLabel = (code: string) => code === 'com' ? 'CMD' : code.toUpperCase()

function pairTable(rows: Pair[]) {
  return <div className="overflow-x-auto"><table className="w-full text-sm tabular-nums"><thead className={heading}><tr>{['Comparação', 'A', 'Relação', 'B', 'A − B', 'Valor crítico', 'Significativa', 'Taxa de base'].map(text => <th key={text} scope="col" className={cell}>{text}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={`${row.first}-${row.second}`}><th scope="row" className={cell}>{scaleLabel(row.first)} – {scaleLabel(row.second)}</th><td className={cell}>{row.first_score ?? '—'}</td><td className={cell}>{row.relation ?? '—'}</td><td className={cell}>{row.second_score ?? '—'}</td><td className={cell}>{number(row.difference)}</td><td className={cell}>{number(row.critical_value)}</td><td className={cell}>{row.significant === null ? '—' : row.significant ? 'Sim' : 'Não'}</td><td className={cell}>{row.base_rate ?? '—'}</td></tr>)}</tbody></table></div>
}

export function VinelandNormativeResults({ result }: { result: VinelandNormativeResultsData }) {
  if (result.error) return <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-5">Correção normativa indisponível: {result.error}</p>
  const rows = [...result.adaptive.slice(0, 3), result.cca, ...result.adaptive.slice(3)]
  const extensive = result.form_level === 'extensivo'
  const y = (score: number) => extensive ? 300 - score * 1.75 : 300 - (score - 20) * 2
  return <>
    <aside className="rounded-xl border border-blue-200 bg-blue-50 p-5 text-sm text-blue-950">
      <h2 className="font-semibold">Correção normativa — {result.population} · IC {result.confidence_level}%</h2>
      <p>Tabelas {result.table_codes || 'C.3, C.4, C.5 e E.2'} de {result.form_label || 'Pais/Cuidadores — Níveis de Domínio'}. Idade: {Math.floor(result.age_months / 12)} anos e {result.age_months % 12} meses.</p>
      <p>Requer revisão clínica; não inclui automaticamente o registro no laudo. Resultados sem norma para a idade permanecem indisponíveis.</p>
    </aside>
    {extensive && <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="font-semibold">Subdomínios — perfil de escala-v</h2>
      <p className="text-sm">Escala-v: 1–24, média normativa 15. CMD = Comunidade; COM = Comunicação. Equivalente etário (anos:meses) não é idade global de desenvolvimento ou diagnóstico.</p>
      <div className="overflow-x-auto"><table className="w-full text-sm tabular-nums"><thead className={heading}><tr>{['Domínio', 'Subdomínio', 'Bruto', 'Escala-v', 'Equiv. etário (a:m)', 'VEC'].map(label => <th key={label} scope="col" className={cell}>{label}</th>)}</tr></thead><tbody>{result.subdomains?.map(row => <tr key={row.scale}><td className={cell}>{row.domain}</td><th scope="row" className={cell}>{row.label} ({row.display_code})</th><td className={cell}>{row.raw_score}</td><td className={cell}>{row.v_scale}</td><td className={cell}>{row.age_equivalent ?? '—'}</td><td className={cell}>{row.growth_value ?? '—'}</td></tr>)}</tbody></table></div>
      {['COM', 'AVD', 'SOC', 'HMOT'].map(domain => {
        const subdomains = result.subdomains?.filter(row => row.domain === domain) || []
        return <div key={domain} className="space-y-2"><h3 className="font-medium">{result.adaptive.find(row => row.scale === domain)?.label || domain}</h3>{subdomains.length ? subdomains.map(row => <div key={row.scale}><div className="flex justify-between text-sm"><span>{row.display_code} · {row.label}</span><strong>{row.v_scale}</strong></div><div aria-hidden="true" className="relative h-3 bg-slate-100"><div className="h-3 bg-cyan-700" style={{ width: `${row.v_scale / 24 * 100}%` }} /><span className="absolute inset-y-0 border-l-2 border-slate-800" style={{ left: '62.5%' }} /></div></div>) : <p className="text-sm">Não informado ou não aplicável à idade; não representado como zero.</p>}</div>
      })}
    </section>}
    <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-4 font-semibold">Resumo da pontuação adaptativa</h2>
      <table className="w-full text-sm tabular-nums"><thead className={heading}><tr>{['Domínio', extensive ? 'Soma de entrada' : 'Bruto', 'Escore padrão', 'IC 95%', 'Percentil', 'Nível adaptativo'].map(text => <th key={text} scope="col" className={cell}>{text}</th>)}</tr></thead>
          <tbody>{rows.map(row => <tr key={row.scale}><th scope="row" className={`${cell} text-left`}>{row.label} ({row.scale})</th><td className={cell}>{extensive ? row.sum_standard_scores ?? row.sum_v_scale ?? '—' : row.raw_score ?? '—'}</td><td className={`${cell} font-bold`}>{row.standard_score ?? '—'}</td><td className={cell}>{row.confidence_interval?.join(' – ') ?? '—'}</td><td className={cell}>{row.percentile ?? '—'}</td><td className={cell}>{row.classification ?? row.unavailable_reason}</td></tr>)}</tbody>
      </table>
      <p className="mt-3 text-sm text-slate-600">CCA: soma dos escores padrão de COM + AVD + SOC = {result.cca.sum_standard_scores ?? '—'}. Habilidades Motoras não entra no CCA.</p>
      {extensive && <p className="text-sm text-slate-600">Soma de entrada: escala-v por domínio; para CCA, escores padrão. Não são brutos dos Níveis de Domínio.</p>}
    </section>
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="font-semibold">Perfil dos escores padrão</h2>
      <p className="text-sm text-slate-600">Marcadores: escores padrão. Hastes: intervalos de confiança de 95%. Média normativa: 100.</p>
      <svg viewBox="0 0 600 340" role="img" aria-label="Perfil dos escores padrão COM, AVD, SOC, CCA e HMOT com intervalos de confiança de 95%" className="mx-auto w-full max-w-3xl">
        {[20, 40, 60, 80, 100, 120, 140, 160].map(score => <g key={score}><line x1="50" x2="570" y1={y(score)} y2={y(score)} stroke={score === 100 ? '#1d4ed8' : '#cbd5e1'} strokeDasharray={score === 100 ? '5 4' : undefined} /><text x="40" y={y(score) + 4} textAnchor="end" fontSize="12">{score}</text></g>)}
        {rows.map((row, index) => { const x = 100 + index * 105; return <g key={row.scale}>
          <text x={x} y="325" textAnchor="middle" fontSize="13">{row.scale}</text>
          {row.standard_score !== null ? <><line x1={x} x2={x} y1={y(row.confidence_interval?.[0] ?? row.standard_score)} y2={y(row.confidence_interval?.[1] ?? row.standard_score)} stroke="#1d4ed8" strokeWidth="3" /><circle cx={x} cy={y(row.standard_score)} r="5" fill="#082d5f" /><text x={x + 10} y={y(row.standard_score) + 4} fontSize="12">{row.standard_score}</text></> : <text x={x} y="290" textAnchor="middle" fontSize="11">{row.unavailable_reason === 'Não informado' ? 'Não informado' : 'Sem norma'}</text>}
        </g> })}
      </svg>
    </section>
    {result.behavior.length > 0 && <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-4 font-semibold">Comportamento mal adaptativo — Tabela E.{result.form === 'entrevista' ? '1' : result.form === 'professores' ? '3' : '2'}</h2>
      <table className="w-full text-sm"><thead className={heading}><tr><th className={cell}>Seção</th><th className={cell}>Bruto</th><th className={cell}>Escala-v</th><th className={cell}>Situação</th></tr></thead><tbody>{result.behavior.map(row => <tr key={row.code}><th className={`${cell} text-left`}>{row.scale === 'internalizante' ? 'Internalizante (A)' : 'Externalizante (B)'}</th><td className={cell}>{row.raw_score ?? '—'}</td><td className={cell}>{row.v_scale ?? '—'}</td><td className={cell}>{row.unavailable_reason ?? 'Calculado'}</td></tr>)}</tbody></table>
      <p className="mt-3 text-sm">Maior pontuação indica maior frequência dos comportamentos relatados, não melhor habilidade adaptativa.</p>
    </section>}
    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="font-semibold">Página de Análise — p = 0,05</h2>
      <p className="text-sm">Média dos escores padrão: {number(result.mean_standard_score)} ({result.mean_domain_count} domínios com conversão disponível). A significância estatística não equivale a diagnóstico.</p>
      <h3 className="font-medium">Análise de força / fraqueza — {result.form === 'entrevista' ? 'B' : result.form === 'professores' ? 'D' : 'C'}.4</h3>
      <div className="overflow-x-auto"><table className="w-full text-sm tabular-nums"><thead className={heading}><tr>{['Domínio', 'Escore padrão', 'Diferença da média', 'Valor crítico', 'Força / fraqueza', 'Taxa de base'].map(text => <th key={text} className={cell}>{text}</th>)}</tr></thead><tbody>{result.strengths.map(row => <tr key={row.scale}><th className={cell}>{row.scale}</th><td className={cell}>{number(row.standard_score)}</td><td className={cell}>{number(row.difference)}</td><td className={cell}>{number(row.critical_value)}</td><td className={cell}>{row.finding}</td><td className={cell}>{row.base_rate ?? '—'}</td></tr>)}</tbody></table></div>
      <h3 className="font-medium">Comparação das diferenças emparelhadas — {result.form === 'entrevista' ? 'B' : result.form === 'professores' ? 'D' : 'C'}.5</h3>
      {extensive ? pairTable(result.pairs) : <div className="overflow-x-auto"><table className="w-full text-sm tabular-nums"><thead className={heading}><tr>{['Domínios', 'Diferença', 'Valor crítico', 'Significância', 'Taxa de base'].map(text => <th key={text} className={cell}>{text}</th>)}</tr></thead><tbody>{result.pairs.map(row => <tr key={`${row.first}-${row.second}`}><th className={cell}>{row.first} – {row.second}</th><td className={cell}>{number(row.difference)}</td><td className={cell}>{number(row.critical_value)}</td><td className={cell}>{row.significant === null ? '—' : row.significant ? 'Sim' : 'Não'}</td><td className={cell}>{row.base_rate ?? '—'}</td></tr>)}</tbody></table></div>}
      <p className="text-xs text-slate-600">Taxas de base em faixas conforme as tabelas, não percentis exatos. — = não aplicado ou sem conversão normativa.</p>
    </section>
    {extensive && <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="font-semibold">Análise dos subdomínios — p = 0,05</h2>
      <p className="text-sm">Média de escala-v {number(result.subdomain_mean_v_scale ?? null)} · {result.subdomain_count} subdomínios disponíveis. Decisões calculadas antes de arredondar as diferenças.</p>
      <div className="overflow-x-auto"><table className="w-full text-sm"><thead className={heading}><tr>{['Subdomínio', 'Escala-v', 'Diferença da média', 'Valor crítico', 'Resultado', 'Taxa de base'].map(label => <th key={label} scope="col" className={cell}>{label}</th>)}</tr></thead><tbody>{result.subdomain_strengths?.map(row => <tr key={row.scale}><th scope="row" className={cell}>{scaleLabel(row.scale)} · {row.label}</th><td className={cell}>{row.score ?? '—'}</td><td className={cell}>{number(row.difference)}</td><td className={cell}>{number(row.critical_value)}</td><td className={cell}>{row.finding}</td><td className={cell}>{row.base_rate ?? '—'}</td></tr>)}</tbody></table></div>
      <h3 className="font-medium">Comparações no mesmo domínio</h3>
      {pairTable(result.subdomain_pairs?.filter(row => row.within_domain) || [])}
      <details className="space-y-3 rounded-lg border p-3"><summary className="cursor-pointer font-medium">Comparações adicionais entre domínios diferentes</summary><p className="text-sm">Análise exploratória de uma aplicação; múltiplas comparações exigem cautela. Não representa mudança longitudinal ou diagnóstico.</p>{pairTable(result.subdomain_pairs?.filter(row => !row.within_domain) || [])}</details>
      <p className="text-sm">Taxas de base limitadas pelos limiares publicados; ausências não são zero nem interpoladas. Comportamento e itens críticos exigem conferência no protocolo original.</p>
    </section>}
  </>
}
