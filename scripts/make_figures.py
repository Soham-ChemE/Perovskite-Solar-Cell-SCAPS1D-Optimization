"""Regenerate every figure in figures/ and data/scaps_metrics.json from the raw SCAPS-1D batch exports in data/.
Usage: python scripts/make_figures.py   (needs numpy, openpyxl, matplotlib)
Metrics are the Voc / Jsc / FF / eta values SCAPS writes into each export; Pmax from the sweep is stored as a cross-check."""
import os, re, json, glob, numpy as np, openpyxl, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon
from matplotlib import font_manager as fm
FONT = "Avenir Next" if "Avenir Next" in {f.name for f in fm.fontManager.ttflist} else "Helvetica Neue"
plt.rcParams.update({"font.family": FONT, "font.size": 12, "axes.labelsize": 12.5, "legend.fontsize": 10.5, "savefig.dpi": 220, "mathtext.fontset": "custom", "mathtext.rm": FONT, "mathtext.it": FONT + ":italic", "mathtext.bf": FONT + ":bold"})
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "data"); OUT = os.path.join(HERE, "..", "figures") + os.sep; os.makedirs(OUT, exist_ok=True)
PAL = {"gold": "#d97706", "sun": "#f59e0b", "sand": "#fde68a", "ink": "#1f2937", "muted": "#6b7280", "teal": "#0f766e", "red": "#b91c1c", "blue": "#1d4ed8", "green": "#15803d", "bg": "#fffbf2"}
def label(ax, s): ax.text(-0.1, 1.06, s, transform=ax.transAxes, fontsize=15, fontweight="bold", va="top")

def sheet_jv(ws):
    """Return (param, V, J, scaps_metrics) from a SCAPS batch sheet. J is positive photocurrent in mA/cm^2.
    Metrics are SCAPS's own 'Voc = / Jsc = / FF = / eta =' rows written into each export (the J-V sweep in the
    export stops at 1.16 V, before the J = 0 crossing, so Voc cannot be read from the sweep itself)."""
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
def metrics(V, J, sm):
    """SCAPS-reported metrics; cross-checked against Pmax from the sweep (PCE % = Pmax in mW/cm^2 at 100 mW/cm^2 input)."""
    o = np.argsort(V); V, J = V[o], J[o]; P = V * J; pmax = P[(V >= 0) & (J >= 0)].max()
    m = dict(sm); m["Pmax_from_sweep"] = float(pmax)
    if "PCE" in m and abs(m["PCE"] - pmax) > 0.05 * max(m["PCE"], 1e-6) and m["PCE"] > 0.5: print("  WARNING PCE mismatch", m["PCE"], pmax)
    return m

res = {"etl_thickness": {}, "layers": {}, "temperature": {}}
etl_files = {"Cs2BiAgI6": "Cs2BiAgI6 DATA POINTS.xlsx", "C60": "C60 DATA POINTS.xlsx", "CuO": "CuO DATA POINTS.xlsx", "Cu2O": "Cu2O DATA POINTS.xlsx", "PC16BM": "PC16BM DATA POINTS.xlsx", "PCBM": "PCBM DATA POINTS.xlsx", "Sb2Se3": "Sb2Se3 DATA POINTS.xlsx", "TiO2": "TiO2 DATA POINTS.xlsx", "WO3": "WO3 DATA POINTS.xlsx", "WS2": "WS2 DATA POINTS.xlsx"}
jv_2um = {}
for etl, f in etl_files.items():
    wb = openpyxl.load_workbook(os.path.join(SRC, f), data_only=True); rows = []
    for ws in wb.worksheets:
        if not ws.title.startswith("ETL"): continue
        try: param, V, J, sm = sheet_jv(ws)
        except Exception: continue
        if param is None or len(V) < 5 or "PCE" not in sm: continue
        m = metrics(V, J, sm); m["thickness"] = param[1]; rows.append(m); jv_2um[(etl, param[1])] = (V, J)
    res["etl_thickness"][etl] = rows
# layer sweeps for the optimum stack (Cs2BiAgI6 file has CdTe/ZnSe/FTO batches)
wb = openpyxl.load_workbook(os.path.join(SRC, "Cs2BiAgI6 DATA POINTS.xlsx"), data_only=True)
for ws in wb.worksheets:
    layer = ws.title.split()[0]
    try: param, V, J, sm = sheet_jv(ws)
    except Exception: continue
    if param is None or "PCE" not in sm: continue
    m = metrics(V, J, sm); m["thickness"] = param[1]; res["layers"].setdefault(layer, []).append(m)
# temperature
wbT = openpyxl.load_workbook(os.path.join(SRC, "Cs2BiAgI6_Temperature_Data.xlsx"), data_only=True); jvT = {}
for ws in wbT.worksheets:
    param, V, J, sm = sheet_jv(ws); m = metrics(V, J, sm); m["T"] = param[1]; res["temperature"][param[1]] = m; jvT[param[1]] = (V, J)

# ---------- Fig A: J-V curves of the ten ETLs at their thickest simulated point + PCE bars ----------
fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), gridspec_kw={"width_ratios": [1.15, 1]})
cols = plt.cm.tab10(np.linspace(0, 1, 10)); summary = []
for (etl, c) in zip(etl_files, cols):
    rows = res["etl_thickness"][etl]
    if not rows: continue
    best = max(rows, key=lambda r: r["PCE"]); V, J = jv_2um[(etl, best["thickness"])]; o = np.argsort(V)
    axes[0].plot(V[o], J[o], color=c, lw=2.2 if etl == "Cs2BiAgI6" else 1.5, label=f"{etl} ({best['thickness']:.1f} µm): {best['PCE']:.2f}%"); summary.append((etl, best))
axes[0].set_xlim(0, 1.25); axes[0].set_ylim(0, 28); axes[0].set_xlabel("voltage (V)"); axes[0].set_ylabel("current density (mA cm$^{-2}$)"); axes[0].set_title("J-V curves of the ten electron-transport layers (FTO/ZnSe/CdTe/ETL/Ni, 300 K)", fontsize=12); axes[0].text(0.98, 0.42, "exported sweeps stop at 1.16 V;\nV$_{OC}$, FF and η are SCAPS-reported values", transform=axes[0].transAxes, fontsize=9, color=PAL["muted"], ha="right"); axes[0].legend(fontsize=9, ncol=2, loc="lower left"); label(axes[0], "(a)")
summary.sort(key=lambda t: -t[1]["PCE"]); names = [s[0] for s in summary]; pce = [s[1]["PCE"] for s in summary]
bars = axes[1].bar(range(len(names)), pce, color=[PAL["gold"] if n == "Cs2BiAgI6" else "#94a3b8" for n in names], edgecolor="k")
for i, v in enumerate(pce): axes[1].text(i, v + 0.4, f"{v:.1f}" if v > 1 else f"{v:.2f}", ha="center", fontsize=10, fontweight="bold")
axes[1].set_xticks(range(len(names))); axes[1].set_xticklabels(names, rotation=30, ha="right"); axes[1].set_ylabel("power conversion efficiency (%)"); axes[1].set_ylim(0, 32); axes[1].set_title("SCAPS-reported efficiency at each ETL's best swept thickness", fontsize=12); label(axes[1], "(b)")
fig.tight_layout(); fig.savefig(OUT + "fig_etl_screening.png"); plt.close(fig)

# ---------- Fig B: thickness sweeps of all four layers, four metrics ----------
fig, axes = plt.subplots(2, 2, figsize=(13, 8.5)); keys = [("Voc", "V$_{OC}$ (V)"), ("Jsc", "J$_{SC}$ (mA cm$^{-2}$)"), ("FF", "fill factor (%)"), ("PCE", "efficiency (%)")]
lc = {"ETL": PAL["gold"], "CdTe": PAL["red"], "ZnSe": PAL["green"], "FTO": PAL["blue"]}; nm = {"ETL": "Cs$_2$BiAgI$_6$ (ETL)", "CdTe": "CdTe absorber", "ZnSe": "ZnSe buffer", "FTO": "FTO front contact"}
for ax, (k, lab_), pl in zip(axes.flat, keys, "abcd"):
    for layer, rows in res["layers"].items():
        rows = sorted(rows, key=lambda r: r["thickness"]); ax.plot([r["thickness"] for r in rows], [r[k] for r in rows], marker="o", lw=2, ms=7, color=lc.get(layer, "k"), label=nm.get(layer, layer))
    ax.set_xlabel("layer thickness (µm)"); ax.set_ylabel(lab_); label(ax, f"({pl})"); ax.grid(alpha=0.25)
axes[0, 0].legend(fontsize=10); fig.suptitle("Layer-thickness sweeps (0.4 to 2.0 µm) with the other layers held at the optimum", fontsize=13, y=0.995)
fig.tight_layout(); fig.savefig(OUT + "fig_thickness_sweeps.png"); plt.close(fig)

# ---------- Fig C: temperature ----------
fig, axes = plt.subplots(1, 3, figsize=(16, 5.0), gridspec_kw={"width_ratios": [1.25, 1, 1]}); Ts = sorted(jvT); cm_ = plt.cm.plasma(np.linspace(0.1, 0.85, len(Ts)))
for T, c in zip(Ts, cm_):
    V, J = jvT[T]; o = np.argsort(V); axes[0].plot(V[o], J[o], color=c, lw=2, label=f"{T:.0f} K")
axes[0].set_xlim(0, 1.25); axes[0].set_ylim(0, 27); axes[0].set_xlabel("voltage (V)"); axes[0].set_ylabel("current density (mA cm$^{-2}$)"); axes[0].legend(title="cell temperature", fontsize=9.5); axes[0].set_title("J-V family, optimum stack", fontsize=12); label(axes[0], "(a)")
tm = [res["temperature"][T] for T in Ts]
axes[1].plot(Ts, [m["PCE"] for m in tm], marker="o", color=PAL["gold"], lw=2.4, ms=8); axes[1].set_ylabel("efficiency (%)"); axes[1].set_xlabel("temperature (K)")
for T, m in zip(Ts, tm): axes[1].annotate(f"{m['PCE']:.1f}", (T, m["PCE"]), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9.5)
dpce = np.polyfit(Ts, [m["PCE"] for m in tm], 1)[0]; axes[1].set_title(f"Efficiency: {dpce:.3f} points per K", fontsize=12); axes[1].set_ylim(22.5, 28.8); axes[1].grid(alpha=0.25); label(axes[1], "(b)")
axes[2].plot(Ts, [m["Voc"] for m in tm], marker="s", color=PAL["blue"], lw=2.2, ms=7, label="V$_{OC}$ (V)"); axes[2].set_ylabel("V$_{OC}$ (V)", color=PAL["blue"]); axes[2].set_xlabel("temperature (K)")
ax3 = axes[2].twinx(); ax3.plot(Ts, [m["FF"] for m in tm], marker="^", color=PAL["teal"], lw=2.2, ms=7, label="fill factor (%)"); ax3.set_ylabel("fill factor (%)", color=PAL["teal"])
slope = np.polyfit(Ts, [m["Voc"] for m in tm], 1)[0] * 1000; axes[2].set_title(f"dV$_{{OC}}$/dT = {slope:.2f} mV K$^{{-1}}$; J$_{{SC}}$ fixed at {tm[0]['Jsc']:.2f}", fontsize=12); axes[2].grid(alpha=0.25); label(axes[2], "(c)")
fig.tight_layout(); fig.savefig(OUT + "fig_temperature.png"); plt.close(fig); res["voc_slope_mV_per_K"] = slope; res["pce_slope_per_K"] = dpce

# ---------- Fig D: back contact (from report table; simulation outputs) ----------
bc = [("Al", 4.3, 5.26), ("Cu", 4.6, 12.43), ("Fe", 4.8, 17.35), ("C", 5.0, 22.33), ("W", 5.2, 25.72), ("Ni", 5.55, 27.99), ("Pt", 5.7, 28.44), ("Se", 5.9, 28.45)]
fig, ax = plt.subplots(figsize=(8.5, 5)); ax.plot([b[1] for b in bc], [b[2] for b in bc], "-", color="#94a3b8", lw=1.5, zorder=1)
ax.scatter([b[1] for b in bc], [b[2] for b in bc], s=[220 if b[0] == "Ni" else 120 for b in bc], color=[PAL["gold"] if b[0] == "Ni" else "#475569" for b in bc], edgecolors="k", zorder=3)
for m, wf, p in bc: ax.annotate(m, (wf, p), xytext=(6, -14 if m in ("Pt",) else 8), textcoords="offset points", fontsize=11, fontweight="bold")
ax.set_xlabel("back-contact work function (eV)"); ax.set_ylabel("efficiency (%)"); ax.set_title("Back-contact metal: efficiency tracks the work function; Ni is the practical optimum", fontsize=12); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(OUT + "fig_back_contact.png"); plt.close(fig)

# ---------- Fig E: device schematic ----------
fig, ax = plt.subplots(figsize=(8, 5.2)); ax.set_xlim(0, 10); ax.set_ylim(0, 7.0); ax.axis("off")
layers = [("Ni back contact  (φ = 5.55 eV)", "#64748b", 0.55), ("Cs$_2$BiAgI$_6$ electron-transport layer  2 µm", PAL["red"], 1.1), ("CdTe absorber  3 µm", PAL["gold"], 1.6), ("ZnSe buffer  0.025 µm", PAL["green"], 0.35), ("FTO front contact  0.4 µm", PAL["blue"], 0.6)]
y = 0.4
for lab_, c, h in layers:
    ax.add_patch(FancyBboxPatch((1.5, y), 6.0, h, boxstyle="round,pad=0,rounding_size=0.06", facecolor=c, edgecolor="k", lw=0.8)); ax.text(4.5, y + h / 2, lab_, ha="center", va="center", fontsize=11.5, fontweight="bold", color="white" if c != PAL["green"] else "white"); y += h + 0.08
for xx in np.linspace(2.2, 6.8, 7): ax.annotate("", (xx, y + 0.15), (xx, y + 1.3), arrowprops=dict(arrowstyle="-|>", color=PAL["sun"], lw=1.8))
ax.text(4.5, y + 1.42, "AM 1.5G, 1000 W m$^{-2}$, 300 K", ha="center", fontsize=11, color=PAL["gold"], fontweight="bold")
ax.text(9.0, 0.7, "hole extraction", rotation=90, va="bottom", fontsize=10, color=PAL["muted"]); ax.text(0.9, 4.0, "electron extraction", rotation=90, va="bottom", fontsize=10, color=PAL["muted"])
ax.set_title("FTO / ZnSe / CdTe / Cs$_2$BiAgI$_6$ / Ni  (SCAPS-1D, planar, one-dimensional)", fontsize=12, pad=14)
fig.tight_layout(); fig.savefig(OUT + "fig_device_stack.png"); plt.close(fig)

json.dump(res, open(os.path.join(SRC, "scaps_metrics.json"), "w"), indent=1, default=float)
print("ETL best (thickest) metrics from raw J-V:"); [print(f"  {e:10} t={b['thickness']:.1f}  Voc {b['Voc']:.3f}  Jsc {b['Jsc']:.2f}  FF {b['FF']:.2f}  PCE {b['PCE']:.2f}") for e, b in summary]
print("Temperature:", {T: round(m["PCE"], 2) for T, m in res["temperature"].items()}, "slope", round(slope, 2))
print("Layers:", {k: [(r["thickness"], round(r["PCE"], 2)) for r in sorted(v, key=lambda r: r["thickness"])] for k, v in res["layers"].items()})
