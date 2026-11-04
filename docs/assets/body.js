/* Body scenes for the SCAPS page, drawn by the shared Viz renderer (assets/viz.js) from window.SCAPS (assets/data.js):
   1. stack: the five-layer cell exploded to its thicknesses (log-compressed) with the band diagram floating beside it;
   2. etl: the ten-ETL screen as a two-row bar field (efficiency, short-circuit current);
   3. jv: the ten J-V curves at the best thickness as ribbons stacked by rank;
   4. sweeps: efficiency against the swept parameter for CdTe, FTO, ZnSe, the ETL and temperature, the sticky steps highlighting one;
   5. temperature: the six J-V curves from 300 to 400 K as ribbons;
   6. contact: efficiency against back-contact work function as bars. */
import { Viz } from './viz.js';
import { THREE } from './three-kit.js';
const D = window.SCAPS; const f = (v, d = 0) => (+v).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d });
const sub = s => s.replace(/(\d)/g, '$1'); const LC = { FTO: 'blue', ZnSe: 'green', CdTe: 'warm', Cs2BiAgI6: 'rose', Ni: 'steel' };

/* ---------- 1. stack and band diagram ---------- */
Viz.view('[data-viz="stack"]', v => {
  const L = D.stack; const vis = t => t === 0 ? .22 : Math.max(.16, .42 * Math.log10(1 + t * 40)); let y = -1.3; const parts = [], labs = [];
  L.forEach((s, i) => { const h = vis(s.t_um); const m = new THREE.Mesh(new THREE.BoxGeometry(2.6, h, 1.8), Viz.mat(LC[s.name] || 'steel', { roughness: .4, metalness: s.name === 'Ni' ? .7 : .1 })); m.position.set(-1.6, y + h / 2, 0); m.userData = s; v.pickables.push(m); parts.push({ mesh: m, from: [0, 2.2 + i * .3, 0], delay: i * .12, span: .3 }); labs.push(Viz.label(v, `${s.name.replace(/(\d)/g, m => '₀₁₂₃₄₅₆₇₈₉'[+m])} · ${s.t_um} µm`, [-1.6 - 1.5 - .7, y + h / 2, .4], { px: 20, scale: .085, bg: false, color: 'ink', weight: 700 })); y += h; });
  // band diagram: Ec = -chi, Ev = -(chi + Eg) per layer, drawn as steps beside the stack (energy down the page), Ni as its work function line
  const E0 = 3.0, ES = .7; const ec = [], ev = []; let x = 0; const W = 2.6 / L.length;
  L.forEach((s, i) => { if (s.name === 'Ni') return; const Ec = -(s.chi), Ev = -(s.chi + s.Eg); ec.push([1.2 + x, (Ec + E0) * ES, 0], [1.2 + x + W, (Ec + E0) * ES, 0]); ev.push([1.2 + x, (Ev + E0) * ES, 0], [1.2 + x + W, (Ev + E0) * ES, 0]); x += W; });
  const lEc = Viz.line(v, ec, 'cyan'), lEv = Viz.line(v, ev, 'rose'); lEc.geometry.setDrawRange(0, 0); lEv.geometry.setDrawRange(0, 0);
  const ni = L.find(s => s.name === 'Ni'); const phi = ni ? (ni.chi || 5.55) : 5.55; const lNi = Viz.line(v, [[1.2 + x, (-phi + E0) * ES, 0], [1.2 + x + .5, (-phi + E0) * ES, 0]], 'steel'); lNi.geometry.setDrawRange(0, 0);
  const bl = [Viz.label(v, 'E_c', [1.0, (-(L[0].chi) + E0) * ES + .05, 0], { px: 20, scale: .085, bg: false, color: 'cyan', weight: 700 }), Viz.label(v, 'E_v', [1.0, (-(L[0].chi + L[0].Eg) + E0) * ES - .05, 0], { px: 20, scale: .085, bg: false, color: 'rose', weight: 700 }), Viz.label(v, 'Ni φ = 5.55 eV', [1.2 + x + .9, (-phi + E0) * ES, 0], { px: 19, scale: .08, bg: false, color: 'steel', weight: 700 }), Viz.label(v, 'band alignment, eV below vacuum', [2.2, (-(L[0].chi) + E0) * ES + .5, 0], { px: 20, scale: .085, bg: false, color: 'ink', weight: 700 })];
  const ex = Viz.exploded(v, parts);
  v.update = vv => { ex.draw(vv.p); labs.forEach((l, i) => l.material.opacity = Math.max(0, (vv.p - i * .12 - .2) * 4)); const b = Math.max(0, Math.min(1, (vv.p - .55) / .4)); lEc.geometry.setDrawRange(0, Math.floor(ec.length * b)); lEv.geometry.setDrawRange(0, Math.floor(ev.length * b)); lNi.geometry.setDrawRange(0, b > .95 ? 2 : 0); bl.forEach(l => l.material.opacity = b); return false; };
  v.hover = hit => { const s = hit.object.userData; return s && s.name ? `<b>${s.name}, ${s.t_um} µm</b>${s.role} · ${s.type} · E<sub>g</sub> ${s.Eg} eV, χ ${s.chi} eV` : null; };
  v.rig.position.x = .9; v.rot = .25; v.tilt = .15;
}, { camera: [0, 1.4, 8.2], target: [.2, -.1, 0], fov: 34 });

/* ---------- 2. the ten-ETL screen ---------- */
Viz.view('[data-viz="etl"]', v => {
  const R = D.ranking; const A = Viz.axes(v, { size: [5.0, 2.2, 1.6], x: { lo: -.5, hi: R.length - .5, ticks: [] }, y: { lo: 0, hi: 30, ticks: [0, 10, 20, 30], label: 'PCE, % · J_SC, mA/cm²' }, z: { lo: -.5, hi: 1.5, ticks: [] } });
  const items = []; R.forEach((r, i) => { items.push({ x: i, z: 0, y: r[5], color: i === 0 ? 'rose' : r[5] > 20 ? 'warm' : r[5] > 5 ? 'cyan' : 'grey', name: `${r[0]}: PCE`, raw: `${r[5].toFixed(2)} % at ${r[1]} µm (V_OC ${r[2].toFixed(3)} V, FF ${r[4].toFixed(1)} %)` }); items.push({ x: i, z: 1, y: r[3], color: 'blue', name: `${r[0]}: J_SC`, raw: `${r[3].toFixed(2)} mA/cm²` }); });
  const B = Viz.bars(v, A, items, { width: .32, depth: .4 });
  R.forEach((r, i) => { const p = A.map(i, r[5], 0); Viz.label(v, r[5].toFixed(2), [p.x, p.y + .16, p.z], { px: 18, scale: .08 }); Viz.label(v, r[0].replace(/(\d)/g, m => '₀₁₂₃₄₅₆₇₈₉'[+m]), [p.x, A.map(0, 0).y - .25, A.map(0, 0, -.5).z - .1], { px: 17, scale: .075, bg: false, color: 'ink' }); });
  Viz.label(v, 'PCE', [A.map(R.length - .2, 0, 0).x + .3, A.map(0, 0).y + .1, A.map(0, 0, 0).z], { px: 19, scale: .08, bg: false, color: 'ink', weight: 700 }); Viz.label(v, 'J_SC', [A.map(R.length - .2, 0, 1).x + .3, A.map(0, 0).y + .1, A.map(0, 0, 1).z], { px: 19, scale: .08, bg: false, color: 'blue', weight: 700 });
  v.update = vv => { B.draw(vv.p); return false; };
  v.hover = hit => { const it = items[hit.instanceId]; return it ? `<b>${it.name}</b>${it.raw}` : null; };
  v.rot = -.3; v.tilt = .12;
}, { camera: [0, 2.2, 8.0], target: [0, -.2, 0], fov: 32 });

/* ---------- 3. J-V curves ---------- */
Viz.view('[data-viz="jv"]', v => {
  const R = D.ranking; const A = Viz.axes(v, { size: [4.4, 2.2, 3.0], x: { lo: 0, hi: 1.3, ticks: [0, .4, .8, 1.2], label: 'voltage, V' }, y: { lo: 0, hi: 28, ticks: [0, 10, 20], label: 'J, mA/cm²' }, z: { lo: -.5, hi: R.length - .5, ticks: [] } });
  const cols = ['rose', 'warm', 'warm', 'cyan', 'cyan', 'cyan', 'green', 'violet', 'grey', 'grey'];
  const rbs = R.map((r, i) => { const jv = D.etl[r[0]].jv_best.filter(p => p[1] >= 0); const rb = Viz.ribbon(v, A, jv.map(p => p[0]), jv.map(p => p[1]), { color: cols[i] || 'grey', width: .16, z: i, name: r[0], unit: 'mA/cm²', skirtOpacity: .06 }); rb.mesh.userData.r = r; const lab = Viz.label(v, `${r[0].replace(/(\d)/g, m => '₀₁₂₃₄₅₆₇₈₉'[+m])} ${r[5].toFixed(1)} %`, [A.map(-.05, 0, i).x - .55, A.map(0, jv[0][1]).y + .05, A.map(0, 0, i).z], { px: 18, scale: .078, bg: false, color: cols[i] || 'grey', weight: 700 }); return { rb, lab }; });
  v.update = vv => { rbs.forEach((r, i) => { const p = Math.max(0, Math.min(1, vv.p * 1.4 - i * .045)); r.rb.draw(p); r.lab.material.opacity = p > .9 ? 1 : 0; }); return false; };
  v.hover = hit => { const r = hit.object.userData.r; if (!r) return null; const i = Viz.ribbonIndex(hit, A); const u = hit.object.userData; return `<b>${r[0]} at ${r[1]} µm</b>${f(u.ys[i], 2)} mA/cm² at ${f(u.xs[i], 3)} V · PCE ${r[5].toFixed(2)} %`; };
  v.rot = -.55; v.tilt = .15;
}, { camera: [0, 2.6, 8.4], target: [0, -.3, 0], fov: 32 });

/* ---------- 4. sweeps (sticky) ---------- */
const sweepView = Viz.view('[data-viz="sweeps"]', v => {
  const keys = [['CdTe', 'CdTe absorber', 'warm'], ['FTO', 'FTO front contact', 'blue'], ['ZnSe', 'ZnSe buffer', 'green'], ['ETL', 'Cs₂BiAgI₆ ETL', 'rose'], ['T', 'temperature 300 → 400 K', 'violet']];
  const rows = k => k === 'T' ? D.temperature.map(r => ({ x: r.T, ...r })) : D.layers[k].map(r => ({ x: r.thickness, ...r }));
  const A = Viz.axes(v, { size: [3.6, 2.2, 3.2], x: { lo: 0, hi: 1, ticks: [0, .5, 1], fmt: t => t === 0 ? 'start' : t === 1 ? 'end' : '', label: 'swept range' }, y: { lo: 22, hi: 28.5, ticks: [23, 25, 27], label: 'PCE, %' }, z: { lo: -.5, hi: keys.length - .5, ticks: [] } });
  const sets = keys.map(([k, name, col], i) => { const rs = rows(k); const xs = rs.map(r => (r.x - rs[0].x) / ((rs[rs.length - 1].x - rs[0].x) || 1)); const rb = Viz.ribbon(v, A, xs, rs.map(r => r.PCE), { color: col, width: .22, z: i, name, unit: '%' }); rb.mesh.userData.rows = rs; rb.mesh.userData.k = k; const lab = Viz.label(v, name, [A.map(1.06, 0, i).x + .5, A.map(0, rs[rs.length - 1].PCE).y, A.map(0, 0, i).z], { px: 19, scale: .08, color: col, weight: 700 }); return { rb, lab, k }; });
  v.sel = 'CdTe';
  v.update = vv => { sets.forEach((s, i) => { const p = Math.max(0, Math.min(1, vv.p * 1.3 - i * .08)); s.rb.draw(p); const on = s.k === vv.sel; s.rb.mesh.material.opacity = on ? 1 : .3; s.rb.mesh.material.transparent = true; s.rb.mesh.material.emissiveIntensity = on ? .5 : .1; s.lab.material.opacity = p > .9 ? (on ? 1 : .4) : 0; }); return false; };
  v.hover = hit => { const rs = hit.object.userData.rows; if (!rs) return null; const i = Viz.ribbonIndex(hit, A); const r = rs[Math.min(rs.length - 1, Math.round(i * (rs.length - 1) / (hit.object.userData.xs.length - 1)))]; return `<b>${hit.object.userData.series}: ${hit.object.userData.k === 'T' ? r.x + ' K' : r.x + ' µm'}</b>PCE ${r.PCE.toFixed(2)} % · V_OC ${r.Voc.toFixed(3)} V · J_SC ${r.Jsc.toFixed(2)} · FF ${r.FF.toFixed(1)} %`; };
  v.rot = -.5; v.tilt = .15;
}, { camera: [0, 2.4, 8.2], target: [0, -.2, 0], fov: 32 });
document.addEventListener('scaps-step', e => { if (sweepView) { sweepView.sel = e.detail; sweepView.dirty = true; } });

/* ---------- 5. temperature J-V ---------- */
Viz.view('[data-viz="temperature"]', v => {
  const Ts = Object.keys(D.jv_temperature).sort((a, b) => +a - +b); const A = Viz.axes(v, { size: [4.4, 2.2, 2.4], x: { lo: 0, hi: 1.3, ticks: [0, .4, .8, 1.2], label: 'voltage, V' }, y: { lo: 0, hi: 28, ticks: [0, 10, 20], label: 'J, mA/cm²' }, z: { lo: -.5, hi: Ts.length - .5, ticks: [] } });
  const cols = ['cyan', 'green', 'warm', 'warm', 'hot', 'rose'];
  const rbs = Ts.map((T, i) => { const jv = D.jv_temperature[T].filter(p => p[1] >= 0); const row = D.temperature.find(r => +r.T === +T); const rb = Viz.ribbon(v, A, jv.map(p => p[0]), jv.map(p => p[1]), { color: cols[i], width: .18, z: i, name: `${+T} K`, unit: 'mA/cm²', skirtOpacity: .06 }); rb.mesh.userData.row = row; const lab = Viz.label(v, `${+T} K · ${row ? row.PCE.toFixed(2) : ''} %`, [A.map(-.05, 0, i).x - .55, A.map(0, jv[0][1]).y + .05, A.map(0, 0, i).z], { px: 18, scale: .078, bg: false, color: cols[i], weight: 700 }); return { rb, lab }; });
  Viz.label(v, `V_OC ${D.voc_slope_mV_per_K} mV/K · PCE ${D.pce_slope_per_K} points/K`, [0, A.map(0, 28).y + .35, A.map(0, 0, -.5).z], { px: 20, scale: .085, color: 'ink', weight: 700 });
  v.update = vv => { rbs.forEach((r, i) => { const p = Math.max(0, Math.min(1, vv.p * 1.3 - i * .06)); r.rb.draw(p); r.lab.material.opacity = p > .9 ? 1 : 0; }); return false; };
  v.hover = hit => { const row = hit.object.userData.row; if (!row) return null; const i = Viz.ribbonIndex(hit, A); const u = hit.object.userData; return `<b>${row.T} K</b>${f(u.ys[i], 2)} mA/cm² at ${f(u.xs[i], 3)} V · V_OC ${row.Voc.toFixed(3)} V, PCE ${row.PCE.toFixed(2)} %`; };
  v.rot = -.5; v.tilt = .15;
}, { camera: [0, 2.4, 8.0], target: [0, -.3, 0], fov: 32 });

/* ---------- 6. back contact ---------- */
Viz.view('[data-viz="contact"]', v => {
  const B0 = [...D.back_contact].sort((a, b) => a[1] - b[1]); const A = Viz.axes(v, { size: [4.6, 2.2, 1.2], x: { lo: 4.1, hi: 6.1, ticks: [4.5, 5, 5.5, 6], label: 'metal work function, eV' }, y: { lo: 0, hi: 30, ticks: [0, 10, 20, 30], label: 'PCE, %' }, z: { lo: -.5, hi: .5, ticks: [] } });
  const items = B0.map(b => ({ x: b[1], z: 0, y: b[2], color: b[0] === 'Ni' ? 'rose' : b[1] >= 5.4 ? 'green' : 'warm', name: b[0], raw: `φ ${b[1].toFixed(2)} eV → ${b[2].toFixed(2)} %, hole barrier ≈ ${Math.max(0, 5.4 - b[1]).toFixed(1)} eV` }));
  const B = Viz.bars(v, A, items, { width: .18, depth: .5 });
  items.forEach(it => { const p = A.map(it.x, it.y, 0); Viz.label(v, it.name, [p.x, p.y + .18, p.z], { px: 19, scale: .085, weight: 700, color: it.name === 'Ni' ? 'rose' : 'ink' }); });
  const bx = A.map(5.4, 0, 0).x; const line = Viz.line(v, [[bx, A.map(0, 0).y, -.7], [bx, A.map(0, 30).y, -.7]], 'ink'); line.material.transparent = true; line.material.opacity = .6; Viz.label(v, 'CdTe valence band 5.4 eV:\nno hole barrier beyond', [bx + .2, A.map(0, 30).y - .1, -.6], { px: 19, scale: .08 });
  v.update = vv => { B.draw(vv.p); return false; };
  v.hover = hit => { const it = items[hit.instanceId]; return it ? `<b>${it.name}</b>${it.raw}` : null; };
  v.rot = -.25; v.tilt = .1;
}, { camera: [0, 2.0, 7.4], target: [0, -.2, 0], fov: 32 });
