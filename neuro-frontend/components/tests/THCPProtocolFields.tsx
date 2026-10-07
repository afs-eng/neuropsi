'use client'

import { Fragment } from 'react'
import { Input } from '@/components/ui/input'
import { validTHCPItem, type THCPGroup, type THCPItemForm, type THCPProtocol } from '@/lib/thcp-protocol'

interface ProtocolProps {
  protocol: THCPProtocol
  items: THCPItemForm
  onChange: (group: THCPGroup, key: string, field: 'score', value: string) => void
}

// Destaques visuais transcritos da foto ampliada de Linguagem, sem efeito na nota.
const LANGUAGE_HIGHLIGHTS: Record<string, number> = {
  '1': 2, '2': 3, '3': 1, '4': 1, '5': 1, '6': 1,
  '7': 1, '8': 3, '9': 2, '10': 4, '11': 3, '12': 3,
}

const GROUP_LABELS: Record<THCPGroup, string> = {
  hpm_i: 'HPM — Exercício I', hpm_ii: 'HPM — Exercício II',
  linguagem: 'Linguagem', memoria: 'Memória', pq: 'Pensamento Quantitativo',
}

export function THCPGroupFields({ group, protocol, items, onChange }: ProtocolProps & { group: THCPGroup }) {
  const hasReferences = protocol[group].some(item => item.options.length || item.score_options)
  return <table className="w-full table-fixed text-sm">
    <caption className="sr-only">{GROUP_LABELS[group]} — valores fixos de referência e notas editáveis</caption>
    <colgroup><col className={hasReferences ? 'w-[14%]' : 'w-[45%]'} /><col /><col className="w-[4.5rem]" /></colgroup>
    <thead><tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
      <th scope="col" colSpan={hasReferences ? 1 : 2} className="py-2 text-left font-medium">{hasReferences ? 'Item' : 'Descrição'}</th>
      {hasReferences && <th scope="col" className="py-2 text-left font-medium">Referência fixa</th>}
      <th scope="col" className="py-2 text-center font-semibold text-slate-700">Nota</th>
    </tr></thead>
    <tbody>{protocol[group].map((item, index) => {
      const response = items[group]?.[item.key] || { answer: '', score: '' }
      const id = `thcp-${group}-${item.key}-score`
      const references = item.options.length ? item.options : item.score_options || []
      const highlight = group === 'linguagem' ? LANGUAGE_HIGHLIGHTS[item.key] : null
      const invalid = response.score !== '' && !validTHCPItem(item, response)
      const error = Number(response.score) > item.max_score ? `Máximo ${item.max_score} ${item.max_score === 1 ? 'ponto' : 'pontos'}` : Number(response.score) < 0 ? 'Mínimo 0 pontos' : 'Nota inteira obrigatória'
      return <Fragment key={item.key}>
        {group === 'hpm_i' && [0, 1, 8].includes(index) && <tr><th scope="rowgroup" colSpan={3} className="bg-slate-50 px-1 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-500">{index === 0 ? 'Labirinto · 0–4 pontos' : index === 1 ? 'Cópia · 0–2 pontos cada' : 'Figura complexa · 0–1 ponto cada'}</th></tr>}
        <tr className="border-b border-slate-100 last:border-0">
          <th scope="row" colSpan={hasReferences ? 1 : 2} className="py-2 pr-1 text-left font-medium text-slate-700">{item.label}</th>
          {hasReferences && <td className="py-2 pr-2"><div className="inline-flex max-w-full flex-wrap overflow-hidden rounded-sm border border-slate-200 bg-slate-50">
            {references.map(value => <span key={value} data-reference-value={value} data-reference-highlight={value === highlight ? 'true' : undefined} aria-label={value === highlight ? `${value} — destaque fixo do protocolo` : undefined} className={`flex h-9 min-w-7 items-center justify-center border-r border-slate-200 px-1.5 text-base tabular-nums last:border-r-0 ${value === highlight ? 'bg-emerald-800 font-bold text-white' : 'font-medium text-slate-700'}`}>{value}</span>)}
          </div></td>}
          <td className="py-1.5 pl-1">
            <label htmlFor={id} className="sr-only">Nota — {GROUP_LABELS[group]}, item {item.label}</label>
            <Input id={id} name={id} data-thcp-note="true" aria-describedby={`${id}-hint${invalid ? ` ${id}-error` : ''}`} aria-invalid={invalid} autoComplete="off" type="number" inputMode="numeric" min={0} max={item.max_score} step={1} required value={response.score} onChange={e => onChange(group, item.key, 'score', e.target.value)} className={`h-11 w-full bg-white px-1 text-center text-base font-semibold tabular-nums ${invalid ? 'border-red-400 bg-red-50 text-red-900 focus-visible:ring-red-500' : 'border-slate-300 focus-visible:ring-teal-600'}`} />
            <span id={`${id}-hint`} className="mt-1 block text-center text-xs text-slate-500"><span className="sr-only">Nota inteira, mínimo 0, </span>máx. {item.max_score}<span className="sr-only"> pontos. Campo vazio não equivale a zero.</span></span>
            {invalid && <span id={`${id}-error`} role="alert" className="mt-1 block text-center text-xs font-medium leading-4 text-red-700">{error}</span>}
          </td>
        </tr>
      </Fragment>
    })}</tbody>
  </table>
}
