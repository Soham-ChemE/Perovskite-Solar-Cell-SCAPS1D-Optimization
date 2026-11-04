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
