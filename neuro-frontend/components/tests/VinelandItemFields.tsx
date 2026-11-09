'use client'

import { useState } from 'react'

export interface VinelandItemProtocol {
  id: string
  title: string
  description: string
  legend: Record<string, string>
  warning: string
  supports_estimates?: boolean
  item_observations?: boolean
  domains: { code: string; label: string; behavior_problems?: boolean; pages?: number[]; items: { id: string; text: string; allowed_responses?: string[]; hint?: string }[] }[]
}
export type VinelandItemResponses = Record<string, Record<string, { response: string; observation: string; estimated?: boolean }>>

export function resolveVinelandItemProtocol(current: VinelandItemProtocol, legacy: VinelandItemProtocol, savedId?: string, savedItems = false) {
  if (!savedItems) return current
  if (!savedId || savedId === legacy.id) return legacy
  if (savedId === current.id) return current
  throw new Error('Banco de perguntas desta aplicação não reconhecido. Preserve o registro original.')
}

export function vinelandResponseError(protocol: VinelandItemProtocol, responses: VinelandItemResponses) {
  for (const domain of protocol.domains) {
    for (const item of domain.items) {
      const entry = responses[domain.code]?.[item.id]
      const allowed = item.allowed_responses || Object.keys(protocol.legend)
      if (entry?.response && !allowed.includes(entry.response)) return `${domain.label}, item ${item.id}: use ${allowed.join(', ')}.`
      if (entry?.estimated && !entry.response) return `${domain.label}, item ${item.id}: Est. exige uma pontuação.`
    }
  }
  return ''
}

export function restoreVinelandObservations(protocol: VinelandItemProtocol, responses: VinelandItemResponses, observations?: string) {
  if (observations !== undefined) return observations
  return protocol.domains.flatMap(domain => domain.items.flatMap(item => {
    const note = responses[domain.code]?.[item.id]?.observation
    return note ? [`${domain.label} — item ${item.id}: ${note}`] : []
  })).join('\n')
}

interface Props {
  protocol: VinelandItemProtocol
  responses: VinelandItemResponses
  onChange: (responses: VinelandItemResponses) => void
  observations: string
  onObservationsChange: (observations: string) => void
  disabled: boolean
}

export function VinelandItemFields({ protocol, responses, onChange, observations, onObservationsChange, disabled }: Props) {
  const [activeDomain, setActiveDomain] = useState(protocol.domains[0].code)
  const domain = protocol.domains.find(entry => entry.code === activeDomain) || protocol.domains[0]
  const total = protocol.domains.reduce((count, entry) => count + entry.items.length, 0)
  const answered = protocol.domains.reduce((count, entry) => count + entry.items.filter(item =>
    Boolean(responses[entry.code]?.[item.id]?.response) && (item.allowed_responses || Object.keys(protocol.legend)).includes(responses[entry.code][item.id].response)
  ).length, 0)

  function update(itemId: string, changes: Partial<VinelandItemResponses[string][string]>) {
    onChange({ ...responses, [domain.code]: {
      ...responses[domain.code], [itemId]: {
        ...responses[domain.code]?.[itemId],
        observation: responses[domain.code]?.[itemId]?.observation ?? '',
        response: responses[domain.code]?.[itemId]?.response ?? '',
        ...changes,
      },
    } })
  }

  return <section className="space-y-5 rounded-xl border bg-white p-4 sm:p-6">
    <p className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">{protocol.warning} {!protocol.supports_estimates && 'Faixas etárias e subdomínios deste banco ainda não confirmados; não aplicar automaticamente os dos formulários extensivos.'}</p>
    <nav aria-label="Domínios do registro Vineland" className="flex flex-wrap gap-2">
      {protocol.domains.map(entry => <button key={entry.code} type="button" aria-pressed={domain.code === entry.code}
        className={`min-h-11 touch-manipulation rounded-md border px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-700 ${domain.code === entry.code ? 'border-cyan-800 bg-cyan-800 text-white hover:bg-cyan-900' : 'border-slate-300 bg-white text-slate-800 hover:bg-slate-100'}`}
        onClick={() => setActiveDomain(entry.code)}>{entry.label}</button>)}
    </nav>
    <div className="space-y-3 border-b pb-4">
      <p className="font-semibold">{protocol.title}</p>
      <p className="max-w-prose text-sm leading-relaxed text-slate-700">{protocol.description}</p>
      <dl aria-label="Legenda de pontuação" className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
        {['2', '1', '0', 'N', 'D'].filter(code => code in protocol.legend).map(code => <div key={code} className="flex gap-2"><dt className="font-bold">{code}</dt><dd>{domain.behavior_problems && code === '2' ? 'Frequentemente' : protocol.legend[code]}</dd></div>)}
      </dl>
      {protocol.supports_estimates && <p className="text-sm text-slate-700">Est. = pontuação estimada. Itens binários aceitam somente 0 ou 2. Formulário de níveis de domínio a partir de 3 anos; motor opcional até 9 anos. Consulte os critérios das páginas 2 e 15 do PDF.</p>}
      {domain.behavior_problems && <p className="font-medium text-amber-950">Nesta seção, maior pontuação significa mais problemas de comportamento, não maior adaptação. Itens críticos devem ser avaliados individualmente pelo profissional, sem soma diagnóstica.</p>}
    </div>
    <h2 id="vineland-active-domain" className="text-xl font-semibold text-slate-900">{domain.label}</h2>
    {domain.pages && <p className="text-sm text-slate-600">Referência: páginas {domain.pages.join(' e ')} do formulário.</p>}
    <p role="status" className="text-sm text-slate-600">{answered} de {total} itens transcritos respondidos; {total - answered} pendentes. Campos vazios não são zero. O registro parcial pode ser salvo. {protocol.supports_estimates && 'As pendências incluem seções opcionais ainda não preenchidas; isso não indica aplicação incompleta dessas seções.'}</p>
    <div className="overflow-x-auto">
      <table aria-labelledby="vineland-active-domain" className="w-full text-left text-sm">
        <thead><tr className="border-b"><th scope="col" className="p-2">Nº</th><th scope="col" className="p-2">Pergunta</th><th scope="col" className="p-2 text-right">Resposta</th>{protocol.supports_estimates && <th scope="col" className="p-2">Est.</th>}</tr></thead>
        <tbody>{domain.items.map(item => {
          const entry = responses[domain.code]?.[item.id]
          const value = entry?.response ?? ''
          const allowed = item.allowed_responses || ['2', '1', '0', 'N', 'D']
          const invalid = value !== '' && !allowed.includes(value)
          const id = `vineland-item-${domain.code}-${item.id}`
          return <tr key={item.id} className="border-b align-top">
            <td className="p-2 tabular-nums text-slate-600">{item.id}</td>
            <th scope="row" className="min-w-[15rem] p-2 font-normal leading-relaxed">
              <label htmlFor={id}>{item.text}</label>
              {item.allowed_responses?.length === 2 && <p className="mt-1 text-xs font-medium text-slate-700">Somente 2 = Sim ou 0 = Não.</p>}
              {item.hint && <p className="mt-1 text-sm text-slate-600">{item.hint}</p>}
              {protocol.item_observations && <details className="mt-2 text-sm"><summary className="cursor-pointer text-slate-600">Observação do item</summary><label htmlFor={`${id}-observation`} className="sr-only">{domain.label}, item {item.id}: observação</label><textarea id={`${id}-observation`} rows={2} maxLength={2000} disabled={disabled} value={entry?.observation ?? ''} onChange={event => update(item.id, { observation: event.target.value })} className="mt-2 w-full rounded-md border p-2" /></details>}
            </th>
            <td className="p-2 text-right">
              <input id={id} name={`${domain.code}.${item.id}.response`} type="text" maxLength={1} inputMode={protocol.supports_estimates ? 'numeric' : 'text'} pattern={item.allowed_responses ? `[${allowed.join('')}]` : '[210NnDd]'} autoComplete="off" spellCheck={false}
                aria-label={`${domain.label}, item ${item.id}: resposta`} aria-invalid={invalid} aria-describedby={invalid ? `${id}-error` : undefined}
                disabled={disabled} value={value} onChange={event => update(item.id, { response: event.target.value.toUpperCase(), ...(protocol.supports_estimates && event.target.value === '' ? { estimated: false } : {}) })}
                className={`h-11 w-12 rounded-md border text-center text-base uppercase focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-700 ${invalid ? 'border-red-600' : 'border-slate-300'}`} />
              {invalid && <p id={`${id}-error`} className="mt-1 text-xs text-red-800">Use {allowed.join(', ')}.</p>}
              {value === '' && <span className="mt-1 block text-xs text-slate-500">Pendente</span>}
            </td>
            {protocol.supports_estimates && <td className="p-2"><label className="flex min-h-11 min-w-11 items-center justify-center"><span className="sr-only">{domain.label}, item {item.id}: pontuação estimada</span><input type="checkbox" name={`${domain.code}.${item.id}.estimated`} checked={entry?.estimated ?? false} disabled={disabled || value === '' || invalid} onChange={event => update(item.id, { estimated: event.target.checked })} className="h-5 w-5" /></label></td>}
          </tr>
        })}</tbody>
      </table>
    </div>
    <div>
      <label htmlFor="vineland-general-observations" className="mb-2 block text-sm font-medium">Observações gerais (opcional)</label>
      <textarea id="vineland-general-observations" name="general_observations" rows={4} maxLength={10000} autoComplete="off"
        disabled={disabled} value={observations} onChange={event => onObservationsChange(event.target.value)}
        aria-describedby="vineland-general-observations-hint"
        className="w-full rounded-md border border-slate-300 p-3 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-700" />
      <p id="vineland-general-observations-hint" className="mt-1 text-xs text-slate-600">Campo único para todo o formulário, compartilhado entre os domínios.</p>
    </div>
  </section>
}
