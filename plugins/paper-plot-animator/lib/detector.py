"""Generic barrel-detector event display (transverse r-phi view) for matplotlib video frames.

CMS-like layout (radii are *display* units, not metres, so the tracker gets room):
tracker 0-1, ECAL 1.06-1.22, HCAL 1.28-1.72, solenoid 1.78-1.88, 4 muon stations (12-sided wheels) 2.0-2.85.
Change LAYERS for ATLAS/ALICE-like looks.

Usage
-----
    D = EventDisplay()
    D.track(pt=45, phi0=0.6, q=+1, color=..., kind="e", tag="e+")   # kind: 'had' | 'e' | 'mu'
    D.tower(phi=0.6, e=40, layer="ecal", tag="e+")
    D.jet(phi=2.1, et=80, tag="b")
    D.met(phi=-2.4, et=70)
    ...
    D.draw(ax, cx, cy, s, prog=t, alpha=a, emph={"e+": 1.0, "b": 0.3})
`prog` 0->1 grows the event from the vertex outwards (tracks first, then calorimeter towers, muon hits, MET).
`emph`: per-tag brightness multiplier (tags not listed get `emph_default`).
"""
import numpy as np
from matplotlib.patches import Wedge, Circle, Polygon, FancyArrowPatch
from matplotlib.collections import LineCollection

B_FIELD = 3.8            # T
R_TRK_PHYS = 1.1         # m, physical tracker radius mapped to display radius 1.0
LAYERS = dict(trk=(0.0, 1.0), ecal=(1.06, 1.22), hcal=(1.28, 1.72), sol=(1.78, 1.88),
              mu=[(2.00, 2.10), (2.25, 2.35), (2.50, 2.60), (2.75, 2.85)])
COL = dict(trk_fill=(0.55, 0.65, 0.85, 0.05), trk_edge=(0.55, 0.65, 0.85, 0.30),
           ecal=(0.30, 0.75, 0.55), hcal=(0.40, 0.60, 0.95), sol=(0.65, 0.65, 0.70),
           mu=(0.85, 0.45, 0.45), ecal_e=(1.0, 0.25, 0.25), hcal_e=(0.35, 0.55, 1.0),
           jet=(1.0, 0.85, 0.25), met=(1.0, 0.35, 0.85), had=(0.80, 0.86, 0.95))


def _ease(x):
    x = np.clip(x, 0, 1); return float(np.clip(x * x * x * (x * (6 * x - 15) + 10), 0, 1))


class EventDisplay:
    def __init__(self, emph_default=1.0):
        self.tracks, self.towers, self.jets, self.mets = [], [], [], []
        self.emph_default = emph_default

    # ---------- content ----------
    def track(self, pt, phi0, q, color=None, kind="had", tag=None, lw=None):
        """charged track; pt GeV. kind 'mu' continues through the calorimeters into the muon stations."""
        R = pt / (0.3 * B_FIELD) / R_TRK_PHYS          # radius of curvature in display units
        self.tracks.append(dict(pt=pt, phi0=phi0, q=q, R=R, color=color or COL["had"], kind=kind, tag=tag,
                                lw=lw or (2.6 if kind != "had" else 0.9)))

    def tower(self, phi, e, layer="ecal", tag=None, dphi=0.087):
        self.towers.append(dict(phi=phi, e=e, layer=layer, tag=tag, dphi=dphi))

    def jet(self, phi, et, tag=None, half=0.35, label=None):
        self.jets.append(dict(phi=phi, et=et, tag=tag, half=half, label=label))

    def met(self, phi, et, tag="met"):
        self.mets.append(dict(phi=phi, et=et, tag=tag))

    # ---------- geometry ----------
    @staticmethod
    def helix_xy(trk, rmax=1.0, n=120):
        """points of a track in display units, from the vertex to radius rmax (or until it curls back)."""
        R, q, p0 = trk["R"], trk["q"], trk["phi0"]
        # circle centre: perpendicular to the initial direction; sign by charge (B along +z)
        cxy = R * np.array([np.sin(p0) * q, -np.cos(p0) * q])
        # parameter = turning angle a; position = c + R*(-sin(p0)q, cos(p0)q) rotated by -q*a
        reach = 2 * R                                     # max distance from the vertex
        if reach > rmax:
            amax = 2 * np.arcsin(min(rmax / (2 * R), 1.0))
        else:
            amax = np.pi * 0.98                           # loopers: half a turn
        a = np.linspace(0, amax, n)
        x0, y0 = -cxy
        ang0 = np.arctan2(y0, x0)
        ang = ang0 - q * a
        return np.stack([cxy[0] + R * np.cos(ang), cxy[1] + R * np.sin(ang)], 1)

    def exit_phi(self, trk):
        xy = self.helix_xy(trk)
        return float(np.arctan2(xy[-1, 1], xy[-1, 0]))

    # ---------- drawing ----------
    def draw_detector(self, ax, cx, cy, s, alpha=1.0, z=1):
        if alpha <= 0.01:
            return
        r0, r1 = LAYERS["trk"]
        ax.add_patch(Circle((cx, cy), r1 * s, fc=COL["trk_fill"][:3] + (COL["trk_fill"][3] * alpha,),
                            ec=COL["trk_edge"][:3] + (COL["trk_edge"][3] * alpha,), lw=1.0, zorder=z))
        for rr in (0.25, 0.5, 0.75):        # strip layers
            ax.add_patch(Circle((cx, cy), rr * s, fc="none", ec=(0.55, 0.65, 0.85, 0.10 * alpha), lw=0.6, zorder=z))
        for key, a_ in (("ecal", 0.22), ("hcal", 0.16), ("sol", 0.22)):
            ri, ro = LAYERS[key]
            ax.add_patch(Wedge((cx, cy), ro * s, 0, 360, width=(ro - ri) * s, fc=COL[key] + (a_ * alpha,),
                               ec=COL[key] + (0.45 * alpha,), lw=0.6, zorder=z))
        # muon stations: 12-sided wheels with gaps
        for ri, ro in LAYERS["mu"]:
            for k in range(12):
                a0 = np.pi / 12 * (2 * k - 1) + 0.03; a1 = np.pi / 12 * (2 * k + 1) - 0.03
                pts = []
                for r_ in (ri, ro):
                    rr = r_ / np.cos(np.pi / 12)
                    pts.append((cx + rr * s * np.cos(a0), cy + rr * s * np.sin(a0)))
                    pts.append((cx + rr * s * np.cos(a1), cy + rr * s * np.sin(a1)))
                poly = [pts[0], pts[1], pts[3], pts[2]]
                ax.add_patch(Polygon(poly, closed=True, fc=COL["mu"] + (0.16 * alpha,), ec=COL["mu"] + (0.40 * alpha,),
                                     lw=0.5, zorder=z))

    def _em(self, tag, emph):
        if emph is None:
            return 1.0
        return emph.get(tag, self.emph_default)

    def draw(self, ax, cx, cy, s, prog=1.0, alpha=1.0, emph=None, det_alpha=None, z=5):
        """prog: 0-0.55 tracks grow, 0.45-0.8 towers/jets, 0.6-0.9 muon hits, 0.75-1 MET."""
        self.draw_detector(ax, cx, cy, s, alpha if det_alpha is None else det_alpha, z=z - 4)
        if alpha <= 0.01:
            return
        g_trk = _ease(prog / 0.55)
        g_cal = _ease((prog - 0.45) / 0.35)
        g_mu = _ease((prog - 0.6) / 0.3)
        g_met = _ease((prog - 0.75) / 0.25)
        # jets (cones) underneath
        for j in self.jets:
            a = alpha * g_cal * self._em(j["tag"], emph)
            if a > 0.01:
                rr = LAYERS["hcal"][1] * s * 1.02
                ax.add_patch(Wedge((cx, cy), rr, np.degrees(j["phi"] - j["half"]), np.degrees(j["phi"] + j["half"]),
                                   fc=COL["jet"] + (0.13 * a,), ec=COL["jet"] + (0.55 * a,), lw=1.2, zorder=z - 1))
        # tracks
        segs, cols, lws = [], [], []
        for t in self.tracks:
            a = alpha * self._em(t["tag"], emph)
            if a <= 0.01 or g_trk <= 0:
                continue
            xy = self.helix_xy(t)
            path = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
            keep = path <= g_trk * path[-1] + 1e-9
            xy = xy[keep]
            if t["kind"] == "mu" and g_mu > 0:
                ph = np.arctan2(xy[-1, 1], xy[-1, 0])
                rmax = 1.0 + g_mu * (LAYERS["mu"][-1][1] + 0.05 - 1.0)
                ext = np.stack([np.linspace(1.0, rmax, 40) * np.cos(ph), np.linspace(1.0, rmax, 40) * np.sin(ph)], 1)
                xy = np.concatenate([xy, ext])
            if len(xy) < 2:
                continue
            P = np.stack([cx + xy[:, 0] * s, cy + xy[:, 1] * s], 1)
            c = np.asarray(t["color"], float)
            for mult, am in ((3.0, 0.12), (1.0, 1.0)) if t["kind"] != "had" else ((1.0, 0.75),):
                ax.add_collection(LineCollection([P], colors=[(*c, a * am)], linewidths=t["lw"] * mult,
                                                 zorder=z + (1 if t["kind"] != "had" else 0), capstyle="round"))
            if t["kind"] == "mu" and g_mu > 0:     # station hits
                ph = np.arctan2(xy[-1, 1], xy[-1, 0])
                for k, (ri, ro) in enumerate(LAYERS["mu"]):
                    if g_mu * 4 > k:
                        rm = 0.5 * (ri + ro)
                        ax.scatter([cx + rm * s * np.cos(ph)], [cy + rm * s * np.sin(ph)], s=60, marker="s",
                                   c=[(*c, a)], edgecolors="white", linewidths=0.6, zorder=z + 2)
        # towers
        for tw in self.towers:
            a = alpha * g_cal * self._em(tw["tag"], emph)
            if a <= 0.01:
                continue
            base = LAYERS["ecal"][0] if tw["layer"] == "ecal" else LAYERS["hcal"][0]
            L = 0.10 + 0.18 * np.log1p(tw["e"] / 5.0)
            L *= g_cal
            col = COL["ecal_e"] if tw["layer"] == "ecal" else COL["hcal_e"]
            ax.add_patch(Wedge((cx, cy), (base + L) * s, np.degrees(tw["phi"] - tw["dphi"] / 2),
                               np.degrees(tw["phi"] + tw["dphi"] / 2), width=L * s, fc=col + (0.85 * a,),
                               ec=(1, 1, 1, 0.5 * a), lw=0.5, zorder=z + 1))
        # MET
        for m in self.mets:
            a = alpha * g_met * self._em(m["tag"], emph)
            if a <= 0.01:
                continue
            L = (0.4 + 0.012 * m["et"]) * s * g_met
            ax.add_patch(FancyArrowPatch((cx, cy), (cx + L * np.cos(m["phi"]), cy + L * np.sin(m["phi"])),
                                         arrowstyle="-|>,head_length=8,head_width=5", mutation_scale=1.6,
                                         color=COL["met"] + (a,), lw=3.0, linestyle=(0, (4, 2)), zorder=z + 3))
        # vertex
        ax.scatter([cx], [cy], s=18, c=[(1, 1, 1, alpha)], zorder=z + 4, edgecolors="none")

    def anchor(self, cx, cy, s, phi, r):
        """data coordinates of display radius r at angle phi (for labels/callouts)."""
        return cx + r * s * np.cos(phi), cy + r * s * np.sin(phi)


def underlying_event(D, rng, n=30, ptmin=0.4, ptmax=3.0):
    """soft charged tracks (loopers and gentle curves)."""
    for _ in range(n):
        pt = ptmin * (ptmax / ptmin) ** rng.uniform()
        D.track(pt=pt, phi0=rng.uniform(-np.pi, np.pi), q=rng.choice([-1, 1]), kind="had", tag="ue")
