'use client'

import { type THCPGroup, type THCPItemDefinition, type THCPItemForm, type THCPProtocol } from '@/lib/thcp-protocol'

interface ProtocolProps {
  protocol: THCPProtocol
  items: THCPItemForm
  onChange: (group: THCPGroup, key: string, field: 'answer' | 'score', value: string) => void
}

const GROUP_ACCENTS: Record<THCPGroup, string> = {
  hpm_i: 'peer-checked:border-indigo-600 peer-checked:bg-indigo-600 peer-focus-visible:ring-indigo-600',
  hpm_ii: 'peer-checked:border-indigo-600 peer-checked:bg-indigo-600 peer-focus-visible:ring-indigo-600',
  linguagem: 'peer-checked:border-emerald-700 peer-checked:bg-emerald-700 peer-focus-visible:ring-emerald-700',
  memoria: 'peer-checked:border-sky-700 peer-checked:bg-sky-700 peer-focus-visible:ring-sky-700',
  pq: 'peer-checked:border-amber-700 peer-checked:bg-amber-700 peer-focus-visible:ring-amber-700',
}

function Choice({ name, value, selected, label, accent, onChange }: { name: string; value: number; selected: string; label?: string; accent: string; onChange: (value: string) => void }) {
  return <label className="relative cursor-pointer">
    <input type="radio" name={name} value={value} checked={selected === String(value)} onChange={e => onChange(e.target.value)} required className="peer sr-only" aria-label={label} />
    <span className={`flex min-h-11 min-w-11 items-center justify-center rounded-md border border-slate-200 bg-white px-2 text-sm font-medium tabular-nums hover:border-slate-400 peer-checked:text-white peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-disabled:cursor-not-allowed peer-disabled:opacity-50 sm:min-h-8 sm:min-w-8 ${accent}`}>{label ? '∅' : value}</span>
  </label>
}

function ProtocolRow({ group, item, items, onChange }: Omit<ProtocolProps, 'protocol'> & { group: THCPGroup; item: THCPItemDefinition }) {
  const response = items[group]?.[item.key] || { answer: '', score: '' }
  const id = `thcp-${group}-${item.key}`
  const change = (field: 'answer' | 'score', value: string) => onChange(group, item.key, field, value)
  const accent = GROUP_ACCENTS[group]
  const scoreOptions = item.score_options || Array.from({ length: item.max_score + 1 }, (_, index) => index)
  return <fieldset className="min-w-0 border-b border-slate-100 py-2 last:border-0">
    <legend className="sr-only">{item.label}</legend>
    <div className={`flex flex-wrap items-center gap-x-3 gap-y-2 ${item.options.length ? '' : 'justify-between'}`}>
      <span className={`${item.options.length ? 'w-6 shrink-0' : 'min-w-0 flex-1'} text-xs font-medium text-slate-700 sm:text-[13px]`} aria-hidden="true">{item.label}</span>
      {item.options.length > 0 && <div className="flex flex-wrap gap-1" role="group" aria-label="Alternativa respondida">
        {item.options.map(option => <Choice key={option} name={`${id}-answer`} value={option} selected={response.answer} accent={accent} onChange={value => change('answer', value)} />)}
        <Choice name={`${id}-answer`} value={0} selected={response.answer} label="Sem resposta" accent={accent} onChange={value => change('answer', value)} />
      </div>}
      <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Pontuação do item">
        {item.options.length > 0 && <span className="text-[11px] text-slate-500">Pts</span>}
        {scoreOptions.map(option => <Choice key={option} name={`${id}-score`} value={option} selected={response.score} accent={accent} onChange={value => change('score', value)} />)}
      </div>
    </div>
  </fieldset>
}

export function THCPGroupFields({ group, ...props }: ProtocolProps & { group: THCPGroup }) {
  return <div>{props.protocol[group].map((item, index) => <div key={item.key} className="border-b border-slate-100 last:border-0">
    {group === 'hpm_i' && [0, 1, 8].includes(index) && <h3 className="-mx-3 border-y border-slate-100 bg-slate-50 px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">{index === 0 ? 'Labirinto · 0–4 pontos' : index === 1 ? 'Cópia · 0–2 pontos cada' : 'Figura complexa · 0–1 ponto cada'}</h3>}
    <ProtocolRow group={group} item={item} {...props} />
  </div>)}</div>
}
