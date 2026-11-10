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

function loadResult(react = React, component = 'VinelandQuestionnaireResult.tsx') {
  const filename = path.join(__dirname, component);
  const mod = new Module(filename, module);
  mod.paths = module.paths;
  const original = mod.require.bind(mod);
  mod.require = id => {
    if (id === 'react') return react;
    if (id === './VinelandNormativeResults') return loadNormative();
    if (id === '@/lib/api') return { getToken: () => 'test-token', resolveApiUrl: url => `https://api.example.test${url}` };
    if (id === 'next/link') return { default: ({ href, children, ...props }) => React.createElement('a', { ...props, href }, children) };
    return original(id);
  };
  mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText, filename);
  return mod.exports;
}

function loadNormative() {
  const filename = path.join(__dirname, 'VinelandNormativeResults.tsx');
  const mod = new Module(filename, module);
  mod.paths = module.paths;
  mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText, filename);
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

test('domain-level rows contain only the question and a numeric text response, without observations or estimates', () => {
  const html = render({ protocol: domainProtocol, responses: {} });
  assert.equal((html.match(/type="text"/g) || []).length, 2);
  assert.equal((html.match(/type="checkbox"/g) || []).length, 0);
  assert.match(html, /pattern="\[210\]"/);
  assert.match(html, /pattern="\[20\]"/);
  assert.match(html, /Somente 2 = Sim ou 0 = Não/);
  assert.match(html, /Critério específico do formulário/);
  assert.match(html, /páginas 4 e 5/);
  assert.doesNotMatch(html, /<select|\[210NnDd\]|edição não confirmada/);
  assert.equal((html.match(/<textarea/g) || []).length, 1);
  const table = html.slice(html.indexOf('<table'), html.indexOf('</table>'));
  assert.doesNotMatch(table, /Observação|Est\.|<details|<textarea|type="checkbox"/);
  assert.equal((table.match(/scope="col"/g) || []).length, 3);
});

test('hidden historical estimates and observations survive response edits, tab navigation and reloading', () => {
  const tree = interactive(domainProtocol, { comunicacao: { '1': { response: '0', observation: 'Nota histórica', estimated: true } } });
  const find = id => elements(tree()).find(element => element.props?.id === id || element.props?.name === id);
  assert.equal(find('comunicacao.1.estimated'), undefined);
  assert.equal(find('vineland-item-comunicacao-1-observation'), undefined);
  find('vineland-item-comunicacao-1').props.onChange({ target: { value: '2' } });
  elements(tree()).find(element => element.type === 'button' && element.props.children === 'Problemas de Comportamento — Seção C').props.onClick();
  const html = renderToStaticMarkup(tree());
  assert.match(html, /maior pontuação significa mais problemas/);
  assert.match(html, /sem soma diagnóstica/);
  elements(tree()).find(element => element.type === 'button' && element.props.children === 'Comunicação').props.onClick();
  assert.equal(find('vineland-item-comunicacao-1').props.value, '2');
  assert.deepEqual(tree.getResponses().comunicacao['1'], { response: '2', observation: 'Nota histórica', estimated: true });
  const reopened = interactive(domainProtocol, tree.getResponses());
  assert.equal(elements(reopened()).find(element => element.props?.id === 'vineland-item-comunicacao-1').props.value, '2');
  assert.deepEqual(reopened.getResponses().comunicacao['1'], tree.getResponses().comunicacao['1']);
  find('vineland-item-comunicacao-1').props.onChange({ target: { value: '' } });
  assert.equal(tree.getResponses().comunicacao['1'].estimated, false);
  assert.equal(tree.getResponses().comunicacao['1'].observation, 'Nota histórica');
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

test('locked domain-level records disable responses and general observations', () => {
  const tree = interactive(domainProtocol, { comunicacao: { '1': { response: '2', observation: '', estimated: true } } }, true);
  for (const element of elements(tree()).filter(element => ['input', 'textarea'].includes(element.type))) {
    assert.equal(element.props.disabled, true);
  }
});

async function loadPage(application, query = 'evaluation_id=13&application_id=78', route = 'vineland', options = {}) {
  const filename = path.join(__dirname, `../../app/dashboard/tests/${route}/page.tsx`);
  const state = [];
  let cursor = 0;
  let effect;
  let posted;
  const redirects = [];
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
    if (id === '../vineland/page') {
      const canonicalFile = path.join(__dirname, '../../app/dashboard/tests/vineland/page.tsx');
      const canonical = new Module(canonicalFile, module);
      canonical.filename = canonicalFile;
      canonical.paths = module.paths;
      canonical.require = mod.require;
      canonical._compile(ts.transpileModule(fs.readFileSync(canonicalFile, 'utf8'), {
        compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2018 },
      }).outputText, canonicalFile);
      return canonical.exports;
    }
    if (id === 'react') return mockReact;
    if (id === 'next/navigation') return { useRouter: () => ({ replace(url) { redirects.push(url); } }), useSearchParams: () => new URLSearchParams(query), useParams: () => ({ id: new URLSearchParams(query).get('application_id') }) };
    if (id === 'next/link') return { default: ({ href, children, ...props }) => React.createElement('a', { ...props, href }, children) };
    if (id === '@/components/ui/button') return { Button: props => React.createElement('button', props) };
    if (id === '@/components/ui/input') return { Input: props => React.createElement('input', props) };
    if (id === '@/components/tests/VinelandItemFields') return load();
    if (id === '@/components/tests/VinelandQuestionnaireResult') return loadResult();
    if (id === '@/components/tests/VinelandPdfButton') return { VinelandPdfButton: () => React.createElement('button', { type: 'button' }, 'Imprimir / PDF') };
    if (id === '@/lib/api') return { api: {
      async get(url) {
        if (url.endsWith('/protocol')) return definitions;
        if (url.includes('/applications/')) return application;
        return { id: Number(new URLSearchParams(query).get('evaluation_id')), patient_name: 'Paciente de teste', patient_birth_date: '2020-01-01', start_date: '2026-01-15' };
      },
      async post(url, payload) {
        posted = { url, payload };
        if (options.postError) throw { message: options.postError };
        return { ...application, application_id: application?.id || 78 };
      },
    } };
    return original(id);
  };
  mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2018 },
  }).outputText, filename);
  function tree() {
    cursor = 0;
    const page = mod.exports.default();
    return route.endsWith('/result') ? page : page.props.children.type();
  }
  tree();
  effect();
  await new Promise(resolve => setImmediate(resolve));
  return { tree, posted: () => posted, redirects };
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

test('page with saved extensive results offers a separate question form without trusting cached text', async () => {
  const page = await loadPage({ id: 78, evaluation_id: 13, instrument_code: 'vineland3', status: 'scored',
    raw_payload: { form: 'entrevista', raw_scores: { rec: 10 } },
    computed_payload: { domains: [{ scale: 'COM', label: 'Comunicação', standard_score: 90, percentile: '25' }] },
    interpretation_text: 'Síntese preservada', is_validated: false }, 'evaluation_id=13&application_id=78&entry=totals');
  const html = renderToStaticMarkup(page.tree());
  assert.doesNotMatch(html, /Síntese preservada/);
  assert.match(html, /Correção normativa indisponível/);
  assert.match(html, /Abrir formulário de 180 perguntas/);
  assert.match(html, /href="\/dashboard\/tests\/vineland\?evaluation_id=13"/);
  assert.doesNotMatch(html, /Pergunta adaptativa/);
  assert.equal(page.posted(), undefined);
});

test('default evaluation link opens questions even when an application has extensive-form metadata', async () => {
  const original = { id: 79, evaluation_id: 13, instrument_code: 'vineland3', status: 'completed',
    raw_payload: { form: 'pais_cuidadores', entry_mode: 'totals', raw_scores: {}, respondent: '' },
    computed_payload: {}, interpretation_text: '', is_validated: false };
  const page = await loadPage(original, 'evaluation_id=13&application_id=79');
  const tree = page.tree();
  const html = renderToStaticMarkup(tree);
  assert.match(html, /Pergunta adaptativa/);
  assert.match(html, /Pergunta binária/);
  assert.doesNotMatch(html, /Pontuações brutas por subdomínio/);
  assert.match(html, /aplicação anterior #79/);
  assert.match(html, /application_id=79&amp;entry=totals/);
  await elements(tree).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(page.posted().payload.entry_mode, 'items');
  assert.equal(page.posted().payload.application_id, null);
  assert.deepEqual(original.raw_payload.raw_scores, {});
});

test('evaluation question mode never imports old scores, answers or notes into the new protocol', async () => {
  const page = await loadPage({ id: 79, evaluation_id: 13, instrument_code: 'vineland3', status: 'scored',
    raw_payload: { form: 'entrevista', raw_scores: { rec: 10 }, general_observations: 'Nota do protocolo antigo' },
    computed_payload: { domains: [{ scale: 'COM', label: 'Comunicação', standard_score: 90, percentile: '25' }] },
    interpretation_text: 'Síntese anterior', is_validated: true }, 'evaluation_id=13&application_id=79&entry=items');
  const tree = page.tree();
  const html = renderToStaticMarkup(tree);
  assert.match(html, /Pergunta adaptativa/);
  assert.doesNotMatch(html, /Nota do protocolo antigo|Síntese anterior/);
  await elements(tree).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(page.posted().payload.application_id, null);
  assert.deepEqual(page.posted().payload.raw_scores, {});
  assert.deepEqual(page.posted().payload.item_responses, {});
  assert.equal(page.posted().payload.general_observations, '');
});

test('evaluation question mode reopens the current questionnaire and saves the same application', async () => {
  const savedResponses = { comunicacao: { '1': { response: '0', estimated: true, observation: 'Preservar' } } };
  const page = await loadPage({ id: 79, evaluation_id: 13, instrument_code: 'vineland3', status: 'completed',
    raw_payload: { entry_mode: 'items', item_protocol_id: domainProtocol.id, item_responses: savedResponses },
    computed_payload: {}, interpretation_text: '', is_validated: false }, 'evaluation_id=13&application_id=79&entry=items');
  const tree = page.tree();
  const html = renderToStaticMarkup(tree);
  assert.match(html, /Pergunta adaptativa/);
  assert.match(html, /Preservar/);
  assert.doesNotMatch(html, /um novo formulário/);
  await elements(tree).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(page.posted().payload.application_id, 79);
  assert.deepEqual(page.posted().payload.item_responses, savedResponses);
});

test('evaluation navigation points to the canonical question form and retains evaluation/application IDs', async () => {
  const navFile = path.join(__dirname, '../../lib/vineland-navigation.ts');
  const nav = new Module(navFile, module);
  nav._compile(ts.transpileModule(fs.readFileSync(navFile, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText, navFile);
  const overviewFile = path.join(__dirname, '../../app/dashboard/evaluations/[id]/overview/page.tsx');
  const source = ts.createSourceFile(overviewFile, fs.readFileSync(overviewFile, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  let routingFunction;
  function find(node) {
    if (ts.isFunctionDeclaration(node) && node.name?.text === 'getTestUrl') routingFunction = node;
    ts.forEachChild(node, find);
  }
  find(source);
  assert.ok(routingFunction, 'evaluation routing function must exist');
  const routing = new Module(overviewFile, module);
  routing.require = () => nav.exports;
  routing._compile(ts.transpileModule(`
    const evaluation = { id: 15 };
    const { vinelandQuestionnaireUrl } = require('navigation');
    export ${routingFunction.getText(source)}
  `, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, overviewFile);
  const url = new URL(routing.exports.getTestUrl('vineland3', 85), 'http://localhost');
  assert.equal(url.pathname, '/dashboard/tests/vineland');
  assert.equal(url.searchParams.get('evaluation_id'), '15');
  assert.equal(url.searchParams.get('application_id'), '85');
  assert.equal(url.searchParams.get('entry'), 'items');
  assert.equal(new URL(routing.exports.getTestUrl('wasi', 86), url).pathname, '/dashboard/tests/wasi');
  const page = await loadPage({ id: 85, evaluation_id: 15, instrument_code: 'vineland3', status: 'draft',
    raw_payload: {}, computed_payload: {}, interpretation_text: '', is_validated: false }, url.search);
  const tree = page.tree();
  assert.match(renderToStaticMarkup(tree), /Pergunta adaptativa/);
  assert.doesNotMatch(renderToStaticMarkup(tree), /Pontuações brutas por subdomínio/);
  await elements(tree).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(page.posted().payload.evaluation_id, 15);
  assert.equal(page.posted().payload.application_id, 85);
  assert.equal(page.posted().payload.entry_mode, 'items');
});

test('vineland and vineland3 URLs render the same questionnaire, not separate implementations', async () => {
  const saved = { id: 85, evaluation_id: 15, instrument_code: 'vineland3', status: 'draft',
    raw_payload: {}, computed_payload: {}, interpretation_text: '', is_validated: false };
  const query = 'evaluation_id=15&application_id=85&entry=items';
  const direct = await loadPage(saved, query, 'vineland');
  const alias = await loadPage(saved, query, 'vineland3');
  assert.equal(renderToStaticMarkup(direct.tree()), renderToStaticMarkup(alias.tree()));
});

const finalizedQuestionnaire = {
  id: 85, evaluation_id: 15, instrument_code: 'vineland3', patient_name: 'Paciente Vineland', status: 'completed',
  applied_on: '2026-01-15', computed_payload: {}, interpretation_text: '', is_validated: false,
  raw_payload: { entry_mode: 'items', item_protocol_id: domainProtocol.id, completion_status: 'finalized',
    respondent: 'Cuidador', birth_date: '2020-01-01', general_observations: 'Nota preservada',
    item_responses: { comunicacao: { '1': { response: '0', observation: '' } } },
    item_summary: { protocol_id: domainProtocol.id, normative_scoring: false, answered: 120, applied_total: 120,
      sections: [
        { code: 'comunicacao', label: 'Comunicação', kind: 'adaptive', applied: true, answered: 40, total: 40, raw_score: 0, max_score: 80 },
        { code: 'vida_diaria', label: 'Atividades de Vida Diária', kind: 'adaptive', applied: true, answered: 40, total: 40, raw_score: 60, max_score: 80 },
        { code: 'socializacao', label: 'Habilidades Sociais', kind: 'adaptive', applied: true, answered: 40, total: 40, raw_score: 80, max_score: 80 },
        { code: 'atividade_fisica', label: 'Habilidades Motoras', kind: 'adaptive', applied: false, answered: 0, total: 25, raw_score: null, max_score: 50 },
        { code: 'comportamento_a', label: 'Internalizante', kind: 'behavior', applied: false, answered: 0, total: 13, raw_score: null, max_score: 26 },
        { code: 'comportamento_b', label: 'Externalizante', kind: 'behavior', applied: false, answered: 0, total: 11, raw_score: null, max_score: 22 },
        { code: 'comportamento_c', label: 'Itens críticos', kind: 'critical', applied: false, answered: 0, total: 11, raw_score: null, max_score: null },
      ], critical_items: [],
    },
  },
};

test('finalize submits all current responses under the existing ID and opens its result page', async () => {
  const saved = structuredClone(finalizedQuestionnaire);
  delete saved.raw_payload.completion_status;
  delete saved.raw_payload.item_summary;
  const page = await loadPage(saved, 'evaluation_id=15&application_id=85');
  const tree = page.tree();
  assert.match(renderToStaticMarkup(tree), /Finalizar teste e ver resultados/);
  assert.match(renderToStaticMarkup(tree), /Salvar registro parcial/);
  const finalize = elements(tree).find(element => element.props?.value === 'finalize');
  assert.equal(finalize.props.type, 'submit');
  await elements(tree).find(element => element.type === 'form').props.onSubmit({
    preventDefault() {}, nativeEvent: { submitter: { getAttribute: name => name === 'value' ? 'finalize' : null } },
  });
  assert.equal(page.posted().payload.finalize, true);
  assert.equal(page.posted().payload.application_id, 85);
  assert.equal(page.posted().payload.evaluation_id, 15);
  assert.deepEqual(page.posted().payload.item_responses, saved.raw_payload.item_responses);
  assert.equal(page.posted().payload.general_observations, 'Nota preservada');
  assert.deepEqual(page.redirects, ['/dashboard/tests/vineland/85/result']);
});

test('partial save stays in the form, and failed finalization keeps answers without navigating', async () => {
  const saved = structuredClone(finalizedQuestionnaire);
  delete saved.raw_payload.completion_status;
  delete saved.raw_payload.item_summary;
  const partial = await loadPage(saved, 'evaluation_id=15&application_id=85');
  await elements(partial.tree()).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.equal(partial.posted().payload.finalize, false);
  assert.doesNotMatch(partial.redirects[0], /\/result/);
  const failure = await loadPage(saved, 'evaluation_id=15&application_id=85', 'vineland', { postError: 'Comunicação: faltam respostas nos itens 2.' });
  await elements(failure.tree()).find(element => element.type === 'form').props.onSubmit({
    preventDefault() {}, nativeEvent: { submitter: { getAttribute: () => 'finalize' } },
  });
  assert.deepEqual(failure.redirects, []);
  assert.match(renderToStaticMarkup(failure.tree()), /faltam respostas nos itens 2/);
  const fields = elements(failure.tree()).find(element => element.props?.responses);
  assert.deepEqual(fields.props.responses, saved.raw_payload.item_responses);
});

test('finalized questionnaire reopens with WISC-style result, zero scores, optional sections and editing link', async () => {
  const page = await loadPage(finalizedQuestionnaire, 'evaluation_id=15&application_id=85');
  const html = renderToStaticMarkup(page.tree());
  assert.match(html, /Vineland-3 - Resultado/);
  assert.match(html, /Paciente Vineland/);
  assert.match(html, /Cuidador/);
  assert.match(html, /15\/01\/2026/);
  assert.match(html, /Resumo das áreas adaptativas/);
  assert.match(html, /Perfil das somas brutas/);
  assert.match(html, /120 de 120/);
  assert.match(html, /font-bold text-blue-700">0<\/td>/);
  assert.match(html, /Não aplicada/);
  assert.match(html, /sem correção normativa/);
  assert.match(html, /application_id=85&amp;edit=true/);
  assert.match(html, /Imprimir \/ PDF/);
  assert.match(html, /Nota preservada/);
  assert.doesNotMatch(html, /<form|Escore Composto|QI Total/);
  const edit = await loadPage(finalizedQuestionnaire, 'evaluation_id=15&application_id=85&edit=true');
  assert.match(renderToStaticMarkup(edit.tree()), /<form/);
  assert.match(renderToStaticMarkup(edit.tree()), /Finalizar teste e ver resultados/);
});

test('result page loads a finalized application and rejects incomplete or other-instrument applications', async () => {
  const result = await loadPage(finalizedQuestionnaire, 'application_id=85', 'vineland/[id]/result');
  assert.match(renderToStaticMarkup(result.tree()), /Vineland-3 - Resultado/);
  for (const saved of [
    { ...finalizedQuestionnaire, instrument_code: 'wisc4' },
    { ...finalizedQuestionnaire, raw_payload: { completion_status: 'partial' } },
  ]) {
    const page = await loadPage(saved, 'application_id=85', 'vineland/[id]/result');
    const html = renderToStaticMarkup(page.tree());
    assert.match(html, /não possui um questionário Vineland finalizado/);
    assert.doesNotMatch(html, /Resumo das áreas adaptativas/);
  }
});

test('critical items are individual review entries, not a sum, and locked results cannot be edited', () => {
  const saved = structuredClone(finalizedQuestionnaire);
  saved.status = 'locked';
  saved.raw_payload.item_summary.sections.at(-1).applied = true;
  saved.raw_payload.item_summary.critical_items = [{ id: '2', response: '1', text: 'Comportamento a revisar.' }];
  const { VinelandQuestionnaireResult } = loadResult();
  const html = renderToStaticMarkup(React.createElement(VinelandQuestionnaireResult, { application: saved }));
  assert.match(html, /Item 2 · Resposta 1/);
  assert.match(html, /Comportamento a revisar/);
  assert.match(html, /não recebe soma ou diagnóstico automático/);
  assert.doesNotMatch(html, /edit=true/);
});

function interactiveResult(application = finalizedQuestionnaire, extensive = false) {
  const state = [];
  let cursor;
  const components = loadResult({ ...React, useState(initial) {
    const index = cursor++;
    if (!(index in state)) state[index] = initial;
    return [state[index], next => { state[index] = next; }];
  } }, extensive ? 'VinelandPdfButton.tsx' : 'VinelandQuestionnaireResult.tsx');
  return () => { cursor = 0; return extensive ? components.VinelandPdfButton({ applicationId: application.id }) : components.VinelandQuestionnaireResult({ application }); };
}

for (const extensive of [false, true]) {
test(`PDF button fetches the authenticated server PDF, shows progress and downloads it instead of printing HTML (${extensive ? 'extensive' : 'domain'})`, async t => {
  const tree = interactiveResult(finalizedQuestionnaire, extensive);
  let resolveFetch;
  const fetchMock = t.mock.method(global, 'fetch', () => new Promise(resolve => { resolveFetch = resolve; }));
  const blob = new Blob(['%PDF-1.4 test'], { type: 'application/pdf' });
  t.mock.method(URL, 'createObjectURL', value => { assert.equal(value, blob); return 'blob:vineland-pdf'; });
  let downloaded = false;
  const anchor = { click() { downloaded = true; }, remove() {} };
  const originalDocument = global.document;
  const originalWindow = global.window;
  global.document = { createElement(tag) { assert.equal(tag, 'a'); return anchor; }, body: { appendChild(value) { assert.equal(value, anchor); } } };
  global.window = { setTimeout() {} };
  try {
    const button = () => elements(tree()).find(element => element.type === 'button' && element.props['aria-busy'] !== undefined);
    const request = button().props.onClick();
    assert.equal(button().props.disabled, true);
    assert.equal(button().props.children, 'Gerando PDF…');
    assert.equal(fetchMock.mock.calls[0].arguments[0], 'https://api.example.test/api/tests/applications/85/export-pdf');
    assert.equal(fetchMock.mock.calls[0].arguments[1].headers.Authorization, 'Bearer test-token');
    assert.equal(fetchMock.mock.calls[0].arguments[1].cache, 'no-store');
    resolveFetch({ ok: true, blob: async () => blob });
    await request;
    assert.equal(downloaded, true);
    assert.equal(anchor.href, 'blob:vineland-pdf');
    assert.equal(anchor.download, 'VINELAND3-85.pdf');
    assert.equal(button().props.disabled, false);
  } finally {
    if (originalDocument === undefined) delete global.document; else global.document = originalDocument;
    if (originalWindow === undefined) delete global.window; else global.window = originalWindow;
  }
});

test(`PDF errors remain visible and allow retry without altering the questionnaire (${extensive ? 'extensive' : 'domain'})`, async t => {
  const tree = interactiveResult(finalizedQuestionnaire, extensive);
  t.mock.method(global, 'fetch', async () => ({ ok: false, status: 404, json: async () => ({ message: 'Finalize o questionário Vineland antes de gerar o PDF.' }) }));
  const button = () => elements(tree()).find(element => element.type === 'button' && element.props['aria-busy'] !== undefined);
  await button().props.onClick();
  assert.equal(button().props.disabled, false);
  const alert = elements(tree()).find(element => element.props?.role === 'alert');
  assert.equal(alert.props.children, 'Finalize o questionário Vineland antes de gerar o PDF.');
  if (!extensive) assert.match(renderToStaticMarkup(tree()), /Resumo das áreas adaptativas/);
});
}

test('normative results replace raw-only panels with standard scores, CCA, IC95 and statistical analysis', () => {
  const { VinelandQuestionnaireResult } = loadResult();
  const score = { code: 'comunicacao', scale: 'COM', label: 'Comunicação', raw_score: 72, standard_score: 130, percentile: '98', confidence_interval: [122, 138], classification: 'Alto', unavailable_reason: null };
  const result = { normative_scoring: true, confidence_level: 95, age_months: 72, population: 'Normas americanas',
    adaptive: [score, { ...score, code: 'vida_diaria', scale: 'AVD' }, { ...score, code: 'socializacao', scale: 'SOC' }, { ...score, code: 'atividade_fisica', scale: 'HMOT', raw_score: null, standard_score: null, confidence_interval: null, classification: null, unavailable_reason: 'Seção não aplicada' }],
    cca: { ...score, code: 'cca', scale: 'CCA', label: 'Composto de Comportamento Adaptativo', raw_score: null, standard_score: 112, percentile: '79', confidence_interval: [107, 117], sum_standard_scores: 331 },
    behavior: [{ ...score, code: 'comportamento_a', scale: 'internalizante', raw_score: 13, v_scale: 21 }],
    mean_standard_score: 106.25, mean_domain_count: 4,
    strengths: [{ scale: 'COM', standard_score: 130, difference: 23.75, critical_value: 6.61, finding: 'Força', base_rate: '≤ 2%' }],
    pairs: [{ first: 'COM', second: 'AVD', difference: 20, critical_value: 10.53, significant: true, base_rate: '> 5% a ≤ 10%' }] };
  const html = renderToStaticMarkup(React.createElement(VinelandQuestionnaireResult, { application: { ...finalizedQuestionnaire, normative_results: result } }));
  for (const text of ['IC 95%', 'Normas americanas', 'Perfil dos escores padrão', '122 – 138', '107 – 117', '331', 'Escala-v', 'Taxa de base', 'Força', 'Seção não aplicada']) assert.ok(html.includes(text), text);
  assert.match(html, /<svg/);
  assert.doesNotMatch(html, /sem correção normativa|Perfil das somas brutas|não está habilitada/);
  assert.match(html, /Itens críticos/);
});

test('normative result error blocks the numeric panels rather than displaying cached scores', () => {
  const { VinelandNormativeResults } = loadNormative();
  const html = renderToStaticMarkup(React.createElement(VinelandNormativeResults, { result: { error: 'Comunicação: faltam respostas.' } }));
  assert.match(html, /role="alert"/);
  assert.match(html, /faltam respostas/);
  assert.doesNotMatch(html, /<table|<svg/);
});

test('extensive results group subdomains by code, preserve missing motor and collapse exploratory pairs', () => {
  const { VinelandNormativeResults } = loadNormative();
  const score = (scale, value) => ({ code: scale, scale, label: scale, raw_score: null, sum_v_scale: 30,
    standard_score: value, percentile: value === null ? null : '4', confidence_interval: value === null ? null : [67, 79],
    classification: value === null ? null : 'Moderadamente baixo', unavailable_reason: value === null ? 'Não informado' : null });
  const result = { form_level: 'extensivo', form: 'entrevista', form_label: 'Entrevista extensiva',
    normative_scoring: true, confidence_level: 95, age_months: 72, population: 'Normas americanas', table_codes: 'B.1–B.6',
    adaptive: [score('COM', 73), score('AVD', 98), score('SOC', 72), score('HMOT', null)],
    cca: { ...score('CCA', 78), sum_standard_scores: 243 }, behavior: [], mean_standard_score: 81, mean_domain_count: 3,
    strengths: [], pairs: [], subdomain_mean_v_scale: 19, subdomain_count: 2,
    subdomains: [{ scale: 'com', display_code: 'CMD', domain: 'AVD', label: 'Comunidade', raw_score: 58, v_scale: 19, age_equivalent: '6:0', growth_value: 100 }],
    subdomain_strengths: [], subdomain_pairs: [
      { first: 'rec', second: 'exp', first_score: 7, second_score: 4, relation: '>', difference: 3, critical_value: 2.22, significant: true, base_rate: '> 15%', within_domain: true },
      { first: 'rec', second: 'com', first_score: 7, second_score: 19, relation: '<', difference: -12, critical_value: 3, significant: true, base_rate: '≤ 2%', within_domain: false },
    ] };
  const original = structuredClone(result);
  const html = renderToStaticMarkup(React.createElement(VinelandNormativeResults, { result }));
  for (const text of ['CMD · Comunidade', 'Soma de entrada', '67 – 79', '243', 'Equiv. etário', 'Comparações no mesmo domínio', 'REC – EXP', 'REC – CMD', 'Não informado']) assert.ok(html.includes(text), text);
  assert.match(html, /<details[^>]*><summary/);
  assert.doesNotMatch(html, /<details[^>]* open|COM – CMD|Sem norma|Internalizante/);
  assert.equal((html.match(/<circle/g) || []).length, 4, 'Missing motor has no score marker');
  assert.deepEqual(result, original);
});

const pendingReview = { eligible: true, validated: false, fingerprint: 'a'.repeat(64), reason: 'Revisão profissional pendente.' };

test('clinical review requires confirmation and a note, authenticates and binds approval to the displayed version', async t => {
  const application = { ...finalizedQuestionnaire, clinical_review: pendingReview };
  const tree = interactiveResult(application);
  const form = () => elements(tree()).find(element => element.type === 'form');
  const button = () => elements(tree()).find(element => element.props?.type === 'submit');
  assert.equal(button().props.disabled, true);
  elements(tree()).find(element => element.type === 'textarea').props.onChange({ target: { value: 'Dados e itens críticos conferidos.' } });
  assert.equal(button().props.disabled, true);
  elements(tree()).find(element => element.props?.type === 'checkbox').props.onChange({ target: { checked: true } });
  assert.equal(button().props.disabled, false);
  let done;
  const mock = t.mock.method(global, 'fetch', () => new Promise(resolve => { done = resolve; }));
  const request = form().props.onSubmit({ preventDefault() {} });
  assert.equal(button().props.disabled, true);
  assert.equal(button().props.children, 'Registrando revisão…');
  const [url, options] = mock.mock.calls[0].arguments;
  assert.equal(url, 'https://api.example.test/api/tests/vineland3/applications/85/review');
  assert.equal(options.method, 'POST');
  assert.equal(options.headers.Authorization, 'Bearer test-token');
  assert.deepEqual(JSON.parse(options.body), { fingerprint: pendingReview.fingerprint, confirmed: true, clinical_note: 'Dados e itens críticos conferidos.' });
  done({ ok: true, json: async () => ({ clinical_review: { ...pendingReview, validated: true, reason: 'Revisado para inclusão no laudo.', reviewer: { name: 'Profissional fictício', crp: '00/000' }, clinical_note: 'Dados conferidos.' } }) });
  await request;
  assert.equal(form(), undefined);
  assert.match(renderToStaticMarkup(tree()), /Profissional fictício|00\/000/);
  assert.match(renderToStaticMarkup(tree()), /Retirar validação/);
  assert.equal(application.clinical_review.validated, false, 'Never mutate the received application');
});

test('stale-version and permission errors stay visible without marking the questionnaire reviewed', async t => {
  const tree = interactiveResult({ ...finalizedQuestionnaire, clinical_review: pendingReview });
  elements(tree()).find(element => element.type === 'textarea').props.onChange({ target: { value: 'Conferência das respostas.' } });
  elements(tree()).find(element => element.props?.type === 'checkbox').props.onChange({ target: { checked: true } });
  t.mock.method(global, 'fetch', async () => ({ ok: false, json: async () => ({ message: 'Os dados ou normas mudaram. Reabra os resultados.' }) }));
  await elements(tree()).find(element => element.type === 'form').props.onSubmit({ preventDefault() {} });
  assert.match(renderToStaticMarkup(tree()), /role="alert"/);
  assert.match(renderToStaticMarkup(tree()), /Reabra os resultados/);
  assert.equal(elements(tree()).find(element => element.props?.type === 'submit').props.disabled, false);
  assert.doesNotMatch(renderToStaticMarkup(tree()), /Retirar validação/);
});

test('clinical review is unavailable when locked or without applicable norms and displays historical estimates read-only', () => {
  const { VinelandQuestionnaireResult } = loadResult();
  for (const changes of [{ status: 'locked', clinical_review: pendingReview }, { clinical_review: { eligible: false, validated: false, reason: 'Sem norma para a idade' } }]) {
    const html = renderToStaticMarkup(React.createElement(VinelandQuestionnaireResult, { application: { ...finalizedQuestionnaire, ...changes } }));
    assert.doesNotMatch(html, /Validar para inclusão no laudo|<textarea/);
  }
  const html = renderToStaticMarkup(React.createElement(VinelandQuestionnaireResult, { application: { ...finalizedQuestionnaire, clinical_review: pendingReview,
    raw_payload: { ...finalizedQuestionnaire.raw_payload, item_responses: { comunicacao: { '1': { response: '0', estimated: true, observation: 'Nota histórica preservada' } } } } } }));
  assert.match(html, /Estimativa registrada/);
  assert.match(html, /Nota histórica preservada/);
});

test('revoking approval uses its authenticated action and restores the review form without changing responses', async t => {
  const reviewed = { ...pendingReview, validated: true, reason: 'Revisado', reviewer: { name: 'Clínico' } };
  const tree = interactiveResult({ ...finalizedQuestionnaire, clinical_review: reviewed });
  const originalWindow = global.window;
  global.window = { confirm: () => true };
  try {
    const mock = t.mock.method(global, 'fetch', async () => ({ ok: true, json: async () => ({ clinical_review: pendingReview }) }));
    await elements(tree()).find(element => element.props?.children === 'Retirar validação').props.onClick();
    assert.equal(mock.mock.calls[0].arguments[0], 'https://api.example.test/api/tests/vineland3/applications/85/review/revoke');
    assert.equal(mock.mock.calls[0].arguments[1].headers.Authorization, 'Bearer test-token');
    assert.match(renderToStaticMarkup(tree()), /Validar para inclusão no laudo/);
    assert.doesNotMatch(renderToStaticMarkup(tree()), /Retirar validação/);
  } finally { if (originalWindow === undefined) delete global.window; else global.window = originalWindow; }
});
