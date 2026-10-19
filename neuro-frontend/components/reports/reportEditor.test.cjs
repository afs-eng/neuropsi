const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

function load(source, overrides = {}) {
  const filename = path.join(__dirname, source);
  const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2018 },
  }).outputText;
  const mod = new Module(filename, module);
  mod.filename = filename;
  mod.paths = module.paths;
  const original = mod.require.bind(mod);
  mod.require = (id) => overrides[id] || original(id);
  mod._compile(compiled, filename);
  return mod.exports;
}

const controls = load("ReportEditorControls.tsx", { "@/components/ui/button": { Button: ({ children, ...props }) => React.createElement("button", props, children) } });
const { ReportEditorNavigation } = load("ReportEditorNavigation.tsx");
const { ReportTestDataPanel } = load("ReportTestDataPanel.tsx", { "@/components/charts/WiscChart": { WiscChart: ({ data }) => React.createElement("div", { "data-chart-values": JSON.stringify(data) }) } });
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props));
const baseTest = (extra = {}) => ({ applicationKey: "20", name: "Teste sintético", code: "wasi", respondent: "", appliedOn: null, domain: "", summary: "", clinicalInterpretation: "", resultRows: [], structuredResults: {}, classifiedPayload: {}, computedPayload: {}, wiscTables: {}, warnings: [], ...extra });

test("workspace defaults safely and exposes only known areas", () => {
  for (const input of [null, "", "other", "<script>"]) assert.equal(controls.parseReportWorkspace(input), "editor");
  for (const input of ["tests", "specialists"]) assert.equal(controls.parseReportWorkspace(input), input);
});
test("tabs provide controls, a selected state and roving tab index", () => {
  const html = render(controls.ReportWorkspaceTabs, { value: "editor", onChange() {} });
  assert.equal((html.match(/role="tab"/g) || []).length, 3);
  assert.equal((html.match(/aria-selected="true"/g) || []).length, 1);
  assert.equal((html.match(/tabindex="0"/g) || []).length, 1);
  for (const area of ["editor", "tests", "specialists"]) assert.match(html, new RegExp(`aria-controls="report-panel-${area}"`));
});
test("tabs support arrow wrap, Home and End without triggering data actions", () => {
  let changed, focused, prevented;
  const tree = controls.ReportWorkspaceTabs({ value: "editor", onChange(value) { changed = value; } });
  const buttons = tree.props.children;
  const items = buttons.map((_, index) => ({ focus() { focused = index; } }));
  for (const [index, key, expected] of [[0, "ArrowLeft", 2], [2, "ArrowRight", 0], [1, "Home", 0], [0, "End", 2]]) {
    prevented = false;
    buttons[index].props.onKeyDown({ key, preventDefault() { prevented = true; }, currentTarget: { parentElement: { querySelectorAll: () => items } } });
    assert.equal(prevented, true);
    assert.equal(focused, expected);
    assert.equal(changed, ["editor", "tests", "specialists"][expected]);
  }
});
test("chapter navigation includes every WISC domain and only calls selection", () => {
  let selected;
  const sections = [{ id: 1, title: "Identificação" }, { id: 2, title: "Funções Executivas" }, { id: 3, title: "Linguagem" }];
  const tree = ReportEditorNavigation({ sections, activeSectionId: 2, onSelect(id) { selected = id; } });
  const html = render(ReportEditorNavigation, { sections, activeSectionId: 2, onSelect() {} });
  assert.match(html, /aria-current="true"/);
  assert.match(html, /label for="report-chapter"/);
  assert.doesNotMatch(html, /Regenera|funcoes_executivas|linguagem/);
  const nav = tree.props.children.props.children.find((child) => child?.type === "nav");
  nav.props.children[2].props.onClick();
  assert.equal(selected, 3);
});
test("report state labels do not imply approval for drafts", () => {
  assert.match(render(controls.ReportStatusBadge, { status: "draft" }), /Rascunho/);
  assert.match(render(controls.ReportStatusBadge, { status: "generating" }), /Em geração/);
  assert.match(render(controls.ReportStatusBadge, { status: "finalized" }), /Aprovado/);
});
test("test panel handles no data and no selected applications", () => {
  assert.match(render(ReportTestDataPanel, { tests: [], selected: [], onToggle() {} }), /Nenhuma aplicação validada/);
  const html = render(ReportTestDataPanel, { tests: [baseTest()], selected: [], onToggle() {} });
  assert.match(html, /Selecione uma aplicação acima/);
  assert.doesNotMatch(html, /<table/);
});
test("informants remain separate and selection does not change clinical data", () => {
  const tests = [baseTest({ respondent: "Pais", summary: "Resumo pais" }), baseTest({ applicationKey: "21", respondent: "Paciente", summary: "Resumo paciente" })];
  const html = render(ReportTestDataPanel, { tests, selected: ["20"], onToggle() {} });
  assert.match(html, /Pais/);
  assert.match(html, /Paciente/);
  assert.match(html, /Resumo pais/);
  assert.doesNotMatch(html, /Resumo paciente/);
});
test("BPA-2 zero scores, percentiles and classifications are retained in semantic tables", () => {
  const test = baseTest({ code: "bpa2", classifiedPayload: { subtestes: [{ codigo: "ac", total: 0, percentil: 1, classificacao: "Inferior" }] } });
  const html = render(ReportTestDataPanel, { tests: [test], selected: ["20"], onToggle() {} });
  assert.match(html, /<table/);
  assert.match(html, /Atenção Concentrada - AC/);
  assert.match(html, /tabular-nums">0</);
  assert.match(html, /tabular-nums">1</);
  assert.match(html, /Inferior/);
  assert.match(html, /overflow-x-auto/);
});
test("WISC chart values, domain scores and notes retain their original source", () => {
  const test = baseTest({ code: "wisc4", structuredResults: { indices: [{ nome: "ICV", escore_composto: 112 }] }, classifiedPayload: { indices: [{ indice: "icv", escore_composto: 112 }], qit_data: { escore_composto: 108 } }, wiscTables: { funcoes_executivas: [{ label: "Dígitos", maxScore: 20, avgScore: 10, minScore: 1, obtainedScore: 0, classification: "Inferior" }, { label: "Nota", note: "Ressalva preservada" }] } });
  const html = render(ReportTestDataPanel, { tests: [test], selected: ["20"], onToggle() {} });
  assert.match(html, /112/);
  assert.match(html, /108/);
  assert.match(html, /Funções Executivas/);
  assert.match(html, /tabular-nums">0</);
  assert.match(html, /colSpan="5"|colspan="5"/);
  assert.match(html, /Ressalva preservada/);
});
test("generic metric values and test warnings are preserved and escaped", () => {
  const test = baseTest({ structuredResults: { metric_results: [{ nome: "Métrica", valor: 0, percentil_num: 0, classificacao: "Média" }] }, warnings: ["Ressalva clínica"], clinicalInterpretation: "<script>not html</script>" });
  const html = render(ReportTestDataPanel, { tests: [test], selected: ["20"], onToggle() {} });
  assert.match(html, /Métrica/);
  assert.match(html, /Média/);
  assert.match(html, /Ressalva clínica/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>/);
});
