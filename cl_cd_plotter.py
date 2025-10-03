#!/usr/bin/env python3
"""Plot lift and drag coefficients versus angle of attack for multiple Reynolds numbers.

The script is tailored for JavaFoil-style `.dat` files that contain repeated
`ZONE` blocks, each representing a different Reynolds number (e.g.
`ClCdDU91-W2-250.dat`). Each block is expected to provide four numeric columns:

* angle of attack for lift (`AoA1`)
* lift coefficient (`C_L`)
* angle of attack for drag (`AoA2`, duplicated values)
* drag coefficient (`C_D`)

Example usage (from the repository root):

```
python joo.py --data ClCdDU91-W2-250.dat --output plots/cl_cd_vs_aoa.png
```

Lift and drag are visualised on a single set of axes with dual y-axes: $C_\ell$
on the left and $C_d$ on the right. The script saves the figure if `--output`
is provided and shows the plot unless `--no-show` is passed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt


ZONE_RE_PATTERN = re.compile(r"Re=([^ \"(]+)")


def load_cl_cd_data(path: Path) -> Dict[str, Dict[str, List[float]]]:
	"""Parse a JavaFoil-style .dat file into a mapping keyed by Reynolds number.

	Parameters
	----------
	path
		Path to the `.dat` file containing repeated `ZONE` blocks.

	Returns
	-------
	dict
		A dictionary keyed by Reynolds number labels. Each value contains three
		lists: `AoA`, `Cl`, and `Cd`, all aligned.
	"""

	if not path.exists():
		raise FileNotFoundError(f"Data file not found: {path}")

	data: Dict[str, Dict[str, List[float]]] = {}
	current_key: str | None = None

	with path.open("r", encoding="utf-8") as fh:
		for raw_line in fh:
			line = raw_line.strip()
			if not line:
				continue

			upper_line = line.upper()
			if upper_line.startswith("TITLE") or upper_line.startswith("VARIABLES"):
				continue

			if upper_line.startswith("ZONE"):
				match = ZONE_RE_PATTERN.search(line)
				re_label = match.group(1) if match else f"Zone {len(data) + 1}"
				pretty_label = format_reynolds_label(re_label)
				data[pretty_label] = {"AoA": [], "Cl": [], "Cd": []}
				current_key = pretty_label
				continue

			if current_key is None:
				# Skip numeric data until we encounter the first ZONE header.
				continue

			tokens = line.replace(",", " ").split()
			if len(tokens) < 4:
				continue

			try:
				aoa_lift = float(tokens[0])
				cl = float(tokens[1])
				aoa_drag = float(tokens[2])
				cd = float(tokens[3])
			except ValueError as exc:
				raise ValueError(f"Failed to parse numeric data from line: {line}") from exc

			if abs(aoa_lift - aoa_drag) > 1e-6:
				# The file should have matching AoA columns; warn the user otherwise.
				raise ValueError(
					"Mismatched angle-of-attack columns detected. "
					"Ensure the .dat file contains identical AoA values for lift and drag."
				)

			zone_data = data[current_key]
			zone_data["AoA"].append(aoa_lift)
			zone_data["Cl"].append(cl)
			zone_data["Cd"].append(cd)

	if not data:
		raise ValueError(f"No ZONE data found in {path}. Check the file format.")

	return data


def format_reynolds_label(raw_label: str) -> str:
	"""Return a human-readable label for a Reynolds number string.

	Examples
	--------
	>>> format_reynolds_label("5E5")
	'Re = 5×10^5'
	>>> format_reynolds_label("750000")
	'Re = 7.5×10^5'
	"""

	label = raw_label.strip()
	if not label:
		return "Re = unknown"

	sci_match = re.fullmatch(r"([0-9]*\.?[0-9]+)[eE]([+-]?\d+)", label)
	if sci_match:
		base_str, exp_str = sci_match.groups()
		base = float(base_str)
		exponent = int(exp_str)
		if base.is_integer():
			base_text = str(int(base))
		else:
			base_text = f"{base:g}"
		return f"Re = {base_text}×10^{exponent}"

	try:
		value = float(label)
	except ValueError:
		return f"Re = {label}"

	exponent = 0
	while value >= 10:
		value /= 10
		exponent += 1
	while 0 < value < 1:
		value *= 10
		exponent -= 1

	if exponent == 0:
		return f"Re = {value:g}"

	value_text = f"{value:g}"
	return f"Re = {value_text}×10^{exponent}"


def sort_zone_series(zone_data: Dict[str, List[float]]) -> Tuple[List[float], List[float], List[float]]:
	"""Return angle of attack, Cl, and Cd sorted by angle of attack."""

	combined = list(zip(zone_data["AoA"], zone_data["Cl"], zone_data["Cd"]))
	combined.sort(key=lambda row: row[0])
	aoa, cl, cd = zip(*combined)
	return list(aoa), list(cl), list(cd)


def plot_cl_cd(
	data: Dict[str, Dict[str, List[float]]],
	*,
	output: Path | None = None,
	show: bool = True,
	dpi: int = 150,
) -> None:
	"""Create the Cl and Cd vs. AoA plot with dual y-axes, optionally saving to disk."""

	if not data:
		raise ValueError("No data provided to plot.")

	fig, ax_cl = plt.subplots(figsize=(9, 6))
	ax_cd = ax_cl.twinx()

	colors = plt.cm.viridis_r
	zones = list(data.items())
	color_values = [i / max(len(zones) - 1, 1) for i in range(len(zones))]

	cl_handles: List = []
	cd_handles: List = []

	for color_value, (reynolds, zone) in zip(color_values, zones):
		color = colors(color_value)
		aoa, cl, cd = sort_zone_series(zone)

		(cl_line,) = ax_cl.plot(
			aoa,
			cl,
			marker="o",
			linewidth=2,
			markersize=4,
			color=color,
			label=reynolds,
		)
		(cd_line,) = ax_cd.plot(
			aoa,
			cd,
			marker="s",
			linewidth=2,
			markersize=4,
			linestyle="--",
			color=color,
			label=reynolds,
		)

		cl_handles.append(cl_line)
		cd_handles.append(cd_line)

	ax_cl.set_xlabel("Angle of attack (degrees)")
	ax_cl.set_ylabel("Lift coefficient, $C_\ell$")
	ax_cd.set_ylabel("Drag coefficient, $C_d$")

	ax_cl.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)

	ax_cl.legend(
		cl_handles,
		[handle.get_label() for handle in cl_handles],
		title="$C_\ell$ (left axis)",
		loc="upper left",
	)
	ax_cd.legend(
		cd_handles,
		[handle.get_label() for handle in cd_handles],
		title="$C_d$ (right axis)",
		loc="lower right",
	)

	fig.suptitle("DU91-W2-250 Airfoil Polars")
	fig.tight_layout(rect=(0, 0, 1, 0.97))

	if output is not None:
		output.parent.mkdir(parents=True, exist_ok=True)
		fig.savefig(output, dpi=dpi, bbox_inches="tight")

	if show:
		plt.show()
	else:
		plt.close(fig)


def parse_args(args: Iterable[str] | None = None) -> argparse.Namespace:
	"""CLI argument parser."""

	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--data",
		type=Path,
		default=Path("ClCdDU91-W2-250.dat"),
		help="Path to the .dat file with Cl and Cd data (default: ClCdDU91-W2-250.dat).",
	)
	parser.add_argument(
		"--output",
		type=Path,
		help="Optional path for saving the generated figure (PNG, PDF, etc.).",
	)
	parser.add_argument(
		"--no-show",
		action="store_true",
		help="Skip displaying the figure window (useful in headless environments).",
	)
	parser.add_argument(
		"--dpi",
		type=int,
		default=150,
		help="Image resolution in dots per inch when saving (default: 150).",
	)
	return parser.parse_args(args=args)


def main() -> None:
	"""CLI entry point."""

	args = parse_args()
	data = load_cl_cd_data(args.data)
	plot_cl_cd(data, output=args.output, show=not args.no_show, dpi=args.dpi)


if __name__ == "__main__":
	main()
