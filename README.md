# DU91-W2-250 Polar Plotter

This repository contains a small utility for visualising lift and drag polars for
the DU91-W2-250 airfoil based on JavaFoil output (`ClCdDU91-W2-250.dat`).

## Quick start

```bash
python joo.py --data ClCdDU91-W2-250.dat --output plots/cl_cd_vs_aoa.png
```

The command reads the provided `.dat` file, creates a single plot with dual
y-axes—$C_\ell$ on the left and $C_d$ on the right—plotted against angle of
attack for each Reynolds number block, saves the figure, and opens an interactive
window. To suppress the window (for headless environments), add `--no-show`.

## Command-line options

- `--data PATH` &mdash; input `.dat` file (defaults to `ClCdDU91-W2-250.dat`).
- `--output PATH` &mdash; save the generated figure (PNG, PDF, etc.).
- `--no-show` &mdash; skip displaying the window.
- `--dpi INT` &mdash; adjust image resolution when saving (default: 150).

## Dependencies

Install the required Python packages with:

```bash
pip install -r requirements.txt
```

## Data notes

The parser expects the JavaFoil-style format: each `ZONE` block corresponds to a
Reynolds number and contains four columns (AoA, C<sub>L</sub>, AoA, C<sub>D</sub>). The
script validates that the AoA columns match and will raise an error otherwise.
