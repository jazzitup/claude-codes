"""Minimal relativistic kinematics for building honest toy events (numpy only).

Four-vectors are numpy arrays [E, px, py, pz] (GeV). All functions accept a single vector.
"""
import numpy as np


def p4(m, p3):
    p3 = np.asarray(p3, float)
    return np.array([np.sqrt(m * m + p3 @ p3), *p3])


def mass(p):
    return float(np.sqrt(max(p[0] ** 2 - p[1:] @ p[1:], 0.0)))


def pt(p):
    return float(np.hypot(p[1], p[2]))


def eta(p):
    pp = np.linalg.norm(p[1:])
    return float(0.5 * np.log((pp + p[3]) / max(pp - p[3], 1e-12)))


def phi(p):
    return float(np.arctan2(p[2], p[1]))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def boost(p, beta):
    """Boost four-vector p by velocity vector beta (passive: returns p seen in a frame moving with -beta... i.e.
    standard active boost: a particle at rest boosted by beta ends with velocity beta)."""
    beta = np.asarray(beta, float)
    b2 = beta @ beta
    if b2 < 1e-16:
        return np.array(p, float)
    g = 1.0 / np.sqrt(1 - b2)
    bp = beta @ p[1:]
    g2 = (g - 1) / b2
    E = g * (p[0] + bp)
    v = p[1:] + g2 * bp * beta + g * beta * p[0]
    return np.array([E, *v])


def to_rest_frame(p, parent):
    """Express p in the rest frame of `parent`."""
    return boost(p, -parent[1:] / parent[0])


def beta_of(p):
    return p[1:] / p[0]


def two_body(M, m1, m2, direction):
    """Two-body decay at rest: returns (p1, p2) with p1 along `direction`."""
    pst = np.sqrt(max((M * M - (m1 + m2) ** 2) * (M * M - (m1 - m2) ** 2), 0)) / (2 * M)
    d = unit(direction)
    return p4(m1, pst * d), p4(m2, -pst * d)


def rand_dir(rng):
    c = rng.uniform(-1, 1); s = np.sqrt(1 - c * c); a = rng.uniform(0, 2 * np.pi)
    return np.array([s * np.cos(a), s * np.sin(a), c])


def sph_dir(theta, phi_):
    return np.array([np.sin(theta) * np.cos(phi_), np.sin(theta) * np.sin(phi_), np.cos(theta)])


def sample_linear(rng, n, slope, lo=-1.0, hi=1.0):
    """Draw n values from f(x) ∝ 1 + slope*x on [lo, hi] (accept-reject). e.g. (1 - D cos phi): slope = -D."""
    out = np.empty(0)
    fmax = 1 + abs(slope) * max(abs(lo), abs(hi))
    while out.size < n:
        x = rng.uniform(lo, hi, 2 * n)
        keep = rng.uniform(0, fmax, 2 * n) < 1 + slope * x
        out = np.concatenate([out, x[keep]])
    return out[:n]
