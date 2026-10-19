const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

const filename = path.join(__dirname, "ReportPreparationPanel.tsx");
const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2018 },
}).outputText;
const mod = new Module(filename, module);
mod.filename = filename;
mod.paths = module.paths;
const original = mod.require.bind(mod);
mod.require = (id) => {
  if (id === "@/components/ui/button") return { Button: ({ children, ...props }) => React.createElement("button", props, children) };
  if (id === "@/lib/api") return { api: {} };
  return original(id);
};
mod._compile(compiled, filename);
const { ReportPreparationView } = mod.exports;

const data = {
  enabled: true, can_prepare: true, ready_for_execution: false,
  blockers: [], applications: [], targets: [], limitations: ["Não agenda IA."], latest: null,
};
function render(extra = {}) {
  return renderToStaticMarkup(React.createElement(ReportPreparationView, {
    data, loading: false, submitting: false, error: "", notice: "", selectedReport: "",
    onSelect() {}, onRefresh() {}, onPrepare() {}, ...extra,
  }));
}
function prepareButton(html) {
  return html.match(/<button[^>]*>Preparar laudo com IA<\/button>/)?.[0];
}

test("disabled flag hides the new feature", () => {
  assert.equal(render({ data: { enabled: false } }), "");
});
test("first delivery is clearly inventory only, without fake progress", () => {
  const html = render();
  assert.match(html, /Ainda não gera interpretações ou altera o laudo/);
  assert.doesNotMatch(html, /progressbar|\d+%|worker online/i);
  assert.doesNotMatch(prepareButton(html), /disabled/);
});
test("unknown, loading, unavailable and failed status cannot submit", () => {
  for (const props of [{ data: null }, { loading: true }, { data: { ...data, can_prepare: false } }, { error: "Sem conexão" }]) {
    assert.match(prepareButton(render(props)), /disabled/);
  }
  assert.match(render({ error: "Sem conexão" }), /role="alert"/);
});
test("submission is busy, visible and disables both actions", () => {
  const html = render({ submitting: true });
  assert.match(html, /aria-busy="true"/);
  assert.match(html, /Registrando fontes/);
  assert.equal((html.match(/<button[^>]*disabled=""/g) || []).length, 2);
});
test("applications are separate and unsupported coverage is explicit", () => {
  const html = render({ data: { ...data, applications: [
    { application_id: 1, instrument_name: "SCARED", validated: true, supported: true, enabled: true },
    { application_id: 2, instrument_name: "SCARED", validated: false, supported: false, enabled: false },
  ] } });
  assert.match(html, /aplicação #1/);
  assert.match(html, /aplicação #2/);
  assert.match(html, /Sem especialista/);
  assert.match(html, /Não validada/);
  assert.match(html, /homologação não verificada/);
});
test("source changes and unavailable stages never look clinically approved", () => {
  const html = render({ data: { ...data, latest: {
    id: 4, report_id: 10, status: "stale", created_at: "2026-10-18T12:00:00Z",
    steps: [{ key: "preflight", title: "Pré-checagem", status: "completed" }, { key: "synthesis", title: "Síntese", status: "unavailable" }],
  } } });
  assert.match(html, /Fontes alteradas/);
  assert.match(html, /não é aprovação clínica/);
  assert.match(html, /não disponível nesta entrega/);
  assert.match(html, /Nenhuma IA agendada/);
  assert.match(html, /href="\/dashboard\/reports\/10"/);
});
test("server messages and instrument titles are rendered as text, not HTML", () => {
  const html = render({ data: { ...data, blockers: [{ code: "missing", message: "<script>unsafe()</script>", application_id: 7 }] } });
  assert.match(html, /Aplicação #7/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>/);
});
test("multiple targets use an accessible explicit selector", () => {
  const html = render({ data: { ...data, targets: [{ id: 8, title: "Revisão", status: "draft" }] }, selectedReport: "8" });
  assert.match(html, /for="preparation-target-report"/);
  assert.match(html, /value="8" selected=""/);
  assert.match(html, /Revisão \(Rascunho\)/);
});
