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
    - End Diaphragms (Moment and Shear as in the summary table, or a note)

    Returns True if the chart was successfully generated and written.
    """
    try:
        summary = bridge.utilization_summary()
        fig = Figure(figsize=(float(CHART.get("width_in", 6.3)), 5.2), dpi=float(CHART.get("dpi", 200)))
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
                        transform=ax.transAxes, color=CHART["muted_color"], fontstyle="italic", fontsize=8.5)
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
                    c = CHART["label_color"]
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
            ax_ed.text(0.5, 0.5, msg, ha="center", va="center",
                       transform=ax_ed.transAxes, color=CHART["muted_color"], fontstyle="italic", fontsize=8.5)
            ax_ed.set_xticks([])
            ax_ed.set_yticks([])
            ax_ed.spines["top"].set_visible(False)
            ax_ed.spines["right"].set_visible(False)

        fig.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
        canvas.print_figure(output_png_path, dpi=float(CHART.get("dpi", 200)))
        return os.path.exists(output_png_path)
    except Exception as exc:
        logger.warning("Failed to generate UR summary chart: %s", exc)
        return False


def generate_quantity_chart(inputs_or_quantities: dict, output_png_path: str) -> bool:
    """
    Generate material quantity bar charts for Chapter 7:
    - Structural steel tonnage (Plate Girders, Cross Bracing, End Diaphragms) in MT
    - Concrete volume (Deck Slab) in m³
    - Reinforcement steel weight (Deck Slab Rebar) in MT
    Uses Figure and FigureCanvasAgg directly without pyplot.
    Returns True if the chart was successfully generated and written.
    """
    try:
        numeric = inputs_or_quantities.get("numeric_quantities", {})
        if not numeric:
            def _parse_num(k):
                v = inputs_or_quantities.get(k)
                if v in (None, "N.A.", "", "---"):
                    return 0.0
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return 0.0

            g_t = _parse_num("steel_girders_wt_total")
            cb_t = (
                _parse_num("bracing_top_wt_total")
                + _parse_num("bracing_bot_wt_total")
                + _parse_num("bracing_diag_wt_total")
            )
            ed_t = _parse_num("steel_ed_wt_total")
            c_m3 = _parse_num("concrete_deck_vol_total")
            r_t = _parse_num("rebar_deck_wt_total")
        else:
            g_t = float(numeric.get("girders_tonnes", 0.0) or 0.0)
            cb_t = float(numeric.get("bracing_tonnes", 0.0) or 0.0)
            ed_t = float(numeric.get("ed_tonnes", 0.0) or 0.0)
            c_m3 = float(numeric.get("concrete_m3", 0.0) or 0.0)
            r_t = float(numeric.get("rebar_tonnes", 0.0) or 0.0)

        fig = Figure(figsize=(float(CHART.get("width_in", 6.3)), 4.2), dpi=float(CHART.get("dpi", 200)))
        canvas = FigureCanvasAgg(fig)
        gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0])

        ax_steel = fig.add_subplot(gs[0, :])
        ax_conc = fig.add_subplot(gs[1, 0])
        ax_rebar = fig.add_subplot(gs[1, 1])

        grid_col = CHART.get("grid", "#E3E3E3")

        # 1. Structural Steel Tonnage
        steel_labels = ["Plate Girders", "Cross Bracing", "End Diaphragms"]
        steel_vals = [g_t, cb_t, ed_t]
        steel_color = CHART["steel_color"]
        bars = ax_steel.bar(steel_labels, steel_vals, color=steel_color, width=0.45, zorder=2)
        ax_steel.set_title("Structural Steel Tonnage by Component (MT)", fontsize=9.5, fontweight="bold")
        ax_steel.set_ylabel("Weight (MT)", fontsize=8)
        max_s = max(steel_vals) if steel_vals else 0.0
        ax_steel.set_ylim(0, max_s * 1.25 if max_s > 0 else 10.0)
        for b in bars:
            h = b.get_height()
            lbl = f"{h:.2f} MT" if h > 0 else "N.A."
            ax_steel.annotate(lbl, (b.get_x() + b.get_width() / 2, max(h, 0)),
                              ha="center", va="bottom", fontsize=8, color=CHART["label_color"])

        # 2. Concrete Volume
        bars_c = ax_conc.bar(["Deck Slab"], [c_m3], color=CHART["concrete_color"], width=0.35, zorder=2)
        ax_conc.set_title("Concrete Volume (m³)", fontsize=9.5, fontweight="bold")
        ax_conc.set_ylabel("Volume (m³)", fontsize=8)
        ax_conc.set_ylim(0, c_m3 * 1.25 if c_m3 > 0 else 10.0)
        for b in bars_c:
            h = b.get_height()
            lbl = f"{h:.2f} m³" if h > 0 else "N.A."
            ax_conc.annotate(lbl, (b.get_x() + b.get_width() / 2, max(h, 0)),
                             ha="center", va="bottom", fontsize=8, color=CHART["label_color"])

        # 3. Reinforcement Steel
        bars_r = ax_rebar.bar(["Deck Slab Rebar"], [r_t], color=CHART["rebar_color"], width=0.35, zorder=2)
        ax_rebar.set_title("Reinforcement Steel (MT)", fontsize=9.5, fontweight="bold")
        ax_rebar.set_ylabel("Weight (MT)", fontsize=8)
        ax_rebar.set_ylim(0, r_t * 1.25 if r_t > 0 else 5.0)
        for b in bars_r:
            h = b.get_height()
            lbl = f"{h:.2f} MT" if h > 0 else "N.A."
            ax_rebar.annotate(lbl, (b.get_x() + b.get_width() / 2, max(h, 0)),
                              ha="center", va="bottom", fontsize=8, color=CHART["label_color"])

        for a in [ax_steel, ax_conc, ax_rebar]:
            a.spines["top"].set_visible(False)
            a.spines["right"].set_visible(False)
            a.grid(axis="y", linestyle=":", color=grid_col, alpha=0.7)
            a.set_axisbelow(True)
            a.tick_params(axis="x", labelsize=8)
            a.tick_params(axis="y", labelsize=7.5)

        fig.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
        canvas.print_figure(output_png_path, dpi=float(CHART.get("dpi", 200)))
        return os.path.exists(output_png_path)
    except Exception as exc:
        logger.warning("Failed to generate quantity summary chart: %s", exc)
        return False
