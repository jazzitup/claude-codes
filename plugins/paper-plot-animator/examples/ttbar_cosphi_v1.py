"""tt̄ spin entanglement: from one dilepton event display to the cos φ distribution (CMS TOP-23-001, arXiv:2406.03976).

Scenes (s):  0-11  one tt̄ → e⁺μ⁻ b b̄ νν̄ event, CMS-like transverse view, grows from the vertex
            11-21  reconstruct t and t̄; m(tt̄) and β_z(tt̄) cuts (threshold region)
            21-35  boost to the tt̄ rest frame, then each top to its own rest frame → ℓ̂⁺, ℓ̂⁻ → cos φ
            35-50  many events: cos φ histogram, ⟨cos φ⟩, D = −3⟨cos φ⟩; reference D = 0, −1/3, −1
            50-62  CMS result: Fig. 6 (left) + D = −0.480 (+0.026 −0.029), 5.1σ

The single event is a real-kinematics toy (Lorentz boosts in kin.py; cos φ on screen is computed from it).
The many-event histogram is parton-level toy MC drawn from ½(1 − D cos φ) with the measured D (labelled as such).
The CMS plot is the published figure (arXiv source PDF rasterised).

Library: paper-plot-animator plugin lib/ (vstyle, kin, detector, harness) — found by _ppa_lib()
Usage:  python ttbar_cosphi_v1.py OUTDIR [lo:hi] [--preview t1,t2] [--jobs N] [--encode OUT.mp4]
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, Ellipse, FancyBboxPatch, Rectangle
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
def _ppa_lib():
    """paper-plot-animator plugin library: $PPA_LIB, the git checkout, or the installed plugin cache."""
    import glob
    cands = [os.environ.get("PPA_LIB", ""), os.path.expanduser("~/claude-codes/plugins/paper-plot-animator/lib")]
    cands += sorted(glob.glob(os.path.expanduser("~/.claude/plugins/cache/*/paper-plot-animator/*/lib")), key=os.path.getmtime)[::-1]
    for c in cands:
        if c and os.path.exists(os.path.join(c, "vstyle.py")):
            return c
    raise SystemExit("paper-plot-animator lib not found: set PPA_LIB")


sys.path.insert(0, _ppa_lib())
import vstyle as V
import kin as K
from detector import EventDisplay, underlying_event
from harness import main

V.setup()
FPS, T_END = 30, 62.0
D_OBS, D_UP, D_DN, D_EXP = -0.480, 0.026, 0.029, -0.467
SIGNIF = 5.1
REF = "CMS, Rep. Prog. Phys. 87 (2024) 117801  ·  arXiv:2406.03976"

C_T = np.array([1.00, 0.62, 0.25])     # top side (warm)
C_TB = np.array([0.40, 0.78, 1.00])    # anti-top side (cool)
C_LP = (0.35, 1.00, 0.55)              # e+  (green)
C_LM = (1.00, 0.38, 0.38)              # mu- (red)
C_B = (1.00, 0.85, 0.25)
C_MET = (1.00, 0.35, 0.85)
STEPS = [r"one $t\bar{t}$ event", r"reconstruct $t$ and $\bar{t}$", "boost → lepton angle", "many events", "CMS result"]
STEP_T = [0, 11, 21, 35, 50]

ramp = V.ramp


# ------------------------------------------------------------------ the event
MT, MW, MB = 172.5, 80.4, 4.8


def make_event(seed):
    rng = np.random.default_rng(seed)
    mtt = rng.uniform(355, 390)
    pstar = np.sqrt(mtt ** 2 / 4 - MT ** 2)
    n = K.rand_dir(rng)
    t_cm, tb_cm = K.p4(MT, pstar * n), K.p4(MT, -pstar * n)
    out = {}
    for name, top, sgn in (("t", t_cm, +1), ("tb", tb_cm, -1)):
        W, b = K.two_body(MT, MW, MB, K.rand_dir(rng))            # in top rest frame
        l, nu = K.two_body(MW, 0.0, 0.0, K.rand_dir(rng))        # in W rest frame
        l = K.boost(l, K.beta_of(W)); nu = K.boost(nu, K.beta_of(W))
        bt = K.beta_of(top)
        out[name] = dict(top=top, W=K.boost(W, bt), b=K.boost(b, bt), l=K.boost(l, bt), nu=K.boost(nu, bt))
    # tt̄ system motion in the lab
    ptt = rng.uniform(5, 30); a = rng.uniform(0, 2 * np.pi); bz = rng.uniform(0.15, 0.55) * rng.choice([-1, 1])
    Ett = np.sqrt(mtt ** 2 + ptt ** 2) / np.sqrt(1 - bz ** 2)
    pz = bz * Ett
    beta = np.array([ptt * np.cos(a), ptt * np.sin(a), pz]) / np.sqrt(mtt ** 2 + ptt ** 2 + pz ** 2)
    lab = {k: {q: K.boost(v, beta) for q, v in d.items()} for k, d in out.items()}
    # observable, the way the analysis does it: lab → tt̄ CM → each top rest frame
    tt = lab["t"]["top"] + lab["tb"]["top"]
    def lep_dir(side):
        top_cm = K.to_rest_frame(lab[side]["top"], tt)
        l_cm = K.to_rest_frame(lab[side]["l"], tt)
        return K.unit(K.to_rest_frame(l_cm, top_cm)[1:])
    lp, lm = lep_dir("t"), lep_dir("tb")
    met = lab["t"]["nu"] + lab["tb"]["nu"]
    return dict(lab=lab, mtt=K.mass(tt), bz=abs(tt[3] / tt[0]), lp=lp, lm=lm, cphi=float(lp @ lm),
                n_cm=K.unit(K.to_rest_frame(lab["t"]["top"], tt)[1:]), pstar=pstar,
                met_pt=K.pt(met), met_phi=K.phi(met), rng_seed=seed)


def good(ev):
    L = ev["lab"]
    objs = [L["t"]["l"], L["tb"]["l"], L["t"]["b"], L["tb"]["b"]]
    if K.pt(L["t"]["l"]) < 30 or K.pt(L["tb"]["l"]) < 30 or K.pt(L["t"]["b"]) < 40 or K.pt(L["tb"]["b"]) < 40:
        return False
    if any(abs(K.eta(o)) > 2.0 for o in objs) or ev["met_pt"] < 50:
        return False
    phis = [K.phi(o) for o in objs] + [ev["met_phi"]]
    for i in range(5):
        for j in range(i + 1, 5):
            d = abs((phis[i] - phis[j] + np.pi) % (2 * np.pi) - np.pi)
            if d < 0.75:
                return False
    return 0.55 < ev["cphi"] < 0.8 and 345 < ev["mtt"] < 400


def pick_event():
    for seed in range(20000):
        ev = make_event(seed)
        if good(ev):
            return ev
    raise RuntimeError("no event")


EV = pick_event()
L = EV["lab"]


def build_display(ev):
    D = EventDisplay(emph_default=1.0)
    rng = np.random.default_rng(11)
    underlying_event(D, rng, n=34)
    # leptons
    lp, lm = L["t"]["l"], L["tb"]["l"]
    D.track(K.pt(lp), K.phi(lp), +1, color=C_LP, kind="e", tag="lp")
    D.tower(K.phi(lp), lp[0], "ecal", tag="lp")
    D.track(K.pt(lm), K.phi(lm), -1, color=C_LM, kind="mu", tag="lm")
    D.tower(K.phi(lm), 2.0, "hcal", tag="lm")
    # b jets: cone + towers + a few charged tracks
    for tag, b in (("b", L["t"]["b"]), ("bb", L["tb"]["b"])):
        ph, E = K.phi(b), b[0]
        D.jet(ph, K.pt(b), tag=tag, half=0.30)
        for k, f in enumerate((0.15, 0.35, 0.3, 0.2)):
            dph = (k - 1.5) * 0.09
            D.tower(ph + dph, 0.35 * E * f, "ecal", tag=tag)
            D.tower(ph + dph, 0.65 * E * f, "hcal", tag=tag)
        for k in range(7):
            ptk = K.pt(b) * rng.uniform(0.03, 0.18)
            D.track(ptk, ph + rng.normal(0, 0.10), rng.choice([-1, 1]), color=(1.0, 0.9, 0.55), kind="had", tag=tag, lw=1.4)
    D.met(EV["met_phi"], EV["met_pt"], tag="met")
    return D


DISP = build_display(EV)


# ------------------------------------------------------------------ helpers
def title(ax, s, a=1.0, sub=None):
    V.text(ax, 0, V.YL - 0.42, s, a=a, size=26, weight="bold")
    if sub:
        V.text(ax, 0, V.YL - 0.86, sub, a=a * 0.9, size=15, color=V.GREY)


def frame_common(ax, t):
    k = max(i for i, s in enumerate(STEP_T) if t >= s)
    V.steps(ax, STEPS, k)


def label(ax, x, y, s, col, a, size=17, ha="center"):
    V.text(ax, x, y, s, a=a, size=size, color=col, weight="bold", ha=ha)


def obj_anchor(cx, cy, s, phi, r, perp=0.0):
    x, y = DISP.anchor(cx, cy, s, phi, r)
    return x - perp * np.sin(phi), y + perp * np.cos(phi)


# where the object labels sit: (tag, display radius, perpendicular offset in data units)
LAB_POS = {"lp": (1.75, 0.38), "lm": (2.35, 0.42), "b": (1.98, 0.0), "bb": (1.98, 0.0)}


def rotm(yaw, pitch):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    # physics axes (x, y, z=beam) → view axes (beam horizontal on screen)
    P = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
    return Ry @ Rx @ P


def proj(R, v):
    w = R @ np.asarray(v, float)
    return np.array([w[0], w[1]]), w[2]


def sphere(ax, cx, cy, r, R, col, a, z=10):
    if a <= 0.01:
        return
    V.glow_disc(ax, cx, cy, r * 1.25, col, 0.18 * a, z=z - 1)
    ax.add_patch(Circle((cx, cy), r, fc=(*col, 0.07 * a), ec=(*col, 0.55 * a), lw=1.4, zorder=z))
    for normal in ([0, 0, 1], [1, 0, 0]):     # two great circles for 3D feel
        u = np.cross(normal, [0.3, 0.5, 0.8]); u /= np.linalg.norm(u); w = np.cross(normal, u)
        th = np.linspace(0, 2 * np.pi, 120)
        pts = np.array([proj(R, np.cos(q) * u + np.sin(q) * w)[0] for q in th])
        ax.plot(cx + r * pts[:, 0], cy + r * pts[:, 1], color=(*col, 0.22 * a), lw=0.8, zorder=z)


def arrow3(ax, cx, cy, r, R, v, col, a, lw=4, z=14, lab=None, lab_off=1.18, size=20):
    if a <= 0.01:
        return
    p, _ = proj(R, v)
    x1, y1 = cx + r * p[0], cy + r * p[1]
    for m, am in ((3.0, 0.15), (1.0, 1.0)):
        ax.add_patch(FancyArrowPatch((cx, cy), (x1, y1), arrowstyle="-|>,head_length=10,head_width=6",
                                     mutation_scale=1.5, color=(*col, a * am), lw=lw * m, zorder=z))
    if lab:
        V.text(ax, cx + r * lab_off * p[0], cy + r * lab_off * p[1], lab, a=a, size=size, color=col, weight="bold", z=z + 1)


def angle_arc(ax, cx, cy, r, R, u, v, col, a, frac=1.0, z=13):
    if a <= 0.01:
        return
    u, v = K.unit(u), K.unit(v)
    om = np.arccos(np.clip(u @ v, -1, 1))
    ts = np.linspace(0, frac, 60)
    pts = np.array([proj(R, (np.sin((1 - s) * om) * u + np.sin(s * om) * v) / np.sin(om))[0] for s in ts])
    ax.plot(cx + r * pts[:, 0], cy + r * pts[:, 1], color=(*col, a), lw=2.4, zorder=z)
    mid = proj(R, K.unit(u + v))[0]
    V.text(ax, cx + r * 1.45 * mid[0], cy + r * 1.45 * mid[1], r"$\varphi$", a=a * min(1, frac * 2), size=24,
           color=col, weight="bold", z=z + 1)


# ------------------------------------------------------------------ many events (parton-level toy)
N_TOT = 200000
_rng = np.random.default_rng(5)
SAMP = K.sample_linear(_rng, N_TOT, slope=-D_OBS)
NB = 20
EDGES = np.linspace(-1, 1, NB + 1)


def n_events(t):
    if t < T4_FAST:
        return int(np.clip((t - T4_0) / 0.6, 0, 9)) + 1 if t >= T4_0 else 0
    x = ramp(t, T4_FAST, T4_FULL)
    return int(10 * (N_TOT / 10) ** x)


T4_0, T4_FAST, T4_FULL = 36.2, 41.6, 46.5
_CUM = None


def hist_counts(n):
    return np.histogram(SAMP[:n], EDGES)[0]


def glyph_vectors(i):
    """random pair of unit vectors with the i-th sampled cos φ (for the per-event glyph)."""
    r = np.random.default_rng(1000 + i)
    a = K.rand_dir(r)
    c = SAMP[i]; s = np.sqrt(1 - c * c)
    p = K.unit(np.cross(a, K.rand_dir(r)))
    return a, c * a + s * p


# ------------------------------------------------------------------ CMS figure
_IMG = None


def cms_img():
    global _IMG
    if _IMG is None:
        _IMG = np.asarray(Image.open(os.path.join(HERE, "assets", "CMS_TOP-23-001_Fig6a.png")).convert("RGB")) / 255.0
    return _IMG


# ------------------------------------------------------------------ frame
def frame(t, path):
    fig, ax = V.new_figure(plt)
    frame_common(ax, t)

    # ---------------- scene 1+2: event display
    if t < 22.0:
        a_det = ramp(t, 0.2, 1.2) * (1 - ramp(t, 20.8, 21.8))
        mv = ramp(t, 11.0, 12.6)
        cx = -0.0 * (1 - mv) + (-2.75) * mv
        cy = -0.45 * (1 - mv) + (-0.55) * mv
        s = 1.33 * (1 - mv) + 1.06 * mv
        prog = ramp(t, 1.0, 7.0) ** 0.9
        # emphasis during reconstruction
        g1, g2, g3 = ramp(t, 13.0, 13.8), ramp(t, 15.4, 16.2), ramp(t, 17.8, 18.6)
        dim = 0.25
        emph = {"ue": 1 - 0.65 * max(g1, 0) * (1 - g3) - 0.65 * g3}
        for tag in ("lp", "b"):          # t-side objects dim while the t̄ is being assembled
            emph[tag] = 1 - (1 - dim) * g1 * (1 - g2)
        for tag in ("lm", "bb"):          # t̄-side objects dim while the t is being assembled
            emph[tag] = 1 - (1 - dim) * g2 * (1 - g3)
        emph["met"] = 1.0
        DISP.draw(ax, cx, cy, s, prog=prog, alpha=a_det, emph=emph)
        a_title = ramp(t, 0.2, 1.0) * (1 - ramp(t, 10.6, 11.2))
        title(ax, "One top-quark pair, seen by CMS", a_title,
              sub=r"pp $\rightarrow$ $t\bar{t}$ $\rightarrow$ ($b\,e^{+}\nu$) ($\bar{b}\,\mu^{-}\bar{\nu}$)     transverse view, 3.8 T field")
        # object labels
        a_lab = ramp(t, 6.5, 7.5) * a_det
        if a_lab > 0.01:
            for tag, p, txt, col in (("lp", L["t"]["l"], "e⁺", C_LP), ("lm", L["tb"]["l"], "μ⁻", C_LM),
                                     ("b", L["t"]["b"], "b jet", C_B), ("bb", L["tb"]["b"], r"$\bar{b}$ jet", C_B)):
                rr, pp = LAB_POS[tag]
                x, y = obj_anchor(cx, cy, s, K.phi(p), rr, pp * s / 1.33)
                label(ax, x, y, txt, col, a_lab * emph.get(tag, 1), size=19 if mv < 0.5 else 16)
                # scene 2: which top it came from
                side = "t" if tag in ("lp", "b") else "tb"
                ga = ramp(t, 15.4, 16.2) if side == "t" else ramp(t, 13.0, 13.8)
                if ga > 0.01 and mv > 0.5:
                    gc = C_T if side == "t" else C_TB
                    V.glow_disc(ax, x, y, 0.62, gc, 0.45 * ga * a_det, z=39)
                    label(ax, x + 0.42, y + 0.30, "t" if side == "t" else r"$\bar{t}$", gc, ga * a_det, size=16)
            ph = EV["met_phi"]
            x, y = DISP.anchor(cx, cy, s, ph, 0.55 + 0.012 * EV["met_pt"] + 0.22)
            label(ax, x, y, r"$p_T^{miss}$ (ν ν̄)", C_MET, a_lab, size=17 if mv < 0.5 else 15)
        a_cap = ramp(t, 7.6, 8.4) * (1 - ramp(t, 10.6, 11.2))
        if a_cap > 0.01:
            V.pill(ax, 0, -4.3, "2 leptons + 2 b jets + missing momentum from 2 escaping neutrinos", a=a_cap, size=17,
                   accent=V.ACCENT)
        # ---- scene 2 panel
        a_p = ramp(t, 12.2, 13.0) * (1 - ramp(t, 20.8, 21.8))
        if a_p > 0.01:
            title(ax, "Reconstruct the top and the anti-top", a_p,
                  sub="each top decays before it can hadronize (τ ≈ 5×10⁻²⁵ s)")
            x0 = 0.95
            a_t = ramp(t, 15.4, 16.2)
            a_tb = ramp(t, 13.0, 13.8)
            V.text(ax, x0, 2.55, r"$\bar{t}\ \rightarrow\ W^{-}\,\bar{b}\ \rightarrow\ \mu^{-}\,\bar{\nu}\ \bar{b}$", a=a_p * a_tb,
                   size=25, color=C_TB, ha="left")
            V.text(ax, x0, 1.75, r"$t\ \rightarrow\ W^{+}\,b\ \rightarrow\ e^{+}\,\nu\ b$", a=a_p * a_t, size=25,
                   color=C_T, ha="left")
            a_nu = ramp(t, 17.8, 18.6)
            V.text(ax, x0, 0.85, "two neutrinos escape: solve with", a=a_p * a_nu, size=16, color=V.GREY, ha="left")
            V.text(ax, x0, 0.40, r"$m_W,\ m_t$ and $\vec{p}_T^{\,miss} = \vec{p}_T^{\,\nu} + \vec{p}_T^{\,\bar{\nu}}$",
                   a=a_p * a_nu, size=18, color=V.WHITE, ha="left")
            a_c1 = ramp(t, 19.0, 19.6)
            a_c2 = ramp(t, 19.6, 20.2)
            V.pill(ax, x0 + 2.55, -0.85, rf"$m(t\bar{{t}})$ = {EV['mtt']:.0f} GeV    $\checkmark$  345–400 GeV", a=a_p * a_c1, size=17,
                   accent=C_T, w=5.1)
            V.text(ax, x0 + 0.05, -1.42, r"just above threshold $2m_t$ ≈ 345 GeV, where the spins are most entangled", a=a_p * a_c1,
                   size=13.5, color=V.GREY, ha="left")
            V.pill(ax, x0 + 2.55, -2.25, rf"$\beta_z(t\bar{{t}})$ = {EV['bz']:.2f}    $\checkmark$  < 0.9", a=a_p * a_c2, size=17,
                   accent=C_TB, w=5.1)

    # ---------------- scene 3: boosts
    a3 = ramp(t, 21.6, 22.6) * (1 - ramp(t, 34.4, 35.4))
    if a3 > 0.01:
        yaw = 0.35 + 0.10 * np.sin((t - 21) * 0.35)
        R = rotm(yaw, 0.30)
        title(ax, "From the event to one number:  cos φ", a3, sub="the lepton flies off along its parent top's spin")
        # phase A: tt̄ rest frame (22-26)
        aA = ramp(t, 22.0, 22.8) * (1 - ramp(t, 25.8, 26.6))
        if aA > 0.01:
            cx0, cy0 = 0.0, -0.2
            sep = 1.85 * ramp(t, 22.6, 24.6)
            n2, _ = proj(R, EV["n_cm"])
            n2 = n2 / max(np.linalg.norm(n2), 1e-6)
            for sgn, col, lab in ((1, C_T, "t"), (-1, C_TB, r"$\bar{t}$")):
                x, y = cx0 + sgn * sep * n2[0], cy0 + sgn * sep * n2[1]
                if sep > 0.05:
                    ax.add_patch(FancyArrowPatch((cx0, cy0), (x, y), arrowstyle="-|>,head_length=10,head_width=6",
                                                 mutation_scale=1.5, color=(*col, 0.8 * aA * a3), lw=2.5, zorder=12))
                sphere(ax, x, y, 0.42, R, col, aA * a3)
                label(ax, x + 0.62 * sgn * n2[0], y + 0.62 * sgn * n2[1] + 0.05, lab, col, aA * a3, size=24)
            ax.scatter([cx0], [cy0], s=30, c=[(1, 1, 1, aA * a3)], zorder=13)
            V.pill(ax, 0, -3.6, rf"1.  boost to the $t\bar{{t}}$ rest frame: $t$ and $\bar{{t}}$ fly back to back  (|p| = {EV['pstar']:.0f} GeV)",
                   a=aA * a3, size=17, accent=V.ACCENT)
        # phase B: each top's rest frame (26-35)
        aB = ramp(t, 26.0, 26.8)
        if aB > 0.01:
            m = ramp(t, 30.2, 32.0)
            r = 1.45
            xl, xr = -3.0 * (1 - m), 3.0 * (1 - m)
            y0 = -0.35
            sphere(ax, xl, y0, r, R, C_T, aB * a3 * (1 - 0.5 * m))
            sphere(ax, xr, y0, r, R, C_TB, aB * a3 * (1 - m))
            g = ramp(t, 27.0, 28.0)
            arrow3(ax, xl, y0, r, R, EV["lp"], C_LP, aB * a3 * g, lab=r"$\hat{\ell}^{+}$")
            arrow3(ax, xr, y0, r, R, EV["lm"], C_LM, aB * a3 * g, lab=r"$\hat{\ell}^{-}$")
            if m < 0.6:
                label(ax, xl, y0 - r - 0.38, "t rest frame", C_T, aB * a3 * (1 - ramp(t, 30.2, 31.0)), size=17)
                label(ax, xr, y0 - r - 0.38, r"$\bar{t}$ rest frame", C_TB, aB * a3 * (1 - ramp(t, 30.2, 31.0)), size=17)
            V.pill(ax, 0, -3.6, "2.  boost each top to rest: the lepton direction analyzes the top spin",
                   a=aB * a3 * (1 - ramp(t, 30.0, 30.8)), size=17, accent=V.ACCENT)
            fa = ramp(t, 32.0, 33.0)
            angle_arc(ax, 0, y0, r * 0.42, R, EV["lp"], EV["lm"], (1, 1, 1), aB * a3 * fa, frac=fa)
            aC = ramp(t, 32.6, 33.4)
            if aC > 0.01:
                V.text(ax, 0, 2.55, rf"$\cos\varphi\ =\ \hat{{\ell}}^{{+}}\cdot\hat{{\ell}}^{{-}}\ =\ {EV['cphi']:+.2f}$",
                       a=aC * a3, size=34, weight="bold")
                V.pill(ax, 0, -3.6, "3.  one event → one number.   Spin singlet (entangled) → leptons prefer parallel, cos φ → +1",
                       a=aC * a3, size=16, accent=V.ACCENT)

    # ---------------- scene 4: many events
    a4 = ramp(t, 35.2, 36.0) * (1 - ramp(t, 49.6, 50.4))
    if a4 > 0.01:
        title(ax, "Repeat for every event", a4, sub=r"345 < $m(t\bar{t})$ < 400 GeV,   $\beta_z(t\bar{t})$ < 0.9")
        n = n_events(t)
        # glyph of the current event
        gx, gy, gr = -4.35, 1.0, 1.05
        Rg = rotm(0.5 + 0.2 * t, 0.35)
        sphere(ax, gx, gy, gr, Rg, (0.8, 0.85, 1.0), a4 * 0.8)
        if n > 0:
            u, v = glyph_vectors(n - 1)
            arrow3(ax, gx, gy, gr, Rg, u, C_LP, a4, lw=3)
            arrow3(ax, gx, gy, gr, Rg, v, C_LM, a4, lw=3)
            V.text(ax, gx, gy - gr - 0.45, f"cos φ = {SAMP[n - 1]:+.2f}", a=a4 * (1 - ramp(t, T4_FAST, T4_FAST + 0.6)),
                   size=19, weight="bold")
        V.text(ax, gx, -1.35, "events", a=a4, size=15, color=V.GREY)
        V.text(ax, gx, -1.85, f"{n:,}", a=a4, size=30, weight="bold", color=V.WHITE)
        # histogram
        hx0, hx1, hy0, hh = -2.4, 5.8, -3.0, 5.0
        X = lambda c: hx0 + (c + 1) / 2 * (hx1 - hx0)
        Y = lambda d: hy0 + d / 1.0 * hh
        ax.plot([hx0, hx1], [hy0, hy0], color=(1, 1, 1, 0.5 * a4), lw=1.2, zorder=20)
        ax.plot([hx0, hx0], [hy0, hy0 + hh], color=(1, 1, 1, 0.3 * a4), lw=1.0, zorder=20)
        for c in (-1, -0.5, 0, 0.5, 1):
            V.text(ax, X(c), hy0 - 0.3, f"{c:g}", a=a4, size=14, color=V.GREY)
        V.text(ax, X(0), hy0 - 0.75, r"$\cos\varphi$", a=a4, size=20)
        for d in (0.25, 0.5, 0.75):
            ax.plot([hx0, hx1], [Y(d), Y(d)], color=(1, 1, 1, 0.06 * a4), lw=0.8, zorder=19)
            V.text(ax, hx0 - 0.12, Y(d), f"{d:g}", a=a4, size=12, color=V.DIM, ha="right")
        V.text(ax, hx0 - 0.72, Y(0.5), r"$(1/\sigma)\ d\sigma/d\cos\varphi$", a=a4, size=16, color=V.GREY,
               rotation=90)
        if n > 0:
            cnt = hist_counts(n)
            bw = 2 / NB
            unit_tok = 0.11                                   # height of one event while n is small
            scale = min(unit_tok * hh, hh / (n * bw)) / hh    # density units per event
            for k in range(NB):
                hgt = cnt[k] * scale
                if hgt > 0:
                    ax.add_patch(Rectangle((X(EDGES[k]) + 0.02, hy0), X(EDGES[k + 1]) - X(EDGES[k]) - 0.04, hgt * hh,
                                           fc=(*V.ACCENT, 0.75 * a4), ec=(*V.ACCENT, a4), lw=0.8, zorder=21))
            # newest event token (slow phase)
            if t < T4_FAST:
                k = min(np.searchsorted(EDGES, SAMP[n - 1]) - 1, NB - 1)
                fl = 1 - ramp(t, T4_0 + 0.6 * (n - 1), T4_0 + 0.6 * (n - 1) + 0.35)
                if fl > 0:
                    V.glow_disc(ax, 0.5 * (X(EDGES[k]) + X(EDGES[k + 1])), hy0 + cnt[k] * scale * hh, 0.4, (1, 1, 1),
                                0.6 * fl * a4, z=22)
            mean = SAMP[:n].mean()
            a_m = ramp(t, T4_FAST, T4_FAST + 0.8)
            V.text(ax, gx, -2.7, rf"$\langle\cos\varphi\rangle$ = {mean:+.3f}", a=a4 * a_m, size=18)
            V.text(ax, gx, -3.3, rf"$D = -3\langle\cos\varphi\rangle$ = {-3 * mean:+.3f}", a=a4 * a_m, size=18,
                   weight="bold", color=(1, 0.9, 0.5))
        # reference curves
        c = np.linspace(-1, 1, 50)
        for i, (Dv, col, ls, txt) in enumerate(((0.0, (0.7, 0.7, 0.75), (0, (5, 4)), "D = 0   no spin correlation"),
                                                (-1 / 3, (1.0, 0.75, 0.3), (0, (2, 2)), "D = −1/3   entanglement limit"),
                                                (-1.0, (0.85, 0.5, 1.0), (0, (1, 2)), "D = −1   pure spin singlet"))):
            ar = ramp(t, 46.8 + 0.7 * i, 47.5 + 0.7 * i) * a4
            if ar > 0.01:
                ax.plot(X(c), Y(0.5 * (1 - Dv * c)), color=(*col, ar), lw=2.4, ls=ls, zorder=23)
                V.text(ax, hx0 + 0.15, Y(0.98) - 0.42 * i, txt, a=ar, size=15, color=col, ha="left")
        ar = ramp(t, 47.0, 47.8) * a4
        V.text(ax, X(0), hy0 - 1.25, "illustration: parton-level toy events drawn from ½(1 − D cos φ) with the measured D",
               a=ar * 0.9, size=13, color=V.GREY)

    # ---------------- scene 5: CMS result
    a5 = ramp(t, 50.2, 51.2)
    if a5 > 0.01:
        title(ax, "CMS: entanglement of top quarks observed", a5, sub=r"36.3 fb$^{-1}$, 13 TeV, dilepton $t\bar{t}$ near threshold")
        img = cms_img()
        h_, w_ = img.shape[:2]
        cw = 6.4; chh = cw * h_ / w_
        x0, y0 = -6.15, -3.75
        ax.add_patch(FancyBboxPatch((x0 - 0.1, y0 - 0.1), cw + 0.2, chh + 0.2, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=(1, 1, 1, a5), ec="none", zorder=30))
        ax.imshow(img, extent=(x0, x0 + cw, y0, y0 + chh), zorder=31, alpha=a5, interpolation="lanczos")
        V.text(ax, x0 + cw / 2, y0 - 0.38, "Fig. 6 (left): detector-level cos φ, post-fit", a=a5, size=13, color=V.GREY)
        # number line
        nx0, nx1, ny = 1.25, 5.95, 0.55
        Xd = lambda d: nx0 + (d + 1) * (nx1 - nx0)
        al = ramp(t, 51.4, 52.2) * a5
        if al > 0.01:
            ax.add_patch(Rectangle((Xd(-1), ny - 0.55), Xd(-1 / 3) - Xd(-1), 1.1, fc=(0.3, 0.85, 0.75, 0.13 * al),
                                   ec="none", zorder=30))
            V.text(ax, 0.5 * (Xd(-1) + Xd(-1 / 3)), ny + 0.85, "entangled", a=al, size=17, color=(0.4, 0.95, 0.85),
                   weight="bold")
            V.text(ax, 0.5 * (Xd(-1 / 3) + Xd(0)), ny + 0.85, "separable", a=al, size=17, color=V.GREY)
            ax.plot([Xd(-1), Xd(0)], [ny, ny], color=(1, 1, 1, 0.7 * al), lw=1.6, zorder=31)
            for d, s_ in ((-1, "−1"), (-2 / 3, "−2/3"), (-1 / 3, "−1/3"), (0, "0")):
                ax.plot([Xd(d), Xd(d)], [ny - 0.12, ny + 0.12], color=(1, 1, 1, 0.7 * al), lw=1.4, zorder=31)
                V.text(ax, Xd(d), ny - 0.42, s_, a=al, size=15, color=V.GREY)
            ax.plot([Xd(-1 / 3)] * 2, [ny - 0.55, ny + 0.55], color=(1, 0.75, 0.3, al), lw=2, ls=(0, (2, 2)), zorder=31)
            V.text(ax, Xd(-0.5), ny - 0.95, "D", a=al, size=19, weight="bold")
        ap = ramp(t, 52.6, 53.4) * a5
        if ap > 0.01:
            yo = ny + 0.22
            ax.plot([Xd(D_OBS - D_DN), Xd(D_OBS + D_UP)], [yo, yo], color=(1, 1, 1, ap), lw=3, zorder=33)
            V.glow_points(ax, [[Xd(D_OBS), yo]], 120, [(1, 1, 1)], ap, z=34)
            ax.scatter([Xd(D_EXP)], [ny - 0.2], s=80, facecolors="none", edgecolors=[(0.5, 0.75, 1, ap)], lw=2, zorder=34)
            V.text(ax, 3.6, -1.25, r"$D_{obs} = -0.480^{\,+0.026}_{\,-0.029}$", a=ap, size=26, weight="bold")
            V.text(ax, 3.6, -1.95, "expected (SM + toponium)  −0.467", a=ap, size=15, color=(0.6, 0.8, 1))
        aS = ramp(t, 54.0, 54.8) * a5
        if aS > 0.01:
            V.pill(ax, 3.6, -2.85, f"{SIGNIF}σ away from 'no entanglement'", a=aS, size=20, accent=(0.4, 0.95, 0.85),
                   weight="bold")
            V.text(ax, 3.6, 2.25, "rising data: lepton pairs prefer cos φ → +1", a=aS, size=15, color=V.GREY)
            V.text(ax, 3.6, 1.85, "fit unfolds detector effects → parton-level D", a=aS, size=15, color=V.GREY)
        V.text(ax, 0, -4.5, REF, a=a5 * 0.9, size=12, color=V.DIM)

    V.signature(fig)
    V.save(fig, path)
    plt.close(fig)


if __name__ == "__main__":
    if "--info" in sys.argv:
        print({k: EV[k] for k in ("mtt", "bz", "cphi", "met_pt", "rng_seed")})
        for side in ("t", "tb"):
            for o in ("l", "b", "nu"):
                p = L[side][o]; print(side, o, f"pt={K.pt(p):.1f} eta={K.eta(p):+.2f} phi={K.phi(p):+.2f}")
        sys.exit()
    main(frame, T_END, FPS)
