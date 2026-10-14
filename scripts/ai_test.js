/* Node test for assets/karaoke-ai.js with the real model (used by scripts/ai_prepare.py in GitHub Actions). */
const fs = require('fs'), path = require('path');
const ort = require('onnxruntime-node');
const AI = require(path.join(__dirname, '..', 'assets', 'karaoke-ai.js'));
function f32(p) { const b = fs.readFileSync(p); return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.length)); }
(async () => {
  const [model, cfgJson, work] = process.argv.slice(2), cfg = JSON.parse(cfgJson);
  const L = f32(work + '/test_L.f32'), R = f32(work + '/test_R.f32');
  const sess = await ort.InferenceSession.create(model, { intraOpNumThreads: 1, interOpNumThreads: 1 });
  let n = 0, tm = 0; const t0 = Date.now();
  const run = async (data, dims) => { const a = Date.now(); const r = await sess.run({ [sess.inputNames[0]]: new ort.Tensor('float32', data, dims) }); tm += Date.now() - a; n++; return r[sess.outputNames[0]].data; };
  const res = await AI.separate({ L, R, cfg, run, overlap: 0.25 });
  const instr = /instrument/i.test(cfg.primary);
  const pL = instr ? res.instL : res.vocL, pR = instr ? res.instR : res.vocR;
  fs.writeFileSync(work + '/js_pL.f32', Buffer.from(pL.buffer, pL.byteOffset, pL.byteLength)); fs.writeFileSync(work + '/js_pR.f32', Buffer.from(pR.buffer, pR.byteOffset, pR.byteLength));
  console.log(JSON.stringify({ chunks: n, ms_per_chunk: Math.round(tm / n), total_ms: Date.now() - t0, input: sess.inputNames[0], output: sess.outputNames[0] }));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
