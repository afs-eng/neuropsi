'use client'

import { Input } from '@/components/ui/input'
import { thcpGroupTotal, type THCPGroup, type THCPItemDefinition, type THCPItemForm, type THCPProtocol } from '@/lib/thcp-protocol'

interface ProtocolProps {
  protocol: THCPProtocol
  items: THCPItemForm
  onChange: (group: THCPGroup, key: string, field: 'answer' | 'score', value: string) => void
}

function Choice({ name, value, selected, label, onChange }: { name: string; value: number; selected: string; label?: string; onChange: (value: string) => void }) {
  return <label className="relative cursor-pointer">
    <input type="radio" name={name} value={value} checked={selected === String(value)} onChange={e => onChange(e.target.value)} required className="peer sr-only" aria-label={label} />
    <span className="flex min-h-11 min-w-11 items-center justify-center rounded-md border border-slate-200 bg-white px-2 text-sm tabular-nums hover:border-blue-400 peer-checked:border-blue-600 peer-checked:bg-blue-600 peer-checked:text-white peer-focus-visible:ring-2 peer-focus-visible:ring-blue-600 peer-focus-visible:ring-offset-2 peer-disabled:cursor-not-allowed peer-disabled:opacity-50 sm:min-h-8 sm:min-w-8">{label ? '∅' : value}</span>
  </label>
}

function ProtocolRow({ group, item, items, onChange }: Omit<ProtocolProps, 'protocol'> & { group: THCPGroup; item: THCPItemDefinition }) {
  const response = items[group]?.[item.key] || { answer: '', score: '' }
  const id = `thcp-${group}-${item.key}`
  const change = (field: 'answer' | 'score', value: string) => onChange(group, item.key, field, value)
  if (!item.options.length && !item.score_options) {
    return <div className="flex items-center justify-between gap-3 border-b border-slate-100 py-2 last:border-0">
      <label htmlFor={id} className="text-sm text-slate-700">{item.label}</label>
      <div className="flex shrink-0 items-center gap-2"><Input id={id} name={id} aria-label={`${item.label} — pontos`} autoComplete="off" type="number" inputMode="numeric" min={0} max={item.max_score} step={1} required value={response.score} onChange={e => change('score', e.target.value)} className="h-11 w-16 border-slate-300 bg-white text-center tabular-nums sm:h-9" /><span className="text-xs text-slate-500">/ {item.max_score}</span></div>
    </div>
  }
  return <fieldset className="min-w-0 border-b border-slate-100 py-2 last:border-0">
    <legend className="sr-only">{item.label}</legend>
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      <span className="w-6 shrink-0 text-sm font-medium text-slate-700" aria-hidden="true">{item.label}</span>
      {item.options.length > 0 && <div className="flex flex-wrap gap-1" role="group" aria-label="Alternativa respondida">
        {item.options.map(option => <Choice key={option} name={`${id}-answer`} value={option} selected={response.answer} onChange={value => change('answer', value)} />)}
        <Choice name={`${id}-answer`} value={0} selected={response.answer} label="Sem resposta" onChange={value => change('answer', value)} />
      </div>}
      <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Pontuação do item">
        <span className="text-xs text-slate-500">Pontos</span>
        {(item.score_options || [0, 1]).map(option => <Choice key={option} name={`${id}-score`} value={option} selected={response.score} onChange={value => change('score', value)} />)}
      </div>
    </div>
  </fieldset>
}

function Subtotal({ title, value, maximum }: { title: string; value: number | null; maximum: number }) {
  return <div className="mt-3 flex items-center justify-between gap-3 rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-900"><span className="font-semibold">{title}</span><span className="tabular-nums"><strong>{value ?? '—'}</strong> / {maximum}</span></div>
}

export function THCPHPMFields(props: ProtocolProps) {
  const { protocol, items } = props
  const first = protocol.hpm_i
  const rows = (definitions: THCPItemDefinition[]) => definitions.map(item => <ProtocolRow key={item.key} group="hpm_i" item={item} {...props} />)
  return <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
    <div className="min-w-0">
      <h3 className="mb-3 text-sm font-semibold text-slate-900">Exercício I <span className="ml-2 text-xs font-normal text-slate-500">Máx. 22 pontos</span></h3>
      <div className="rounded-lg border border-blue-100 px-3"><h4 className="-mx-3 rounded-t-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-900">Labirinto · 0 a 4 pontos</h4>{rows(first.slice(0, 1))}</div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div className="min-w-0 rounded-lg border border-blue-100 px-3"><h4 className="-mx-3 rounded-t-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-900">Cópia · 0 a 2 pontos cada</h4>{rows(first.slice(1, 8))}</div>
        <div className="min-w-0 rounded-lg border border-blue-100 px-3"><h4 className="-mx-3 rounded-t-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-900">Figura complexa · 0 a 1 ponto cada</h4>{rows(first.slice(8))}</div>
      </div>
      <Subtotal title="Total Exercício I" value={thcpGroupTotal(protocol, items, 'hpm_i')} maximum={22} />
    </div>
    <div className="min-w-0 lg:border-l lg:border-slate-100 lg:pl-5">
      <h3 className="mb-1 text-sm font-semibold text-slate-900">Exercício II <span className="ml-2 text-xs font-normal text-slate-500">Máx. 8 pontos</span></h3>
      {protocol.hpm_ii.map(item => <ProtocolRow key={item.key} group="hpm_ii" item={item} {...props} />)}
      <Subtotal title="Total Exercício II" value={thcpGroupTotal(protocol, items, 'hpm_ii')} maximum={8} />
    </div>
  </div>
}

export function THCPGroupFields({ group, ...props }: ProtocolProps & { group: 'linguagem' | 'pq' | 'memoria' }) {
  return <div>{props.protocol[group].map(item => <ProtocolRow key={item.key} group={group} item={item} {...props} />)}</div>
}
