const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

// Execute the actual TS/TSX without adding a browser/test dependency.
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

const progress = load("specialistProgress.ts");
const { SpecialistProgressPanel } = load("SpecialistProgressPanel.tsx", { "./specialistProgress": progress });
const start = Date.parse("2026-10-18T12:00:00Z");
const run = (extra = {}) => ({
  id: 1, application_id: 20, instrument_code: "bpa2", status: "queued", is_current: true,
  created_at: new Date(start).toISOString(), started_at: null, finished_at: null, error_code: "", ...extra,
});
const render = (extra = {}) => renderToStaticMarkup(React.createElement(SpecialistProgressPanel, {
  runs: [], requestedIds: [], submitting: false, lastUpdatedAt: start, refreshError: "", errorMessages: {}, ...extra,
}));

test("polls only current pending runs or unconfirmed requested IDs", () => {
  assert.equal(progress.shouldPollSpecialists([run()], []), true);
  assert.equal(progress.shouldPollSpecialists([run({ status: "running" })], []), true);
  for (const status of ["failed", "needs_review", "stale"]) {
    assert.equal(progress.shouldPollSpecialists([run({ status })], [1]), false);
  }
  assert.equal(progress.shouldPollSpecialists([run({ is_current: false })], []), false);
  assert.equal(progress.shouldPollSpecialists([], [1]), true);
});

test("shows latest per application or the exact requested batch, preserving failures", () => {
  const runs = [run({ id: 2, status: "failed" }), run(), run({ id: 3, application_id: 21 })];
  assert.deepEqual(progress.monitoredSpecialists(runs, []).map((r) => r.id), [3, 2]);
  assert.deepEqual(progress.monitoredSpecialists(runs, [1, 2]).map((r) => r.id), [2, 1]);
});

test("queue time and analysis time use different timestamps, completed time is fixed", () => {
  assert.equal(progress.elapsedSpecialistSeconds(run(), start + 61000), 61);
  const running = run({ status: "running", started_at: new Date(start + 10000).toISOString() });
  assert.equal(progress.elapsedSpecialistSeconds(running, start + 61000), 51);
  assert.equal(progress.elapsedSpecialistSeconds({ ...running, status: "failed", finished_at: new Date(start + 30000).toISOString() }, start + 90000), 20);
  assert.equal(progress.elapsedSpecialistSeconds(run({ created_at: "invalid" }), start), null);
  assert.equal(progress.elapsedSpecialistSeconds(run(), start - 1000), 0);
});

test("formats durations and handles unavailable timestamps", () => {
  assert.equal(progress.formatSpecialistDuration(null), "tempo indisponível");
  assert.equal(progress.formatSpecialistDuration(9), "9s");
  assert.equal(progress.formatSpecialistDuration(65), "1min 05s");
  assert.equal(progress.formatSpecialistDuration(3660), "1h 01min");
});

test("poll waits for the query before scheduling another and stops after cleanup", async () => {
  let callback;
  let scheduled = 0;
  let canceled = false;
  let finish;
  const stop = progress.startSpecialistPolling(() => new Promise((resolve) => { finish = resolve; }), (cb, ms) => {
    assert.equal(ms, 5000);
    scheduled++;
    callback = cb;
    return () => { canceled = true; };
  });
  const pending = callback();
  assert.equal(scheduled, 1);
  stop();
  finish();
  await pending;
  assert.equal(scheduled, 1);
  assert.equal(canceled, true);
});

test("poll continues after query failures and canceled timers cannot refresh", async () => {
  let callback;
  let calls = 0;
  let scheduled = 0;
  const stop = progress.startSpecialistPolling(async () => { calls++; throw Error("offline"); }, (cb) => {
    callback = cb;
    scheduled++;
    return () => {};
  });
  await callback();
  assert.equal(scheduled, 2);
  stop();
  await callback();
  assert.equal(calls, 1);
});

test("queue and running states have indeterminate bars, never fake percentages", () => {
  const queued = render({ runs: [run()] });
  assert.match(queued, /Na fila/);
  assert.match(queued, /worker local precisa estar ativo/);
  assert.match(queued, /<progress/);
  assert.doesNotMatch(queued, /value=|aria-valuenow/);
  const running = render({ runs: [run({ status: "running" })] });
  assert.match(running, /Gerando e validando/);
  assert.match(running, /não há percentual/);
});

test("success requires review; failures are visible without opening details", () => {
  const ready = render({ runs: [run({ status: "needs_review" })] });
  assert.match(ready, /Concluído — revisão necessária/);
  assert.match(ready, /laudo não foi alterado/);
  assert.match(ready, /#specialist-run-1/);
  const failed = render({ runs: [run({ status: "failed", error_code: "output_truncated" })], errorMessages: { output_truncated: "Resposta cortada." } });
  assert.match(failed, /Resposta cortada/);
  assert.match(failed, /Não haverá repetição automática/);
  assert.doesNotMatch(failed, /<progress/);
});

test("connection errors retain last-known state and do not imply model failure", () => {
  const html = render({ runs: [run()], refreshError: "Sem conexão." });
  assert.match(html, /role="alert"/);
  assert.match(html, /isso não confirma falha da IA/);
  assert.match(html, /Na fila/);
  assert.match(render({ refreshError: "Sem conexão." }), /Sem conexão/);
});

test("submission, missing confirmation and batch count are explicit", () => {
  assert.match(render({ submitting: true }), /Registrando sua solicitação/);
  assert.match(render({ requestedIds: [2] }), /processamento ainda não está confirmado/);
  const html = render({ runs: [run(), run({ id: 2, application_id: 21, status: "failed" })], requestedIds: [1, 2] });
  assert.match(html, /1 de 2 execuções encerradas/);
  assert.match(html, /max="2" value="1"/);
  assert.equal(render(), "");
});
