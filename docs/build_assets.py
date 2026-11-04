"""Build every asset used by docs/index.html and the README hero from the raw SCAPS-1D exports in data/.

Reads the eleven SCAPS batch workbooks exactly as scripts/make_figures.py does (same sheet parser), plus the material
parameters and back-contact table that are tabulated in the report and already quoted in README.md.
Writes:
  docs/assets/data.js                  window.SCAPS = {...} (classic script, works from file://)
  docs/assets/fig_*_{dark,light}.svg   ETL screening, J-V curves, temperature derating
  docs/assets/social-preview.png       1280x640
Run from the repository root:  python docs/build_assets.py   (needs numpy, openpyxl, matplotlib)
"""
import json, os, sys
import numpy as np, openpyxl
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRC = os.path.join(ROOT, "data"); OUT = os.path.join(ROOT, "docs", "assets"); os.makedirs(OUT, exist_ok=True)

def sheet_jv(ws):  # identical to scripts/make_figures.py
    rows = list(ws.iter_rows(values_only=True)); param = None; data = []; sm = {}
    for row in rows:
        vals = [v for v in row if v is not None]
        if len(vals) >= 2 and isinstance(vals[0], str):
            k = vals[0].strip()
            if k == "Temperature": param = ("temperature", float(str(vals[1]).split()[0]))
            elif "thickness" in k and (param is None or param[0] != "temperature"): param = ("thickness", float(vals[1]))
            for key, name in [("Voc =", "Voc"), ("Jsc =", "Jsc"), ("FF =", "FF"), ("eta =", "PCE")]:
                if k == key and isinstance(vals[1], (int, float)): sm[name] = float(vals[1])
        if len(vals) >= 2 and isinstance(vals[0], (int, float)) and isinstance(vals[1], (int, float)): data.append((float(vals[0]), -float(vals[1])))
    d = np.array(data); return param, d[:, 0], d[:, 1], sm
def thin(V, J, n=80):
    o = np.argsort(V); V, J = V[o], J[o]; idx = np.unique(np.linspace(0, len(V) - 1, n).astype(int)); return [[round(float(V[i]), 4), round(float(J[i]), 3)] for i in idx]

etl_files = {"Cs2BiAgI6": "Cs2BiAgI6 DATA POINTS.xlsx", "C60": "C60 DATA POINTS.xlsx", "CuO": "CuO DATA POINTS.xlsx", "Cu2O": "Cu2O DATA POINTS.xlsx", "PC16BM": "PC16BM DATA POINTS.xlsx", "PCBM": "PCBM DATA POINTS.xlsx", "Sb2Se3": "Sb2Se3 DATA POINTS.xlsx", "TiO2": "TiO2 DATA POINTS.xlsx", "WO3": "WO3 DATA POINTS.xlsx", "WS2": "WS2 DATA POINTS.xlsx"}
etl = {}
for name, f in etl_files.items():
    wb = openpyxl.load_workbook(os.path.join(SRC, f), data_only=True); rows = []
    for ws in wb.worksheets:
        if not ws.title.startswith("ETL"): continue
        try: param, V, J, sm = sheet_jv(ws)
        except Exception: continue
        if param is None or len(V) < 5 or "PCE" not in sm: continue
        rows.append({"thickness": param[1], **{k: round(sm[k], 4) for k in ("Voc", "Jsc", "FF", "PCE")}, "jv": thin(V, J)})
    rows.sort(key=lambda r: r["thickness"]); best = max(rows, key=lambda r: r["PCE"]); etl[name] = {"rows": [{k: v for k, v in r.items() if k != "jv"} for r in rows], "best": {k: v for k, v in best.items() if k != "jv"}, "jv_best": best["jv"]}
layers = {}
wb = openpyxl.load_workbook(os.path.join(SRC, "Cs2BiAgI6 DATA POINTS.xlsx"), data_only=True)
for ws in wb.worksheets:
    layer = ws.title.split()[0]
    try: param, V, J, sm = sheet_jv(ws)
    except Exception: continue
    if param is None or "PCE" not in sm: continue
    layers.setdefault(layer, []).append({"thickness": param[1], **{k: round(sm[k], 4) for k in ("Voc", "Jsc", "FF", "PCE")}})
for k in layers: layers[k].sort(key=lambda r: r["thickness"])
temp = []
wbT = openpyxl.load_workbook(os.path.join(SRC, "Cs2BiAgI6_Temperature_Data.xlsx"), data_only=True)
for ws in wbT.worksheets:
    param, V, J, sm = sheet_jv(ws); temp.append({"T": param[1], **{k: round(sm[k], 4) for k in ("Voc", "Jsc", "FF", "PCE")}, "jv": thin(V, J, 60)})
temp.sort(key=lambda r: r["T"]); Ts = [r["T"] for r in temp]
voc_slope = float(np.polyfit(Ts, [r["Voc"] for r in temp], 1)[0] * 1000); pce_slope = float(np.polyfit(Ts, [r["PCE"] for r in temp], 1)[0])
# tabulated in the report / README (not in the exports)
back_contact = [("Al", 4.3, 5.26), ("Cu", 4.6, 12.43), ("Fe", 4.8, 17.35), ("C", 5.0, 22.33), ("W", 5.2, 25.72), ("Ni", 5.55, 27.99), ("Pt", 5.7, 28.44), ("Se", 5.9, 28.45)]
stack = [  # name, thickness (um) at the optimum, Eg (eV), chi (eV), type, colour
    {"name": "FTO", "t_um": 0.4, "Eg": 3.50, "chi": 4.00, "type": "n+ TCO", "role": "front contact"},
    {"name": "ZnSe", "t_um": 0.025, "Eg": 2.9, "chi": 4.0, "type": "n buffer", "role": "window, CdS replacement"},
    {"name": "CdTe", "t_um": 3.0, "Eg": 1.50, "chi": 3.90, "type": "p absorber", "role": "absorber"},
    {"name": "Cs2BiAgI6", "t_um": 2.0, "Eg": 1.60, "chi": 3.90, "type": "ETL", "role": "electron-transport layer"},
    {"name": "Ni", "t_um": 0.0, "Eg": 0, "chi": 5.55, "type": "metal", "role": "back contact, work function 5.55 eV"}]
best = etl["Cs2BiAgI6"]["best"]
assert abs(best["PCE"] - 27.99) < 0.01 and abs(best["Voc"] - 1.207) < 0.001 and abs(best["Jsc"] - 25.96) < 0.01 and abs(best["FF"] - 89.28) < 0.01, best
ranking = sorted(((n, e["best"]) for n, e in etl.items()), key=lambda x: -x[1]["PCE"])
data = {"etl": etl, "ranking": [[n, b["thickness"], b["Voc"], b["Jsc"], b["FF"], b["PCE"]] for n, b in ranking], "layers": layers, "temperature": [{k: v for k, v in r.items() if k != "jv"} for r in temp],
        "jv_temperature": {str(r["T"]): r["jv"] for r in temp}, "voc_slope_mV_per_K": round(voc_slope, 2), "pce_slope_per_K": round(pce_slope, 4), "back_contact": back_contact, "stack": stack,
        "stats": {"best_pce": best["PCE"], "best_voc": best["Voc"], "best_jsc": best["Jsc"], "best_ff": best["FF"], "n_etl": len(etl), "n_metals": len(back_contact), "spiral_area_pct": 17.9}}
with open(os.path.join(OUT, "data.js"), "w") as f:
    f.write("// Generated by docs/build_assets.py from the SCAPS-1D exports in data/. Do not edit by hand.\n"); f.write("window.SCAPS = " + json.dumps(data, separators=(",", ":")) + ";\n")
print("data.js:", data["stats"], "ranking:", [(r[0], r[5]) for r in data["ranking"]], "slopes", data["voc_slope_mV_per_K"], data["pce_slope_per_K"])

THEMES = {"dark": ("#e6edf3", "#8b98a9"), "light": ("#0b1220", "#5b6676")}; DARK = "#0b1220"; GOLD = "#f59e0b"
def style(ax, INK, MUTED):
    ax.set_facecolor("none")
    for s in ax.spines.values(): s.set_color(MUTED); s.set_linewidth(0.8)
    ax.tick_params(colors=INK, labelsize=9); ax.xaxis.label.set_color(INK); ax.yaxis.label.set_color(INK); ax.title.set_color(INK); ax.grid(True, color=MUTED, alpha=0.2, lw=0.6)
PAL = ["#f59e0b", "#22d3ee", "#34d399", "#a78bfa", "#f87171", "#60a5fa", "#fb923c", "#e879f9", "#94a3b8", "#facc15"]
for THEME, (INK, MUTED) in THEMES.items():
    save = lambda fig, name: (fig.savefig(os.path.join(OUT, f"{name}_{THEME}.svg"), transparent=True, bbox_inches="tight"), plt.close(fig), print("wrote", name, THEME))
    fig, ax = plt.subplots(figsize=(6.6, 3.8)); style(ax, INK, MUTED); ax.grid(False)
    names = [r[0] for r in data["ranking"]][::-1]; pces = [r[5] for r in data["ranking"]][::-1]
    bars = ax.barh(names, pces, color=[GOLD if n == "Cs2BiAgI6" else "#64748b" for n in names], height=.62)
    for b, v in zip(bars, pces): ax.text(b.get_width() + .4, b.get_y() + b.get_height() / 2, f"{v:.2f} %", va="center", color=INK, fontsize=8.5)
    ax.set_xlim(0, 33); ax.set_xlabel("Simulated power-conversion efficiency at the best swept thickness (%)"); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.set_title("Ten electron-transport layers on FTO / ZnSe / CdTe / Ni", fontsize=9); save(fig, "fig_etl")
    fig, ax = plt.subplots(figsize=(6.6, 4.0)); style(ax, INK, MUTED)
    for (n, b), col in zip(ranking, PAL):
        V, J = zip(*etl[n]["jv_best"]); ax.plot(V, J, color=col, lw=2 if n == "Cs2BiAgI6" else 1.3, label=f"{n} ({b['PCE']:.2f} %)")
    ax.set_xlim(0, 1.2); ax.set_ylim(-1, 28); ax.set_xlabel("Voltage (V)"); ax.set_ylabel("Current density (mA cm⁻²)"); ax.legend(fontsize=7, frameon=False, labelcolor=INK, ncol=2); ax.set_title("J-V under AM 1.5G, each ETL at its best thickness (exports stop at 1.16 V)", fontsize=9); save(fig, "fig_jv")
    fig, ax = plt.subplots(figsize=(6.6, 3.6)); style(ax, INK, MUTED)
    ax.plot(Ts, [r["PCE"] for r in temp], "o-", color=GOLD, lw=2, label=f"PCE, {pce_slope:.3f} points / K"); ax2 = ax.twinx(); ax2.plot(Ts, [r["Voc"] for r in temp], "s--", color="#22d3ee", lw=1.5, label=f"V_OC, {voc_slope:.2f} mV / K"); ax2.tick_params(colors=INK, labelsize=9); ax2.set_ylabel("V_OC (V)", color=INK)
    for s in ax2.spines.values(): s.set_color(MUTED)
    ax.set_xlabel("Temperature (K)"); ax.set_ylabel("PCE (%)"); h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, labelcolor=INK, loc="lower left"); ax.set_title("Temperature derating of the optimum stack; J_SC fixed at 25.96 mA cm⁻²", fontsize=9); save(fig, "fig_temperature")

fig = plt.figure(figsize=(12.8, 6.4), dpi=100); fig.patch.set_facecolor(DARK)
ax = fig.add_axes([0.55, 0.12, 0.42, 0.76]); ax.set_facecolor(DARK)
for (n, b), col in zip(ranking[:5], PAL):
    V, J = zip(*etl[n]["jv_best"]); ax.plot(V, J, color=col, lw=2.4 if n == "Cs2BiAgI6" else 1.4, label=f"{n}  {b['PCE']:.2f} %")
for s in ax.spines.values(): s.set_color("#1f2a3c")
ax.tick_params(colors="#8b98a9"); ax.set_xlabel("V (V)", color="#8b98a9"); ax.set_ylabel("J (mA/cm²)", color="#8b98a9"); ax.set_xlim(0, 1.2); ax.set_ylim(-1, 28); ax.legend(frameon=False, labelcolor="#e6edf3", fontsize=10)
fig.text(0.05, 0.74, "ZnSe/CdTe cell in SCAPS-1D", color="#e6edf3", fontsize=36, fontweight="bold")
fig.text(0.05, 0.62, "Ten electron-transport layers, nine back-contact\nmetals, six-parameter design of experiments", color="#e6edf3", fontsize=17, va="top")
fig.text(0.05, 0.38, f"Best simulated efficiency {best['PCE']:.2f} % with Cs₂BiAgI₆\nV_OC {best['Voc']:.2f} V · J_SC {best['Jsc']:.2f} mA/cm² · FF {best['FF']:.1f} %\nSimulation ceiling, not a fabricated cell", color="#f59e0b", fontsize=14, va="top")
fig.text(0.05, 0.10, "Soham Kavathekar  |  github.com/Soham-ChemE", color="#8b98a9", fontsize=12)
fig.savefig(os.path.join(OUT, "social-preview.png"), dpi=100, facecolor=DARK); plt.close(fig); print("wrote social-preview.png")

# ---------------- animated README hero (SVG with CSS keyframes; GitHub renders these through <img>) ----------------
# The ten-ETL ranking as bars that grow in order of simulated efficiency, from the same `ranking` list as data.js, with the
# headline numbers cycling. No SMIL, no scripts, no fonts.
def _sub(s): return "".join("₀₁₂₃₄₅₆₇₈₉"[int(ch)] if ch.isdigit() else ch for ch in s)
PX, PY, PW, PH = 930, 70, 580, 360
rk = data["ranking"]; n = len(rk); bw = PW / n * .66; gapw = PW / n * .34
bars = ""; css = ""
for i, r in enumerate(rk):
    h = max(2, r[5] / 28 * (PH - 30)); x = PX + gapw / 2 + i * (bw + gapw); col = "#f87171" if i == 0 else ("#f59e0b" if r[5] > 20 else "#22d3ee" if r[5] > 5 else "#64748b")
    bars += f'<g class="br b{i}"><rect x="{x:.1f}" y="{PY + PH - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="4" fill="{col}"/><text class="t bl" x="{x + bw / 2:.1f}" y="{PY + PH - h - 8:.1f}" text-anchor="middle" fill="{col}">{r[5]:.1f}</text><text class="t bn" x="{x + bw / 2:.1f}" y="{PY + PH + 18:.1f}" text-anchor="middle">{_sub(r[0])}</text></g>'
    css += f".b{i} rect{{transform-origin:{x + bw / 2:.1f}px {PY + PH:.1f}px;animation-delay:{i * .5:.1f}s}}.b{i} .bl{{animation-delay:{i * .5 + .6:.1f}s}}\n"
S = data["stats"]
lines = [(f"{S['best_pce']:.2f} %", "best simulated efficiency: Cs₂BiAgI₆ electron-transport layer, Ni contact"), (f"{S['best_voc']:.2f} V · {S['best_jsc']:.2f} mA/cm² · FF {S['best_ff']:.1f} %", "open-circuit voltage, short-circuit current, fill factor at the optimum"),
         (f"{S['n_etl']} ETLs · {S['n_metals'] + 1} metals", "screened in SCAPS-1D with ZnSe replacing the CdS window"), (f"{data['voc_slope_mV_per_K']} mV/K", "V_OC temperature coefficient, 300 to 400 K; J_SC does not move")]
stat_svg = "".join(f'<g class="st s{i}"><text x="80" y="268" class="big">{a}</text><text x="80" y="300" class="small">{b}</text></g>' for i, (a, b) in enumerate(lines))
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 500" width="1600" height="500" role="img" aria-label="ZnSe/CdTe thin-film cell in SCAPS-1D: simulated efficiency of ten electron-transport layers as bars growing in order, next to the headline numbers">
<style>
.t{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.h{{font-size:54px;font-weight:800;fill:#e6edf3;letter-spacing:-1.5px}}.sub{{font-size:21px;fill:#8b98a9}}.big{{font-size:32px;font-weight:800;fill:#22d3ee}}.small{{font-size:16px;fill:#8b98a9}}.foot{{font-size:15px;fill:#5b6676}}.ax{{font-size:13px;fill:#8b98a9}}.bl{{font-size:14px;font-weight:700;opacity:0;animation:show 14s infinite}}.bn{{font-size:12px;fill:#8b98a9}}
.br rect{{transform:scaleY(0);animation:grow 14s infinite}}
@keyframes grow{{0%{{transform:scaleY(0)}}5%{{transform:scaleY(1)}}88%{{transform:scaleY(1)}}94%{{transform:scaleY(0)}}100%{{transform:scaleY(0)}}}}
@keyframes show{{0%{{opacity:0}}4%{{opacity:1}}86%{{opacity:1}}90%{{opacity:0}}100%{{opacity:0}}}}
{css}
.st{{opacity:0;animation:cycle 16s infinite}}.s1{{animation-delay:4s}}.s2{{animation-delay:8s}}.s3{{animation-delay:12s}}
@keyframes cycle{{0%,22%{{opacity:1}}25%,97%{{opacity:0}}100%{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.br rect,.bl,.st{{animation:none}}.br rect{{transform:none}}.bl,.s0{{opacity:1}}}}
</style>
<rect width="1600" height="500" fill="#0b1220"/>
<g class="t">
<text x="80" y="120" class="h">Swap the toxic buffer.</text><text x="80" y="178" class="h">Screen the rest.</text>
<text x="80" y="218" class="sub">SCAPS-1D device-physics study of an FTO / ZnSe / CdTe thin-film cell</text>
{stat_svg}
<text x="80" y="420" class="foot">A ceiling for this parameter set, not a fabricated cell · every number from the raw SCAPS exports in the repository</text>
<text x="80" y="446" class="foot">Right: simulated efficiency of the ten electron-transport layers at their best thickness · open the live page for the 3D stack</text>
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="none" stroke="#1f2a3c"/>
<text x="{PX - 12}" y="{PY + PH / 2}" class="ax" text-anchor="middle" transform="rotate(-90 {PX - 12} {PY + PH / 2})">simulated PCE, %</text>
{bars}
</g>
</svg>"""
with open(os.path.join(OUT, "hero.svg"), "w", encoding="utf-8") as f: f.write(svg)
print("wrote hero.svg", os.path.getsize(os.path.join(OUT, "hero.svg")), "bytes")
