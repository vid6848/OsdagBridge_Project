# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import (
    NOT_STORED, _fig_or_placeholder, _render_value, _tex,
    get_girder_entries, girder_dims_mm, not_stored_note)
from osdagbridge.core.reports.styles import (
    TABLE_SPECS, TITLE, VSPACE_SEC, VSPACE_TABLE_LG, VSPACE_TABLE_SM, chapter_format, colspec)
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_OK,
    KEY_DD_SHEAR_OK,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPC_BOT,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


def _max_float(values):
    """Return the largest value coercible to float, or None if there are none."""
    out = None
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if out is None or f > out:
            out = f
    return out


def _max_member_efficiency(pair_designs):
    """Maximum Osdag 'efficiency' (utilization ratio) over a cross-bracing or
    end-diaphragm result dump (nested pair -> member -> force_type -> raw).
    Reads already-computed results only; nothing is recalculated here."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    if not isinstance(pair_designs, dict):
        return None
    best = None
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for force_types in members.values():
            if not isinstance(force_types, dict):
                continue
            for raw in force_types.values():
                try:
                    val = _extract_osdag_summary(raw or {}).get("efficiency")
                    if val is None:
                        continue
                    f = float(val)
                except (TypeError, ValueError, AttributeError):
                    continue
                if best is None or f > best:
                    best = f
    return best


def _girder_outcome(input_dict, output_dict, failing, has_results):
    if failing:
        return "fail"
    if not has_results:
        return "not available"
    # the deflection table has its own pass/fail result
    try:
        span_mm = float(input_dict.get(KEY_SPAN)) * 1000.0
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS))
    except (TypeError, ValueError):
        return "not available"
    for key, limit in ((KEY_SD_DEFL_LIVE, span_mm / 800.0), (KEY_SD_DEFL_TOTAL, span_mm / 600.0)):
        worst = _max_float([output_dict.get(f"{key}.G{i}") for i in range(1, n + 1)])
        if worst is not None and worst > limit:
            return "fail"
    return "pass"


def _deck_outcome(output_dict):
    values = output_dict.get("deck_report_values") or {}
    if not values:
        return "not available"

    def num(key):
        try:
            return float(values.get(key) or 0)
        except (TypeError, ValueError):
            return 0.0

    results = output_dict.get("deck_design_results") or {}
    worst = _max_float([v for k, v in results.items() if str(k).startswith("ur_")])
    if worst is not None and worst > 1.0:
        return "fail"
    if (output_dict.get("design_results") or {}).get("transverse_shear_ok") is False:
        return "fail"
    # same comparisons as the deck tables in Chapter 5
    as_bot, as_min = num(KEY_DD_AS_BOT), num(KEY_DD_AS_MIN)
    crack = [num(KEY_DD_WK_BOT), num(KEY_DD_WK_TOP)]
    checks = [
        values.get(KEY_DD_PUNCH_OK),
        values.get(KEY_DD_SHEAR_OK),
        values.get(KEY_DD_COVER_OK),
        num(KEY_DD_MU_BOT) >= num(KEY_DD_M_ULS_SAG),
        num(KEY_DD_MU_TOP) >= num(KEY_DD_M_ULS_HOG),
        as_bot >= num(KEY_DD_AS_REQ_BOT),
        as_bot >= as_min,
        num(KEY_DD_AS_TOP) >= num(KEY_DD_AS_REQ_TOP),
        num(KEY_DD_AS_LONG) >= max(0.20 * as_bot, as_min),
        0 < num(KEY_DD_SPC_BOT) <= num(KEY_DD_SPACING_MAX),
    ]
    if values.get(KEY_DD_HAS_OVERHANG):
        checks.append(num(KEY_DD_MU_OH) >= num(KEY_DD_M_ULS_OH))
        crack.append(num(KEY_DD_WK_OH))
    checks.append(max(crack) <= num(KEY_DD_WK_LIMIT))
    return "pass" if all(checks) else "fail"


def _bracing_outcome(bridge):
    if bridge is None or not bridge.get_cb_pairs():
        return "not available"
    for ftype in ("compression", "tension"):
        worst = bridge.get_cb_worst(ftype)
        if worst and worst[0] > 1.0:
            return "fail"
    top_chord = bridge.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
    if not any(bridge.get_cb_worst(t) for t in ("compression", "tension")):
        return "not available"
    missing = False
    for pair in bridge.get_cb_pairs():
        for member in ("diagonal", "chord"):
            for ftype in ("compression", "tension"):
                if (bridge.get_cb_force(pair, member, ftype)
                        and not bridge.get_cb_efficiency(pair, member, ftype)):
                    missing = True
            limit = 250 if (member == "diagonal" or top_chord) else 400
            slenderness = _max_float([bridge.get_cb_slenderness(pair, member)])
            if slenderness is not None and slenderness > limit:
                return "fail"
    return "not available" if missing else "pass"


def _diaphragm_outcome(bridge, bracing):
    if bridge is None or not bridge.get_ed_type():
        return "not available"
    if not bridge.ed_is_bracing():
        return "not designed in this version"
    source = bridge.get_ed_source()
    if source is not bridge:
        return _bracing_outcome(source)
    if bracing != "not available":
        return bracing + " (taken from the cross bracing checks)"
    return bracing


def executive_summary(input_dict, output_dict, fig_paths, bridge=None) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # Each girder gets its own section, governing check and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    # ── Pull the stored result dicts once, then work off these locals ─────────
    # (no value is recomputed here — the pipeline already filled these in).
    design_results = output_dict.get("design_results", {}) or {}
    all_lines      = design_results.get("per_girder", {}) or {}
    per_girder     = bridge.get_girder_results() if bridge else []
    deck_results   = output_dict.get("deck_design_results", {}) or {}
    cb_results     = output_dict.get("crossbracing_design_results", {}) or {}
    ed_results     = output_dict.get("end_diaphragm_design_results", {}) or {}

    # Overall Design Status — girder checks only: Pass if every check passes,
    # otherwise Fail with the names of the failing checks. Each check carries a
    # pre-computed {name, dcr, status}.
    failing = []                        # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    for gd in per_girder:                # the bridge's own girders only
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                if _val is None:
                    dcr = None
                else:
                    dcr = float(_val)
            except (TypeError, ValueError):
                dcr = None
            name = str(chk.get("name", "")).strip()
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if is_fail and name and name not in failing:
                failing.append(name)
            if dcr is not None:
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name
                if girder_max_ur is None or dcr > girder_max_ur:
                    girder_max_ur = dcr

    if all_lines and not per_girder:
        overall_design_status = "Not available (no valid per-girder results from the analysis)"
    elif not per_girder:
        overall_design_status = ""
    elif failing:
        overall_design_status = "Fail (" + ", ".join(failing) + ")"
    else:
        overall_design_status = "Pass"

    # Overall Utilization Ratio — the maximum UR across all bridge components,
    # tagged with the governing component (e.g. "1.05 (Deck slab)").
    component_urs = []                  # (ur_value, component_label)
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    deck_max = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if deck_max is not None:
        component_urs.append((deck_max, "Deck slab"))
    for results, label in ((cb_results, "Cross bracing"), (ed_results, "End diaphragm")):
        m = _max_member_efficiency(results)
        if m is not None:
            component_urs.append((m, label))
    if component_urs and not (all_lines and not per_girder):
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = ""

    girder_result = _girder_outcome(input_dict, output_dict, failing, bool(per_girder))
    deck_result = _deck_outcome(output_dict)
    cb_result = _bracing_outcome(bridge)
    ed_result = _diaphragm_outcome(bridge, cb_result)

    status_text = _tex(overall_design_status) or NOT_STORED
    gov = _tex(gov_name) if gov_name not in (None, '', 'None') else NOT_STORED
    ur = _tex(overall_utilization_ratio) if overall_utilization_ratio else NOT_STORED

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    # Column widths: row-label column gets 20% width; girder columns share remainder
    frac_per_girder = round(0.80 / n_cols, 3)
    col_spec = colspec(('C', 0.20), *[('C', frac_per_girder)] * n_cols)

    # Header row
    hdr_cells = ' &\n  '.join([r'\textbf{' + _tex(lbl) + '}' for lbl, _ in labels])
    header_row = r'  \textbf{} &' + '\n  ' + hdr_cells + r' \\' + '\n'

    # Member ID row
    mid_cells = ' & '.join([_tex(mid) for _, mid in labels])
    member_id_row = 'Member ID & ' + mid_cells + r' \\' + '\n'

    # Section / Governing Check / UR rows
    sec_list, gov_list, ur_list = [], [], []
    for i in range(1, n_cols + 1):
        dims = girder_dims_mm(input_dict, i) if design_results else None
        if dims:
            d, _tw, bft, tft, bfb, tfb = dims
            sec_list.append(f"{d:.0f} x {bft:.0f} x {tft:.0f} x {bfb:.0f} x {tfb:.0f}")
        else:
            sec_list.append(sec)
        ctrl = bridge.get_controlling_check(i) if bridge else {}
        gov_list.append(_tex(ctrl.get("name", "")) or NOT_STORED)
        ur_list.append(f"{ctrl['dcr']:.2f} (Girder)" if ctrl.get("dcr") is not None else NOT_STORED)
    sec_cells = ' & '.join(sec_list)
    sections = f"Section Designation & {sec_cells} \\\\"
    gov_cells = ' & '.join(gov_list)
    gov_checks = f"Governing Check & {gov_cells} \\\\"
    ur_cells = ' & '.join(ur_list)
    urs = f"Utilization Ratio & {ur_cells} \\\\"

    table1 = ('\\Needspace*{16\\baselineskip}\n'
              r'\noindent\textbf{Table 1 -- Final Bridge Geometry (after optimization)}' + '\n\n'
              + VSPACE_TABLE_SM + '\n'
              + (r'\begingroup\osDenseTable{}' + '\n' if n_cols > 5 else '')
              + r'\noindent' + '\n'
              r'\begin{tabular}{' + col_spec + '}\n'
              r'\hline' + '\n'
              + header_row +
              r'\hline' + '\n'
              + member_id_row +
              r'\hline' + '\n'
              + sections + '\n'
              r'\hline' + '\n'
              + gov_checks + '\n'
              r'\hline' + '\n'
              + urs + '\n'
              r'\hline' + '\n'
              r'\end{tabular}\par' + '\n'
              + (r'\endgroup' + '\n' if n_cols > 5 else '')
              + not_stored_note(sec_cells + gov_cells + ur_cells))

    return r"""
\newpage
{\centering""" + TITLE['heading'] + r""" Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
""" + VSPACE_TABLE_LG + r"""

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}


\begin{tabular}{""" + TABLE_SPECS['two_col_wide_val'] + r"""}
\hline
\textbf{Bridge Type} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\textbf{Span} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textbf{Carriageway Width} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING)) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS)) + r""" \\
\hline
\textbf{Overall Design Status} & """ + status_text + r""" \\
\hline
\textbf{Governing Check} & """ + gov + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + ur + r""" \\
\hline
\end{tabular}
""" + not_stored_note(status_text + gov + ur + ''.join(
        _render_value(input_dict, key) for key in (KEY_STRUCTURE_TYPE, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH,
                                                   KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS))) + r"""


""" + plan_fig + r"""

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

""" + VSPACE_TABLE_SM + r"""
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check.}

""" + VSPACE_SEC + r"""

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\noindent Girder design """ + girder_result + r""" \\
Cross bracing design """ + cb_result + r""" \\
End Diaphragm design """ + ed_result + r""" \\
Deck design """ + deck_result + r"""

\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:assumptions}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

% Restore numbered chapter format
""" + chapter_format(TITLE['chapter_top_main']) + r"""
"""
