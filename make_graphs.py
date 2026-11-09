"""
EF101-P04 - Hardware stress test graphs.

Reads the HWiNFO CSV logs, gives every column a proper name,
saves cleaned CSVs, and draws the report graphs.

Usage:  python make_graphs.py <folder with the HWiNFO CSVs> <output folder>
"""
import csv, sys, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "out"
os.makedirs(f"{OUT}/graphs", exist_ok=True)
os.makedirs(f"{OUT}/cleaned_data", exist_ok=True)

# ---------- colours (validated categorical palette, light mode) ----------
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURF = "#1f1f1e", "#5f5e58", "#e6e5e0", "#fcfcfb"
SHADE = "#f4d9cc"     # stress-period band
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlecolor": INK, "lines.linewidth": 2, "legend.frameon": False,
})

# HWiNFO left some column names blank in the export. These are the real names,
# in HWiNFO's fixed order (checked against the HWiNFO screenshots in the repo).
SYSTEM_MEM = ["Virtual Memory Committed [MB]", "Virtual Memory Available [MB]",
              "Virtual Memory Load [%]", "Physical Memory Used [MB]",
              "Physical Memory Available [MB]", "Physical Memory Load [%]",
              "Page File Usage [%]", "Page File Total [MB]", "Page File Used [MB]"]
SMART = ["Drive Temperature [°C]", "Drive Remaining Life [%]", "Drive Available Spare [%]",
         "Drive Failure [Yes/No]", "Drive Warning [Yes/No]",
         "Total Host Writes [GB]", "Total Host Reads [GB]"]
DRIVE = ["Read Activity [%]", "Write Activity [%]", "Total Activity [%]",
         "Read Rate [MB/s]", "Write Rate [MB/s]", "Read Total [MB]", "Write Total [MB]"]
IGPU = ["GPU Core Temperature [°C]", "iGPU VID [V]", "iGPU Power [W]", "GPU Clock [MHz]",
        "GPU Memory Clock [MHz]", "GPU D3D Usage (avg) [%]", "GPU 3D Usage [%]",
        "GPU Engine 2 [%]", "GPU Engine 3 [%]", "GPU Engine 4 [%]", "GPU Engine 5 [%]",
        "GPU Engine 6 [%]", "GPU D3D Memory Dynamic [MB]",
        "GPU Throttle Reasons (avg) [Yes/No]"] + [f"GPU Throttle Reason {i} [Yes/No]" for i in range(1, 6)]


def load(name):
    rows = list(csv.reader(open(os.path.join(SRC, name), encoding="latin-1")))
    hdr, sensors = rows[0], rows[-1]
    data = [r for r in rows[1:] if r and r[0][:1].isdigit()]
    if len(data[0]) < len(hdr):                      # GPU log: 10 header columns
        drop = len(hdr) - len(data[0])               # (memory timings) have no data
        hdr = hdr[:13] + hdr[13 + drop:]
        sensors = sensors[:13] + sensors[13 + drop:]
    # fill in the blank names group by group
    names, counters = [], {}
    for h, s in zip(hdr, sensors):
        h = h.strip()
        fill = None
        if s.startswith("System:"): fill = SYSTEM_MEM
        elif s.startswith("S.M.A.R.T."): fill = SMART
        elif s.startswith("Drive:"): fill = DRIVE
        elif s.startswith("iGPU"): fill = IGPU
        if fill is not None and (h.startswith("[") or h.startswith("(")):
            k = counters.get(s, 0); counters[s] = k + 1
            h = fill[k]
        elif fill is not None:
            counters[s] = counters.get(s, 0) + 1
        if s.startswith("PresentMon"):
            k = counters.get(s, 0); counters[s] = k + 1
            h = ("Framerate Presented (avg) [FPS]" if k == 0 else
                 "Frame Time Presented (avg) [ms]" if k == 12 else f"PresentMon {k} {h}")
        names.append(h or "blank")
    df = pd.DataFrame([r[:len(names)] for r in data], columns=names)
    df = df.loc[:, ~df.columns.duplicated()].drop(columns=["blank"], errors="ignore")
    t = df["Time"].str.split(":", expand=True).astype(float)
    secs = t[0] * 3600 + t[1] * 60 + t[2]
    for c in df.columns:
        if c not in ("Date", "Time"):
            conv = pd.to_numeric(df[c], errors="coerce")
            if conv.notna().all():
                df[c] = conv
    df.insert(2, "Elapsed [s]", (secs - secs.iloc[0]).round(1))
    df.to_csv(f"{OUT}/cleaned_data/{os.path.splitext(name)[0].replace(' ', '_')}_clean.csv",
              index=False)
    return df


cpu = load("cpu test.csv")
ram = load("Ram test.CSV")
disk = load("Disk test.csv")
gpu = load("GPU test.csv")
mix = load("Mixed Test.csv")


def window(df, col, thresh):
    """first and last elapsed second where col is above thresh (the stress period)."""
    on = df.loc[df[col] > thresh, "Elapsed [s]"]
    return on.iloc[0], on.iloc[-1]


cpu_w = window(cpu, "Total CPU Usage [%]", 90)
disk_w = window(disk, "Read Rate [MB/s]", 100)
gpu_w = window(gpu, "GPU 3D Usage [%]", 90)


def before(df, w):  return df[df["Elapsed [s]"] < w[0]]
def during(df, w):  return df[(df["Elapsed [s]"] >= w[0]) & (df["Elapsed [s]"] <= w[1])]


def shade(ax, w, label=True):
    ax.axvspan(w[0], w[1], color=SHADE, zorder=0, lw=0)
    if label:
        ax.text((w[0] + w[1]) / 2, 1.0, "stress test running", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=9, color=INK2)


def finish(fig, name, title, note=None):
    fig.suptitle(title, x=0.01, ha="left", fontsize=14, fontweight="bold", color=INK)
    if note:
        fig.text(0.01, 0.005, note, fontsize=9, color=INK2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 0.97))
    fig.savefig(f"{OUT}/graphs/{name}", dpi=200)
    plt.close(fig)


# ================= 1. Idle (before) vs stress =================
pairs = [
    ("CPU test", "Total CPU Usage [%]", "CPU usage (%)", before(cpu, cpu_w), during(cpu, cpu_w)),
    ("Storage test", "Read Rate [MB/s]", "SSD read speed (MB/s)", before(disk, disk_w), during(disk, disk_w)),
    ("GPU test", "GPU 3D Usage [%]", "GPU usage (%)", before(gpu, gpu_w), during(gpu, gpu_w)),
    ("Mixed workload", "Physical Memory Load [%]", "RAM in use (%)",
     before(disk, disk_w), mix),
]
fig, axes = plt.subplots(1, 4, figsize=(14, 4.6))
for ax, (test, col, lab, b, s) in zip(axes, pairs):
    vals = [b[col].mean(), s[col].mean()]
    bars = ax.bar(["Idle\n(before test)", "Under\nstress"], vals, color=[ "#b7d3f6", BLUE],
                  width=0.55, edgecolor=SURF, linewidth=2)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom",
                color=INK, fontweight="bold")
    ax.set_title(f"{test}\n{lab}", loc="left")
    ax.set_ylim(0, max(vals) * 1.18 if "MB/s" in col else 100)
    ax.grid(axis="x", visible=False)
finish(fig, "01_idle_vs_stress.png", "Idle vs stress: average of the main resource in each test",
       "Idle = the seconds logged before each test started. RAM idle value is from the start of the storage "
       "log (RAM test CSV has no memory columns).")

# ================= 2. CPU test timeline =================
fig, ax = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
x = cpu["Elapsed [s]"]
ax[0].plot(x, cpu["Total CPU Usage [%]"], color=BLUE)
ax[0].set_ylim(0, 105); ax[0].set_ylabel("%"); ax[0].set_title("CPU usage", loc="left")
ax[1].plot(x, cpu["Core Clocks (avg) [MHz]"], color=ORANGE)
ax[1].axhline(2800, color=INK2, ls="--", lw=1)
ax[1].text(x.iloc[-1], 2830, "base speed 2,800 MHz", ha="right", va="bottom", fontsize=9, color=INK2)
ax[1].set_ylim(0, 3500); ax[1].set_ylabel("MHz"); ax[1].set_title("CPU clock speed (average of 4 cores)", loc="left")
ax[2].plot(x, cpu["CPU Package [°C]"], color=AQUA)
thr = cpu["Package/Ring Thermal Throttling [Yes/No]"] == "Yes"
ax[2].scatter(x[thr], cpu["CPU Package [°C]"][thr], s=28, color=AQUA, edgecolor=SURF, zorder=3,
              label="dot = HWiNFO reports thermal throttling")
ax[2].set_ylim(70, 100); ax[2].set_ylabel("°C"); ax[2].set_title("CPU package temperature", loc="left")
ax[2].legend(loc="lower right", fontsize=9)
ax[2].set_xlabel("Time since logging started (seconds)")
for i, a in enumerate(ax): shade(a, cpu_w, i == 0)
finish(fig, "02_cpu_test_timeline.png",
       "CPU stress test: usage hits 100%, but clock speed falls below base speed",
       "Laptop on battery. CPU was already ~90 °C and throttling before the test began.")

# ================= 3. Utilization vs performance =================
fig, a = plt.subplots(figsize=(11, 4.8))
a.plot(x, cpu["Total CPU Usage [%]"], color=BLUE, label="CPU usage (time busy)")
a.plot(x, cpu["Total CPU Utility [%]"], color=ORANGE, label="CPU utility (work done vs. base speed)")
a.text(x.iloc[18], 103, "Usage: 100%", color=INK, fontsize=10, ha="center")
a.text(x.iloc[18], cpu["Total CPU Utility [%]"].iloc[18] + 4, f"Utility: ~{during(cpu, cpu_w)['Total CPU Utility [%]'].mean():.0f}%",
       color=INK, fontsize=10, ha="center")
shade(a, cpu_w)
a.set_ylim(0, 112); a.set_ylabel("%"); a.set_xlabel("Time since logging started (seconds)")
a.legend(loc="upper left", fontsize=9, bbox_to_anchor=(0, 0.93))
finish(fig, "03_utilization_vs_performance.png",
       "Utilization vs performance: 100% busy is not 100% of the speed",
       "Usage counts how much of the time the CPU is busy. Utility also counts how fast it runs, "
       "so a hot, slowed CPU does about half the work.")

# ================= 4. Storage test timeline =================
fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
x = disk["Elapsed [s]"]
ax[0].plot(x, disk["Read Rate [MB/s]"], color=BLUE, label="Read")
ax[0].plot(x, disk["Write Rate [MB/s]"], color=ORANGE, label="Write")
ax[0].set_ylabel("MB/s"); ax[0].set_title("SSD transfer speed", loc="left"); ax[0].legend(loc="upper right")
ax[1].plot(x, disk["Total Activity [%]"], color=BLUE)
ax[1].set_ylim(0, 105); ax[1].set_ylabel("%"); ax[1].set_title("SSD active time", loc="left")
ax[2].plot(x, disk["Drive Temperature [°C]"], color=AQUA)
ax[2].set_ylabel("°C"); ax[2].set_title("SSD temperature", loc="left")
ax[2].set_xlabel("Time since logging started (seconds)")
for i, a in enumerate(ax): shade(a, disk_w, i == 0)
finish(fig, "04_storage_test_timeline.png",
       f"Storage stress test: reads up to {disk['Read Rate [MB/s]'].max():.0f} MB/s on the Kingston SSD",
       "Active time sits at 100% even when only ~1-20 MB/s is moving: the drive is busy, but not fast.")

# ================= 5. GPU test timeline =================
fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
x = gpu["Elapsed [s]"]
ax[0].plot(x, gpu["GPU 3D Usage [%]"], color=BLUE)
ax[0].set_ylim(0, 105); ax[0].set_ylabel("%"); ax[0].set_title("GPU 3D usage", loc="left")
ax[1].plot(x, gpu["GPU Clock [MHz]"], color=ORANGE)
ax[1].set_ylim(0, 1400); ax[1].set_ylabel("MHz"); ax[1].set_title("GPU clock speed", loc="left")
ax[2].plot(x, gpu["Framerate Presented (avg) [FPS]"], color=YELLOW)
ax[2].set_ylabel("FPS"); ax[2].set_title("Desktop frame rate (dwm.exe, from PresentMon)", loc="left")
ax[3].plot(x, gpu["GPU Core Temperature [°C]"], color=AQUA)
ax[3].set_ylim(75, 100); ax[3].set_ylabel("°C"); ax[3].set_title("GPU temperature", loc="left")
ax[3].set_xlabel("Time since logging started (seconds)")
for i, a in enumerate(ax): shade(a, gpu_w, i == 0)
finish(fig, "05_gpu_test_timeline.png",
       "GPU stress test (Intel Iris Xe): GPU at 100%, desktop drops to ~2 FPS",
       "GPU clock mostly stays at 600 MHz (max seen 1,050 MHz) while temperature reaches the low 90s °C. "
       "GPU power sensor read a flat 0.029 W, so it is left out.")

# ================= 6. Mixed workload =================
fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True, sharey=True)
x = mix["Elapsed [s]"]
series = [("CPU usage", "Total CPU Usage [%]", BLUE), ("RAM in use", "Physical Memory Load [%]", ORANGE),
          ("SSD active time", "Total Activity [%]", AQUA), ("GPU usage", "GPU 3D Usage [%]", YELLOW)]
for a, (lab, col, c) in zip(ax, series):
    a.plot(x, mix[col], color=c)
    a.set_title(f"{lab}  (average {mix[col].mean():.0f}%)", loc="left")
    a.set_ylim(0, 105); a.set_ylabel("%")
ax[-1].set_xlabel("Time since logging started (seconds)")
finish(fig, "06_mixed_workload.png",
       "Mixed workload (10 browser tabs + YouTube + zipping a video): SSD and CPU are the bottleneck",
       "Whole log is under load (no idle part). CPU clock averaged only "
       f"{mix['Core Clocks (avg) [MHz]'].mean():,.0f} MHz at ~91 °C.")

# ================= 7. Memory and page file =================
fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
x = mix["Elapsed [s]"]
ax[0].plot(x, mix["Physical Memory Used [MB]"] / 1024, color=BLUE, label="RAM used")
ax[0].plot(x, mix["Physical Memory Available [MB]"] / 1024, color=ORANGE, label="RAM free")
ax[0].set_ylim(0, 12); ax[0].set_ylabel("GB"); ax[0].legend(loc="center right")
ax[0].set_title("Physical RAM (about 11.8 GB usable)", loc="left")
ax[1].plot(x, mix["Virtual Memory Committed [MB]"] / 1024, color=BLUE, label="Committed (RAM + page file)")
ax[1].plot(x, mix["Page File Used [MB]"] / 1024, color=AQUA, label="Page file used (on the SSD)")
ax[1].set_ylim(0, 19); ax[1].set_ylabel("GB"); ax[1].legend(loc="upper right")
ax[1].set_title("Virtual memory (limit about 18.5 GB)", loc="left")
ax[1].set_xlabel("Time since logging started (seconds)")
finish(fig, "07_memory_and_pagefile_mixed.png",
       "RAM pressure in the mixed workload: Windows moves data to the page file",
       "When RAM is ~80% full, the page file on the SSD grows "
       f"from {mix['Page File Used [MB]'].min()/1024:.2f} to {mix['Page File Used [MB]'].max()/1024:.2f} GB.")

# ================= 8. Bottleneck summary heatmap =================
nan = float("nan")
c, d, g = during(cpu, cpu_w), during(disk, disk_w), during(gpu, gpu_w)
table = pd.DataFrame({
    "CPU usage": [c["Total CPU Usage [%]"].mean(), nan, nan, mix["Total CPU Usage [%]"].mean()],
    "RAM in use": [nan, d["Physical Memory Load [%]"].mean(), nan, mix["Physical Memory Load [%]"].mean()],
    "SSD active time": [nan, d["Total Activity [%]"].mean(), nan, mix["Total Activity [%]"].mean()],
    "GPU usage": [nan, nan, g["GPU 3D Usage [%]"].mean(), mix["GPU 3D Usage [%]"].mean()],
}, index=["CPU test", "Storage test", "GPU test", "Mixed workload"])
fig, a = plt.subplots(figsize=(10, 4.6))
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#2a78d6", "#0d366b"])
cmap.set_bad("#efeee9")
a.imshow(table.values, cmap=cmap, vmin=0, vmax=100, aspect="auto")
a.set_xticks(range(4), table.columns); a.set_yticks(range(4), table.index)
a.grid(False); a.tick_params(length=0)
for i in range(4):
    for j in range(4):
        v = table.values[i, j]
        if v != v:
            a.text(j, i, "not logged", ha="center", va="center", color=INK2, fontsize=9)
        else:
            a.text(j, i, f"{v:.0f}%", ha="center", va="center", fontweight="bold",
                   color="white" if v > 55 else INK)
for s in a.spines.values(): s.set_visible(False)
a.set_xticks([x - 0.5 for x in range(1, 4)], minor=True)
a.set_yticks([y - 0.5 for y in range(1, 4)], minor=True)
a.grid(which="minor", color=SURF, linewidth=3); a.tick_params(which="minor", length=0)
finish(fig, "08_bottleneck_summary.png", "Which part is the bottleneck? Average load during each test",
       "Grey = that sensor was not switched on in that HWiNFO log. The RAM test CSV is left out because it has no memory columns.")

table.round(1).to_csv(f"{OUT}/cleaned_data/bottleneck_summary.csv")
print("windows (s):", cpu_w, disk_w, gpu_w)
print(table.round(1))
print("done ->", OUT)
