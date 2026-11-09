const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function load(react = React) {
  const filename = path.join(__dirname, 'VinelandItemFields.tsx');
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2018 },
  }).outputText;
  const mod = new Module(filename, module);
  mod.filename = filename;
  mod.paths = module.paths;
  const original = mod.require.bind(mod);
  mod.require = id => id === 'react' ? react : original(id);
  mod._compile(compiled, filename);
  return mod.exports;
}

const protocol = {
  id: 'partial', title: 'Vineland (edição não confirmada)', description: 'Descrição do instrumento.',
  warning: 'Banco parcial, sem conversão normativa ou laudo.',
  legend: { '2': 'Sim, normalmente', '1': 'Algumas vezes ou parcialmente', '0': 'Não, nunca', N: 'Não teve oportunidade', D: 'Desconhecido' },
  domains: [
    { code: 'comunicacao', label: 'Comunicação', items: ['1', '2', '3', '4'].map(id => ({ id, text: `Pergunta ${id}.` })) },
    { code: 'autonomia', label: 'Autonomia', items: [{ id: '1', text: 'Pergunta de autonomia.' }] },
  ],
};
const responses = {
  comunicacao: { '1': { response: '0', observation: 'Não confundir com vazio.' }, '2': { response: 'N', observation: '' }, '3': { response: 'D', observation: '' } },
  autonomia: { '1': { response: '', observation: 'Observação sem resposta.' } },
};
const { VinelandItemFields: Fields, isEmptyVinelandApplication, vinelandEntryMode, restoreVinelandObservations, resolveVinelandItemProtocol, vinelandResponseError } = load();
const render = (extra = {}) => renderToStaticMarkup(React.createElement(Fields, { protocol, responses, observations: restoreVinelandObservations(protocol, responses), onObservationsChange() {}, onChange() {}, disabled: false, ...extra }));

function elements(tree) {
  if (Array.isArray(tree)) return tree.flatMap(elements);
  if (!tree || typeof tree !== 'object') return [];
  return [tree, ...elements(tree.props?.children)];
}

function interactive(definition = protocol, initialResponses = responses, disabled = false) {
  let active;
  const { VinelandItemFields: Component } = load({ ...React, useState(initial) { return [active ?? initial, next => { active = next; }]; } });
  let data = structuredClone(initialResponses);
  let observations = restoreVinelandObservations(definition, data);
  return Object.assign(() => Component({ protocol: definition, responses: data, observations, onObservationsChange(next) { observations = next; }, onChange(next) { data = next; }, disabled }), { getResponses: () => data });
}

test('responses are single-character text inputs, never scoring selects or buttons', () => {
  const html = render();
  assert.equal((html.match(/maxLength="1"/g) || []).length, 4);
  assert.equal((html.match(/inputMode="text"/g) || []).length, 4);
  assert.doesNotMatch(html, /<select|type="radio"|type="number"/);
  assert.match(html, /pattern="\[210NnDd\]"/);
  assert.match(html, /scope="row"/);
});

test('description and legend precede the active domain heading inside the form', () => {
  const html = render();
  const heading = html.indexOf('<h2');
  assert.ok(html.indexOf('Descrição do instrumento.') < heading);
  assert.ok(html.indexOf('Legenda de pontuação') < heading);
  assert.match(html, /edição não confirmada/);
  assert.match(html, /Faixas etárias e subdomínios deste banco ainda não confirmados/);
});

test('zero, N, D and blanks remain distinct and unanswered items are counted', () => {
  const html = render();
  for (const code of ['0', 'N', 'D', '']) assert.ok(html.includes(`value="${code}"`));
  assert.match(html, /3 de 5 itens transcritos respondidos; 2 pendentes/);
  assert.match(html, /Pendente/);
  assert.match(html, /Não confundir com vazio/);
});

test('lowercase is normalized while observations and other domains survive edits', () => {
  const tree = interactive();
  const find = id => elements(tree()).find(element => element.props?.id === id);
  find('vineland-item-comunicacao-1').props.onChange({ target: { value: 'n' } });
  assert.equal(find('vineland-item-comunicacao-1').props.value, 'N');
  assert.equal(tree.getResponses().comunicacao['1'].observation, 'Não confundir com vazio.');
  find('vineland-general-observations').props.onChange({ target: { value: 'Observação atualizada.' } });
  assert.equal(find('vineland-item-comunicacao-1').props.value, 'N');
  assert.equal(find('vineland-general-observations').props.value, 'Observação atualizada.');
  const nav = elements(tree()).find(element => element.type === 'button' && element.props.children === 'Autonomia');
  nav.props.onClick();
  assert.equal(find('vineland-general-observations').props.value, 'Observação atualizada.');
  elements(tree()).find(element => element.type === 'button' && element.props.children === 'Comunicação').props.onClick();
  assert.equal(find('vineland-item-comunicacao-1').props.value, 'N');
});

test('only one general observations field appears below the questions', () => {
  const html = render();
  assert.equal((html.match(/<textarea/g) || []).length, 1);
  assert.equal((html.match(/<input/g) || []).length, 4);
  assert.ok(html.indexOf('<textarea') > html.indexOf('</table>'));
  assert.doesNotMatch(html, /\.observation"/);
  assert.match(html, /Observações gerais \(opcional\)/);
});

test('legacy item observations are consolidated only when no general field was saved', () => {
  assert.equal(restoreVinelandObservations(protocol, responses), 'Comunicação — item 1: Não confundir com vazio.\nAutonomia — item 1: Observação sem resposta.');
  assert.equal(restoreVinelandObservations(protocol, responses, 'Nota geral.'), 'Nota geral.');
  assert.equal(restoreVinelandObservations(protocol, responses, ''), '');
});

test('invalid input is flagged, not silently converted to another score', () => {
  const tree = interactive();
  const find = () => elements(tree()).find(element => element.props?.id === 'vineland-item-comunicacao-1');
  find().props.onChange({ target: { value: '3' } });
  assert.equal(find().props.value, '3');
  assert.equal(find().props['aria-invalid'], true);
  assert.equal(find().props['aria-describedby'], 'vineland-item-comunicacao-1-error');
});

test('saving and locked state disable all clinical data inputs', () => {
  const html = render({ disabled: true });
  assert.equal((html.match(/disabled=""/g) || []).length, 5);
});

const domainProtocol = {
  id: 'domain-180', title: 'Vineland-3 — Pais/Cuidadores dos Níveis de Domínio',
  description: 'Avalie o comportamento que a pessoa realiza sozinha, sem ajuda ou lembretes.',
  warning: 'Cadastro de 180 itens; sem correção normativa.', supports_estimates: true, item_observations: true,
  legend: { '2': 'Usualmente ou frequentemente', '1': 'Às vezes', '0': 'Nunca' },
  domains: [
    { code: 'comunicacao', label: 'Comunicação', pages: [4, 5], items: [
      { id: '1', text: 'Pergunta adaptativa.', allowed_responses: ['2', '1', '0'] },
      { id: '26', text: 'Pergunta binária.', allowed_responses: ['2', '0'], hint: 'Critério específico do formulário.' },
    ] },
    { code: 'comportamento_c', label: 'Problemas de Comportamento — Seção C', behavior_problems: true, items: [
      { id: '8', text: 'Pergunta crítica.', allowed_responses: ['2', '1', '0'] },
    ] },
  ],
};

test('domain-level form has numeric text scores, binary constraints and separate estimate checkboxes', () => {
  const html = render({ protocol: domainProtocol, responses: {} });
  assert.equal((html.match(/type="text"/g) || []).length, 2);
  assert.equal((html.match(/type="checkbox"/g) || []).length, 2);
  assert.match(html, /pattern="\[210\]"/);
  assert.match(html, /pattern="\[20\]"/);
  assert.match(html, /Somente 2 = Sim ou 0 = Não/);
  assert.match(html, /Critério específico do formulário/);
  assert.match(html, /páginas 4 e 5/);
  assert.doesNotMatch(html, /<select|\[210NnDd\]|edição não confirmada/);
  assert.equal((html.match(/<textarea/g) || []).length, 3);
});

test('domain-level estimates and observations survive edits, tab navigation and reloading', () => {
  const tree = interactive(domainProtocol, { comunicacao: { '1': { response: '0', observation: 'Nota', estimated: false } } });
  const find = id => elements(tree()).find(element => element.props?.id === id || element.props?.name === id);
  find('comunicacao.1.estimated').props.onChange({ target: { checked: true } });
  find('vineland-item-comunicacao-1-observation').props.onChange({ target: { value: 'Nota atualizada' } });
  elements(tree()).find(element => element.type === 'button' && element.props.children === 'Problemas de Comportamento — Seção C').props.onClick();
  const html = renderToStaticMarkup(tree());
  assert.match(html, /maior pontuação significa mais problemas/);
  assert.match(html, /sem soma diagnóstica/);
  elements(tree()).find(element => element.type === 'button' && element.props.children === 'Comunicação').props.onClick();
  assert.equal(find('comunicacao.1.estimated').props.checked, true);
  assert.equal(find('vineland-item-comunicacao-1').props.value, '0');
  assert.equal(find('vineland-item-comunicacao-1-observation').props.value, 'Nota atualizada');
  const reopened = interactive(domainProtocol, tree.getResponses());
  assert.equal(elements(reopened()).find(element => element.props?.name === 'comunicacao.1.estimated').props.checked, true);
  find('vineland-item-comunicacao-1').props.onChange({ target: { value: '' } });
  assert.equal(find('comunicacao.1.estimated').props.checked, false);
  assert.equal(find('comunicacao.1.estimated').props.disabled, true);
  assert.equal(find('vineland-item-comunicacao-1-observation').props.value, 'Nota atualizada');
});

test('domain-level form rejects N/D and binary 1 without mutating the answer', () => {
  const tree = interactive(domainProtocol, {});
  const find = () => elements(tree()).find(element => element.props?.id === 'vineland-item-comunicacao-26');
  for (const value of ['1', 'N', 'D', '3']) {
    find().props.onChange({ target: { value } });
    assert.equal(find().props.value, value);
    assert.equal(find().props['aria-invalid'], true);
    assert.match(vinelandResponseError(domainProtocol, tree.getResponses()), /item 26: use 2, 0/);
  }
  find().props.onChange({ target: { value: '0' } });
  assert.equal(vinelandResponseError(domainProtocol, tree.getResponses()), '');
  assert.match(vinelandResponseError(domainProtocol, { comunicacao: { '1': { response: '', estimated: true } } }), /Est. exige/);
});

test('new applications use 180-item bank while saved legacy applications keep their original questions', () => {
  assert.equal(resolveVinelandItemProtocol(domainProtocol, protocol), domainProtocol);
  assert.equal(resolveVinelandItemProtocol(domainProtocol, protocol, domainProtocol.id, true), domainProtocol);
  assert.equal(resolveVinelandItemProtocol(domainProtocol, protocol, protocol.id, true), protocol);
  assert.equal(resolveVinelandItemProtocol(domainProtocol, protocol, undefined, true), protocol);
  assert.throws(() => resolveVinelandItemProtocol(domainProtocol, protocol, 'unknown', true), /não reconhecido/);
});

test('evaluation-created empty applications open questions instead of extensive totals', () => {
  const placeholder = { id: 78, status: 'draft', raw_payload: {}, computed_payload: {}, classified_payload: {}, reviewed_payload: {}, interpretation_text: '', is_validated: false };
  assert.equal(isEmptyVinelandApplication(placeholder), true);
  assert.equal(vinelandEntryMode(placeholder), 'items');
  assert.equal(vinelandEntryMode({ ...placeholder, status: 'completed', applied_on: '2026-01-15' }), 'items');
  assert.equal(vinelandEntryMode(null), 'items');
  assert.equal(resolveVinelandItemProtocol(domainProtocol, protocol, undefined, false), domainProtocol);
  for (const extra of [
    { raw_payload: { respondent: 'Preservar' } }, { computed_payload: { domains: [{}] } },
    { classified_payload: { old: 1 } }, { reviewed_payload: { note: 'Preservar' } },
    { interpretation_text: 'Texto salvo' }, { is_validated: true }, { status: 'locked' },
  ]) {
    assert.equal(isEmptyVinelandApplication({ ...placeholder, ...extra }), false);
    assert.equal(vinelandEntryMode({ ...placeholder, ...extra }), 'totals');
  }
  assert.equal(vinelandEntryMode({ ...placeholder, raw_payload: { entry_mode: 'items', item_protocol_id: protocol.id } }), 'items');
});

test('locked domain-level records disable scores, estimates and all observations', () => {
  const tree = interactive(domainProtocol, { comunicacao: { '1': { response: '2', observation: '', estimated: true } } }, true);
  for (const element of elements(tree()).filter(element => ['input', 'textarea'].includes(element.type))) {
    assert.equal(element.props.disabled, true);
  }
});

async function loadPage(application) {
  const filename = path.join(__dirname, '../../app/dashboard/tests/vineland3/page.tsx');
  const state = [];
  let cursor = 0;
  let effect;
  let posted;
  const definitions = {
    item_protocol: domainProtocol, legacy_item_protocol: protocol, technical_notes: [],
    forms: Object.fromEntries(['entrevista', 'pais_cuidadores', 'professores'].map(code => [code, { label: code, scales: [] }])),
  };
  const mockReact = { ...React,
    useState(initial) {
      const index = cursor++;
      if (!(index in state)) state[index] = initial;
      return [state[index], next => { state[index] = typeof next === 'function' ? next(state[index]) : next; }];
    },
    useEffect(callback) { effect ||= callback; },
  };
  const mod = new Module(filename, module);
  mod.filename = filename;
  mod.paths = module.paths;
  const original = mod.require.bind(mod);
  mod.require = id => {
    if (id === 'react') return mockReact;
    if (id === 'next/navigation') return { useRouter: () => ({ replace() {} }), useSearchParams: () => new URLSearchParams('evaluation_id=13&application_id=78') };
    if (id === 'next/link') return { default: ({ href, children, ...props }) => React.createElement('a', { ...props, href }, children) };
    if (id === '@/components/ui/button') return { Button: props => React.createElement('button', props) };
    if (id === '@/components/ui/input') return { Input: props => React.createElement('input', props) };
    if (id === '@/components/tests/VinelandItemFields') return load();
    if (id === '@/lib/api') return { api: {
      async get(url) {
        if (url.endsWith('/protocol')) return definitions;
        if (url.includes('/applications/')) return application;
        return { id: 13, patient_name: 'Paciente de teste', patient_birth_date: '2020-01-01', start_date: '2026-01-15' };
      },
      async post(url, payload) { posted = { url, payload }; return { ...application, application_id: 78 }; },
    } };
    return original(id);
  };
  mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2018 },
  }).outputText, filename);
  function tree() {
    cursor = 0;
    return mod.exports.default().props.children.type();
  }
  tree();
  effect();
  await new Promise(resolve => setImmediate(resolve));
  return { tree, posted: () => posted };
}

test('page with evaluation/application URL renders questions and submits into the empty application', async () => {
  const page = await loadPage({ id: 78, evaluation_id: 13, instrument_code: 'vineland3', status: 'draft',
    raw_payload: {}, computed_payload: {}, classified_payload: {}, reviewed_payload: {}, interpretation_text: '', is_validated: false });
  const tree = page.tree();
  const html = renderToStaticMarkup(tree);
  assert.match(html, /Pergunta adaptativa/);
  assert.match(html, /Pergunta binária/);
  assert.doesNotMatch(html, /Pontuações brutas por subdomínio/);
  const select = elements(tree).find(element => element.props?.id === 'vineland-entry-mode');
  assert.equal(select.props.disabled, false);
  await elements(tree).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(page.posted().payload.application_id, 78);
  assert.equal(page.posted().payload.entry_mode, 'items');
  assert.equal(page.posted().payload.item_protocol_id, domainProtocol.id);
});

test('page with saved extensive results offers a separate question form without replacing results', async () => {
  const page = await loadPage({ id: 78, evaluation_id: 13, instrument_code: 'vineland3', status: 'scored',
    raw_payload: { form: 'entrevista', raw_scores: { rec: 10 } },
    computed_payload: { domains: [{ scale: 'COM', label: 'Comunicação', standard_score: 90, percentile: '25' }] },
    interpretation_text: 'Síntese preservada', is_validated: false });
  const html = renderToStaticMarkup(page.tree());
  assert.match(html, /Síntese preservada/);
  assert.match(html, /Abrir formulário de 180 perguntas/);
  assert.match(html, /href="\/dashboard\/tests\/vineland3\?evaluation_id=13"/);
  assert.doesNotMatch(html, /Pergunta adaptativa/);
  assert.equal(page.posted(), undefined);
});
