#!/usr/bin/env python3

import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import hsv_to_rgb
from scipy.special import gamma


def plot_gamma_complex(
    re_lim=(-5, 5),
    im_lim=(-5, 5),
    resolution=800,
    output_file=None,
):
    """
    Plot the Euler gamma function Gamma(z) in the complex plane using domain coloring.
    """
    x = np.linspace(re_lim[0], re_lim[1], resolution)
    y = np.linspace(im_lim[0], im_lim[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    W = gamma(Z)

    phase = np.angle(W)
    hue = (phase + np.pi) / (2 * np.pi)

    mag = np.abs(W)
    logmag = np.log1p(mag)
    value = 0.6 + 0.4 * (1 + np.cos(2 * np.pi * logmag)) / 2

    finite = np.isfinite(W.real) & np.isfinite(W.imag) & np.isfinite(mag)
    saturation = np.ones_like(value)
    value = np.where(finite, value, 0.0)
    saturation = np.where(finite, saturation, 0.0)

    hsv = np.dstack((hue, saturation, value))
    rgb = hsv_to_rgb(hsv)

    plt.figure(figsize=(8, 8))
    plt.imshow(
        rgb,
        extent=(re_lim[0], re_lim[1], im_lim[0], im_lim[1]),
        origin="lower",
        aspect="equal",
    )
    plt.xlabel("Re(z)")
    plt.ylabel("Im(z)")
    plt.title(r"Domain Coloring of $\Gamma(z)$")
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=200)

    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot the Euler gamma function in the complex plane."
    )
    parser.add_argument("--re-min", type=float, default=-5.0)
    parser.add_argument("--re-max", type=float, default=5.0)
    parser.add_argument("--im-min", type=float, default=-5.0)
    parser.add_argument("--im-max", type=float, default=5.0)
    parser.add_argument("--resolution", type=int, default=800)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    plot_gamma_complex(
        re_lim=(args.re_min, args.re_max),
        im_lim=(args.im_min, args.im_max),
        resolution=args.resolution,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
