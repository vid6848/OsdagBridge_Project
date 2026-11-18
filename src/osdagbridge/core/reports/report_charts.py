"""
Chart generation for OsdagBridge reports.
Uses Figure and FigureCanvasAgg directly without pyplot for thread-safety.
"""

import os
import logging
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from osdagbridge.core.reports.styles import CHART

logger = logging.getLogger(__name__)


def generate_ur_chart(bridge, output_png_path: str) -> bool:
    """
    Generate a 4-panel utilization ratio (UR) bar chart:
    - Plate Girders (max DCR per girder)
    - Deck Slab (flexure, punching, shear, crack width)
    - Cross Bracing (max UR per girder pair)
    - End Diaphragms (UR per pair or 'Not designed in this version' note)

    Returns True if the chart was successfully generated and written.
    """
    try:
        summary = bridge.utilization_summary()
        fig = Figure(figsize=(CHART.get("width_in", 6.3), 5.2), dpi=CHART.get("dpi", 200))
        canvas = FigureCanvasAgg(fig)
        axes = fig.subplots(2, 2)

        pass_col = CHART.get("pass_color", "#91B014")
        fail_col = CHART.get("fail_color", "#C62828")
        thresh_col = CHART.get("threshold_color", "red")
        thresh_ls = CHART.get("threshold_style", "--")
        grid_col = CHART.get("grid", "#E3E3E3")

        def _plot_panel(ax, title, items, ylabel=True):
            ax.set_title(title, fontsize=10, fontweight="bold")
            if not items:
                ax.text(0.5, 0.5, "No design results", ha="center", va="center",
                        transform=ax.transAxes, color="#777777", fontstyle="italic", fontsize=8.5)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                return

            labels = [it[0] for it in items]
            urs = [it[1] for it in items]
            colors = [fail_col if u > 1.0 else pass_col for u in urs]

            bars = ax.bar(labels, urs, color=colors, width=0.55, zorder=2)
            ax.axhline(1.0, color=thresh_col, linestyle=thresh_ls, linewidth=1.0, zorder=3)

            if ylabel:
                ax.set_ylabel("UR", fontsize=9)

            max_val = max(urs) if urs else 1.0
            ax.set_ylim(0, max(1.2, max_val * 1.15))
            ax.grid(axis="y", linestyle=":", color=grid_col, alpha=0.7)
            ax.set_axisbelow(True)

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            # Bar labels
            for bar, u in zip(bars, urs):
                if u > 1.0:
                    lbl = f"{u:.2f}\nFAIL"
                    c = fail_col
                    fw = "bold"
                else:
                    lbl = f"{u:.2f}"
                    c = "#333333"
                    fw = "normal"
                ax.annotate(lbl, (bar.get_x() + bar.get_width() / 2, u),
                            ha="center", va="bottom", fontsize=7.5, color=c, fontweight=fw)

            if len(labels) > 4:
                ax.tick_params(axis="x", rotation=20, labelsize=8)
            else:
                ax.tick_params(axis="x", labelsize=8.5)

        # 1. Girders
        _plot_panel(axes[0, 0], "Plate Girders", summary.get("girders", []), ylabel=True)

        # 2. Deck Slab
        _plot_panel(axes[0, 1], "Deck Slab", summary.get("deck", []), ylabel=False)

        # 3. Cross Bracing
        _plot_panel(axes[1, 0], "Cross Bracing", summary.get("cross_bracing", []), ylabel=True)

        # 4. End Diaphragms
        ed_info = summary.get("end_diaphragm", {})
        ax_ed = axes[1, 1]
        ax_ed.set_title("End Diaphragms", fontsize=10, fontweight="bold")
        if ed_info.get("designed") and ed_info.get("items"):
            _plot_panel(ax_ed, "End Diaphragms", ed_info.get("items", []), ylabel=False)
        else:
            msg = ed_info.get("message") or "Not designed in this version"
            ax_ed.text(0.5, 0.5, f"{msg}\n(Rolled / Welded section)", ha="center", va="center",
                       transform=ax_ed.transAxes, color="#777777", fontstyle="italic", fontsize=8.5)
            ax_ed.set_xticks([])
            ax_ed.set_yticks([])
            ax_ed.spines["top"].set_visible(False)
            ax_ed.spines["right"].set_visible(False)

        fig.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
        canvas.print_figure(output_png_path, dpi=CHART.get("dpi", 200))
        return os.path.exists(output_png_path)
    except Exception as exc:
        logger.warning("Failed to generate UR summary chart: %s", exc)
        return False
