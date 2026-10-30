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
  return mod.exports.VinelandItemFields;
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
const Fields = load();
const render = (extra = {}) => renderToStaticMarkup(React.createElement(Fields, { protocol, responses, onChange() {}, disabled: false, ...extra }));

function elements(tree) {
  if (Array.isArray(tree)) return tree.flatMap(elements);
  if (!tree || typeof tree !== 'object') return [];
  return [tree, ...elements(tree.props?.children)];
}

function interactive() {
  let active;
  const Component = load({ ...React, useState(initial) { return [active ?? initial, next => { active = next; }]; } });
  let data = structuredClone(responses);
  return () => Component({ protocol, responses: data, onChange(next) { data = next; }, disabled: false });
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
  assert.equal(find('vineland-item-comunicacao-1-observation').props.value, 'Não confundir com vazio.');
  find('vineland-item-comunicacao-1-observation').props.onChange({ target: { value: 'Observação atualizada.' } });
  assert.equal(find('vineland-item-comunicacao-1').props.value, 'N');
  assert.equal(find('vineland-item-comunicacao-1-observation').props.value, 'Observação atualizada.');
  const nav = elements(tree()).find(element => element.type === 'button' && element.props.children === 'Autonomia');
  nav.props.onClick();
  assert.equal(find('vineland-item-autonomia-1-observation').props.value, 'Observação sem resposta.');
  elements(tree()).find(element => element.type === 'button' && element.props.children === 'Comunicação').props.onClick();
  assert.equal(find('vineland-item-comunicacao-1').props.value, 'N');
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
  assert.equal((html.match(/disabled=""/g) || []).length, 8);
});
