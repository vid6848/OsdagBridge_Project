from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed, longtable
from osdagbridge.core.reports.styles import TABLE_SPECS, ROW_END, VSPACE_SEC, status

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    def _merged_row(lc, bm_d, rxn_d):
        bm_d  = bm_d  or {}
        rxn_d = rxn_d or {}
        return (
            _tex(lc)                              + r" & "
            + _fmt(bm_d.get('max_bm'))           + r" & "
            + _tex(bm_d.get('bm_girder', '---')) + r" & "
            + _fmt(bm_d.get('bm_location'))      + r" & "
            + _fmt(bm_d.get('max_sf'))           + r" & "
            + _tex(bm_d.get('sf_girder', '---')) + r" & "
            + _fmt(bm_d.get('sf_location'))      + r" & "
            + _fmt(rxn_d.get('left_kN'))         + r" & "
            + _fmt(rxn_d.get('right_kN'))        + r" " + ROW_END
        )

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    merged_body = ("\n\\hline\n").join(
        _merged_row(lc, lc_summary.get(lc), rxn_summary.get(lc))
        for lc in all_lcs
    ) if all_lcs else r"--- & --- & --- & --- & --- & --- & --- & --- & --- " + ROW_END

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status     = (status(_live_mm <= _allow_live_mm) if _live_mm <= _allow_live_mm else status(False)) if _live_mm is not None else "---"
    _total_status    = (status(_total_mm <= _allow_total_mm) if _total_mm <= _allow_total_mm else status(False)) if _total_mm is not None else "---"

    # The Summary of Maximum Demands table has a complex 2-row spanning header;
    # keep it hand-built so the multirow structure is preserved exactly.
    _demands_hdr = (
        r'\multirow{2}{*}{\makecell{\textbf{Load}\\\textbf{Case/}\\\textbf{Comb.}}}'
        + r' & \multicolumn{3}{c|}{\textbf{Bending Moment}}'
        + r' & \multicolumn{3}{c|}{\textbf{Shear Force}}'
        + r' & \multicolumn{2}{c|}{\textbf{Reaction at Supports}}\\'
        + '\n\\cline{2-9}\n\n'
        + r' & \makecell{\textbf{Max}\\\textbf{(kNm)}}'
        + r' & \textbf{Girder}'
        + r' & \makecell{\textbf{Loc.}\\\textbf{(m)}}'
        + r' & \makecell{\textbf{Max}\\\textbf{(kN)}}'
        + r' & \textbf{Girder}'
        + r' & \makecell{\textbf{Loc.}\\\textbf{(m)}}'
        + r' & \makecell{\textbf{Left}}'
        + r' & \makecell{\textbf{Right }}\\'
    )

    # Reactions table body — empty placeholder rows kept from original
    rxn_hdr  = r'\textbf{Load Case} & \textbf{Left Support (kN)} & \textbf{Right Support (kN)} ' + ROW_END
    rxn_body = (
        r' & ' + '' + r' & ' + '' + r' ' + ROW_END + '\n\\hline\n'
        + r' & ' + '' + r' & ' + '' + r' ' + ROW_END + '\n\\hline\n'
        + r' & ' + '' + r' & ' + '' + r' ' + ROW_END + '\n\\hline\n'
    )

    # Deflection table body
    defl_hdr  = r'\textbf{parameter} & \textbf{value} \\'
    defl_body = (
        r'\textnormal{Deflection due to Live Load, $\delta_{LL}$} & '
        + _live_str + r' ' + ROW_END + '\n\\hline\n'
        + r'\textnormal{Allowable Live Load Deflection ($\Delta_{allow}$)} & '
        + _allow_live_str + r' ' + ROW_END + '\n\\hline\n'
        + r'\textnormal{Live Load Deflection Check Status} & '
        + _live_status + r' ' + ROW_END + '\n\\hline\n'
        + r'\textnormal{Deflection due to Total Load, $\delta_{total}$} & '
        + _total_str + r' ' + ROW_END + '\n\\hline\n'
        + r'\textnormal{Allowable Total Deflection ($\Delta_{allow}$)} & '
        + _allow_total_str + r' ' + ROW_END + '\n\\hline\n'
        + r'\textnormal{Total Load Deflection Check Status} & '
        + _total_status + r' ' + ROW_END + '\n\\hline\n'
    )

    return (
        r'\chapter{Analysis Results}' + '\n\n'
        r'A grillage model was used for structural analysis. The deck is idealized as a grid'
        r' of elastic beam elements --- longitudinal members represent the composite steel'
        r' girders with effective slab, and transverse members represent the slab or cross'
        r' frames. This section summarizes the critical output from that analysis.'
        + '\n\n'
        + VSPACE_SEC + '\n'
        r"""\begingroup
\osDenseTable{}

"""
        + longtable(
            TABLE_SPECS['ch4_demands'],
            'Summary of Maximum Demands',
            'tab:ch4:demands',
            _demands_hdr,
            merged_body + '\n\n\\hline\n',
        )
        + r'\endgroup' + '\n\n'
        + VSPACE_SEC + '\n'
        + longtable(
            TABLE_SPECS['ch4_reactions'],
            'Reactions at Supports',
            'tab:ch4:reactions',
            rxn_hdr,
            rxn_body,
        )
        + '\n' + VSPACE_SEC + '\n'
        + longtable(
            TABLE_SPECS['ch4_deflection'],
            'Deflection Summary (Live Load \\& Total Load)',
            'tab:ch4:deflection',
            defl_hdr,
            defl_body,
        )
        + '\n' + VSPACE_SEC + '\n'
        + r'\noindent' + '\n'
        + _fig_embed(fig_paths.get('bm_envelope'),
                     'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).',
                     width=r'0.75\textwidth')
        + '\n'
        + _fig_embed(fig_paths.get('sf_envelope'),
                     'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).',
                     width=r'0.75\textwidth')
        + '\n'
        + _fig_embed(fig_paths.get('defl_ll'),
                     r'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.',
                     width=r'0.75\textwidth')
        + '\n'
    )
