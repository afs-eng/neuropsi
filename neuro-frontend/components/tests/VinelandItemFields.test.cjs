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
const { VinelandItemFields: Fields, restoreVinelandObservations } = load();
const render = (extra = {}) => renderToStaticMarkup(React.createElement(Fields, { protocol, responses, observations: restoreVinelandObservations(protocol, responses), onObservationsChange() {}, onChange() {}, disabled: false, ...extra }));

function elements(tree) {
  if (Array.isArray(tree)) return tree.flatMap(elements);
  if (!tree || typeof tree !== 'object') return [];
  return [tree, ...elements(tree.props?.children)];
}

function interactive() {
  let active;
  const { VinelandItemFields: Component } = load({ ...React, useState(initial) { return [active ?? initial, next => { active = next; }]; } });
  let data = structuredClone(responses);
  let observations = restoreVinelandObservations(protocol, data);
  return Object.assign(() => Component({ protocol, responses: data, observations, onObservationsChange(next) { observations = next; }, onChange(next) { data = next; }, disabled: false }), { getResponses: () => data });
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
