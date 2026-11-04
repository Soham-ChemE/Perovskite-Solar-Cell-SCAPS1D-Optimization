/* Hero scene for the SCAPS-1D page: the layer stack exploding and stacking with scroll, the band-alignment ribbon lighting up, and
   the ten-ETL sweep rising as bars. Data: window.SCAPS from assets/data.js (built from the raw SCAPS-1D exports). */
import { THREE, createStage, cameraPath } from './three-kit.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const D = window.SCAPS, S = window.SITE, reduced = S.reduced, phone = S.phone;
const textSprite = (txt, color, w = 2.4) => { const c = document.createElement('canvas'); c.width = 512; c.height = 96; const g = c.getContext('2d'); g.font = '600 40px -apple-system,Segoe UI,Roboto,Helvetica,Arial'; g.fillStyle = color; g.textAlign = 'center'; g.fillText(txt, 256, 62); const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false })); s.scale.set(w, w * 96 / 512, 1); return s; };
const sub = s => s.replace(/(\d)/g, m => '₀₁₂₃₄₅₆₇₈₉'[+m]);

(function () {
  const canvas = document.getElementById('heroCanvas'); if (!canvas) return;
  const st = createStage(canvas, { fov: 36, bloom: { strength: .35, radius: .45, threshold: .85 }, dof: { aperture: .0004, maxblur: .003 }, exposure: 1.0, envIntensity: .5 });
  if (st.failed) return; const { scene, camera } = st;
  // dark stage in both themes so the band diagram and bars read (the page shade blends it into the page colour)
  const ctr = new OrbitControls(camera, canvas); ctr.enableDamping = true; ctr.enableZoom = false; ctr.enablePan = false; ctr.autoRotate = !reduced; ctr.autoRotateSpeed = .45; ctr.minPolarAngle = .7; ctr.maxPolarAngle = 1.45;
  const hemi = new THREE.HemisphereLight(0xffffff, 0x223355, .9); scene.add(hemi); const dl = new THREE.DirectionalLight(0xffffff, 1.4); dl.position.set(4, 8, 6); scene.add(dl);
  const COL = { FTO: 0x60a5fa, ZnSe: 0x34d399, CdTe: 0xf59e0b, Cs2BiAgI6: 0xf87171, Ni: 0x94a3b8 }; const LAB = { FTO: 'FTO 0.4 µm', ZnSe: 'ZnSe 0.025 µm', CdTe: 'CdTe 3 µm', Cs2BiAgI6: 'Cs₂BiAgI₆ 2 µm', Ni: 'Ni back contact' };
  const vis = t => t === 0 ? .25 : Math.max(.16, .42 * Math.log10(1 + t * 40)); const W = 4.2, Dp = 3.0; const g = new THREE.Group(); scene.add(g);
  const layers = []; let y = 0; const order = [...D.stack].reverse(); const dark = () => true; // labels always for the dark stage
  order.forEach((L, i) => { const h = vis(L.t_um); const m = new THREE.Mesh(new THREE.BoxGeometry(W, h, Dp), new THREE.MeshStandardMaterial({ color: COL[L.name], roughness: .4, metalness: L.name === 'Ni' ? .75 : .1, transparent: true, opacity: .95, emissive: COL[L.name], emissiveIntensity: .08 })); m.position.y = y + h / 2; m.userData = { base: y + h / 2, i, L }; g.add(m); layers.push(m); y += h; const s = textSprite(LAB[L.name], dark() ? '#e6edf3' : '#0b1220', 2.0); s.position.set(W / 2 + 1.0, y - h / 2, Dp / 2); g.add(s); m.userData.label = s; });
  const stackH = y;
  // band alignment ribbon: CB at -chi, VB at -(chi + Eg) against vacuum; metal Fermi level at -phi
  const band = new THREE.Group(); band.position.set(W / 2 + 3.9, 0, -Dp / 2); g.add(band); const E = v => (v + 3.6) * 1.1;
  const mkLine = (pts, color) => new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color, transparent: true }));
  const segs = []; let yy = 0; order.forEach(L => { const h = vis(L.t_um); const y0 = yy, y1 = yy + h; if (L.Eg > 0) segs.push({ L, y0, y1, c: -L.chi, v: -(L.chi + L.Eg) }); else segs.push({ L, y0, y1, f: -L.chi }); yy += h; });
  segs.forEach(s => { const col = COL[s.L.name]; if (s.c !== undefined) { band.add(mkLine([new THREE.Vector3(E(s.c), s.y0, 0), new THREE.Vector3(E(s.c), s.y1, 0)], col)); band.add(mkLine([new THREE.Vector3(E(s.v), s.y0, 0), new THREE.Vector3(E(s.v), s.y1, 0)], col)); const gap = new THREE.Mesh(new THREE.PlaneGeometry(E(s.c) - E(s.v), s.y1 - s.y0), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: .18, side: THREE.DoubleSide })); gap.position.set((E(s.c) + E(s.v)) / 2, (s.y0 + s.y1) / 2, 0); band.add(gap); } else band.add(mkLine([new THREE.Vector3(E(s.f) - .3, s.y0, 0), new THREE.Vector3(E(s.f) + .3, s.y1, 0)], col)); });
  for (let i = 0; i < segs.length - 1; i++) { const a = segs[i], b = segs[i + 1]; if (a.c !== undefined && b.c !== undefined) { band.add(mkLine([new THREE.Vector3(E(a.c), a.y1, 0), new THREE.Vector3(E(b.c), b.y0, 0)], 0x8b98a9)); band.add(mkLine([new THREE.Vector3(E(a.v), a.y1, 0), new THREE.Vector3(E(b.v), b.y0, 0)], 0x8b98a9)); } }
  const axisLab = [textSprite('E vs vacuum: −3.6 … −5.6 eV', dark() ? '#8b98a9' : '#5b6676', 2.6), textSprite('conduction band', dark() ? '#8b98a9' : '#5b6676', 1.6), textSprite('valence band', dark() ? '#8b98a9' : '#5b6676', 1.4)];
  axisLab[0].position.set(E(-4.6), -.5, 0); axisLab[1].position.set(E(-3.9), stackH + .4, 0); axisLab[2].position.set(E(-5.4), stackH + .4, 0); axisLab.forEach(s => band.add(s));
  const arrows = []; for (let i = -1; i <= 1; i++) { const a = new THREE.ArrowHelper(new THREE.Vector3(0, -1, 0), new THREE.Vector3(i * 1.1, stackH + 1.6, 0), 1.1, 0xfde68a, .3, .18); g.add(a); arrows.push(a); }
  const sun = textSprite('AM 1.5G, 1000 W/m²', '#fde68a', 2.2); sun.position.set(0, stackH + 2.1, 0); g.add(sun);
  // the ten-ETL sweep: one bar per electron-transport layer at its best thickness, behind the stack, rising in the last third
  const bars = new THREE.Group(); bars.position.set(-W / 2 - 1.2, 0, -Dp / 2 - 2.6); g.add(bars); const barList = [];
  const rank = D.ranking; const bw = .62, gapw = .22; const totalW = rank.length * (bw + gapw);
  rank.forEach((r, i) => { const h = Math.max(.02, r[5] / 28 * 3.2); const best = i === 0; const col = best ? 0xf87171 : (r[5] > 20 ? 0xf59e0b : r[5] > 5 ? 0x22d3ee : 0x64748b); const m = new THREE.Mesh(new THREE.BoxGeometry(bw, h, bw), new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: best ? .5 : .2, roughness: .4 })); m.position.set(-totalW + i * (bw + gapw), h / 2, 0); m.scale.y = .001; const lab = textSprite(`${sub(r[0])} ${r[5].toFixed(2)} %`, best ? '#f87171' : (dark() ? '#e6edf3' : '#0b1220'), 1.9); lab.position.set(m.position.x, h + .28, 0); lab.visible = false; bars.add(m, lab); barList.push({ m, lab, h }); });
  const barTitle = textSprite('Ten electron-transport layers, PCE at best thickness', dark() ? '#8b98a9' : '#5b6676', 3.4); barTitle.position.set(-totalW / 2, 3.8, 0); barTitle.visible = false; bars.add(barTitle);
  st.onTheme = () => { hemi.intensity = .9 * st.lights; dl.intensity = 1.4 * st.lights; st.dirty = true; }; st.onTheme();
  // readout
  const ro = { name: document.getElementById('roName'), t: document.getElementById('roT'), eg: document.getElementById('roEg'), chi: document.getElementById('roChi'), role: document.getElementById('roRole') }; let focus = -1;
  function setFocus(i) { if (i === focus || !ro.name) return; focus = i; const L = order[i]; ro.name.textContent = sub(L.name); ro.t.textContent = L.t_um ? L.t_um + ' µm' : 'metal'; ro.eg.textContent = L.Eg ? L.Eg.toFixed(2) + ' eV' : '–'; ro.chi.textContent = L.chi.toFixed(2) + ' eV' + (L.Eg ? '' : ' (φ)'); ro.role.textContent = L.role; }
  // layout and camera path: three-quarter view of the exploded stack -> square on the stacked device and its band diagram -> pulled back to take in the bars
  const wide = () => st.wide !== false;
  function layout() { const w = wide(); g.position.set(w ? 3.0 : 0, w ? -stackH / 2 - .4 : -stackH / 2 + 1.2, 0); g.scale.setScalar(w ? .8 : .5); band.visible = w; }
  const pathWide = cameraPath([[8.5, 5, 11.5], [6.5, 2.6, 9.5], [5.8, 3.4, 10.5], [2.5, 4.8, 12.5]], [[2.2, .2, 0], [2.6, 0, 0], [3.5, .3, 0], [2.0, 1.0, -1.0]]);
  const pathNarrow = cameraPath([[0, 4, 11], [1.5, 2, 8.5], [0, 2.5, 9.5], [-1, 4.5, 11.5]], [[0, 1.6, 0], [0, 1.0, 0], [0, 1.2, 0], [-.5, 1.6, -1]]);
  const pos3 = new THREE.Vector3(), tgt3 = new THREE.Vector3(); let dragging = false, lastT = -1;
  canvas.addEventListener('pointerdown', () => dragging = true); addEventListener('pointerup', () => setTimeout(() => dragging = false, 2500)); ctr.addEventListener('change', () => st.dirty = true);
  layout(); (wide() ? pathWide : pathNarrow).at(reduced ? 1 : 0, pos3, tgt3); camera.position.copy(pos3); ctr.target.copy(tgt3); ctr.update();
  st.loop((t) => {
    const T = S.hero.t; let changed = false; layout();
    const q = reduced ? 1 : Math.max(0, Math.min(1, T / .5)); const ex = (1 - q) * 1.0;
    layers.forEach(m => { const ny = m.userData.base + m.userData.i * ex; if (Math.abs(m.position.y - ny) > 1e-4) { m.position.y = ny; m.userData.label.position.y = ny; changed = true; } });
    band.children.forEach(c => { if (c.material && 'opacity' in c.material && !c.isSprite) { c.material.transparent = true; c.material.opacity = (c.isMesh ? .18 : .9) * q + (c.isMesh ? .05 : .25); } });
    arrows.forEach((a, i) => { a.position.y = stackH + 1.6 + (layers.length - 1) * ex + (reduced ? 0 : .15 * Math.sin(t * 3 + i)); }); sun.position.y = stackH + 2.3 + (layers.length - 1) * ex; if (!reduced) changed = true;
    const grow = reduced ? 1 : Math.max(0, Math.min(1, (T - .62) / .3)); barList.forEach((b, k) => { const gg = Math.max(.001, Math.min(1, grow * 1.4 - k * .04)); if (Math.abs(b.m.scale.y - gg) > 1e-4) { b.m.scale.y = gg; b.m.position.y = b.h * gg / 2; changed = true; } b.lab.visible = gg >= .999; }); barTitle.visible = grow > .15;
    const idx = Math.min(order.length - 1, Math.floor(Math.max(0, Math.min(.999, T / .6)) * order.length)); setFocus(order.length - 1 - idx);
    (wide() ? pathWide : pathNarrow).at(reduced ? 1 : T, pos3, tgt3);
    if (!dragging && camera.position.distanceToSquared(pos3) > 1e-6) { camera.position.lerp(pos3, reduced ? 1 : .08); changed = true; }
    ctr.target.lerp(tgt3, .08); ctr.autoRotate = !reduced && T < .05 && !dragging; if (ctr.autoRotate || dragging) changed = true; ctr.update();
    st.setBloom(.3 + .25 * S.hero.glow); if (st.bokeh) st.bokeh.uniforms.focus.value = camera.position.distanceTo(ctr.target);
    if (Math.abs(T - lastT) > 1e-4) { lastT = T; changed = true; }
    return changed;
  });
})();
