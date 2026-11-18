from osdagbridge.core.reports.report_utils import longtable

def ch7_quantities(input_dict):
    def _v(key):
        return str(input_dict.get(key, "N.A."))

    hdr = (
        r'\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume}'
        r' & \textbf{Quantity} & \textbf{Total Volume}'
        r' & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\'
    )

    body = (
        r'1 & Structural Steel (IS 2062) for Girders & '
        + _v("steel_girders_vol_formula") + r' & '
        + _v("steel_girders_qty") + r' & '
        + _v("steel_girders_vol_total") + r' & '
        + _v("steel_girders_wt_single") + r' & '
        + _v("steel_girders_wt_total") + r' \\' + '\n\\hline\n'
        + r'2(a) & Cross Bracing - Top Chord & '
        + _v("bracing_top_vol_formula") + r' & '
        + _v("bracing_top_qty") + r' & '
        + _v("bracing_top_vol_total") + r' & '
        + _v("bracing_top_wt_single") + r' & '
        + _v("bracing_top_wt_total") + r' \\' + '\n\\hline\n'
        + r'2(b) & Cross Bracing - Bottom Chord & '
        + _v("bracing_bot_vol_formula") + r' & '
        + _v("bracing_bot_qty") + r' & '
        + _v("bracing_bot_vol_total") + r' & '
        + _v("bracing_bot_wt_single") + r' & '
        + _v("bracing_bot_wt_total") + r' \\' + '\n\\hline\n'
        + r'2(c) & Cross Bracing - Diagonal Chord & '
        + _v("bracing_diag_vol_formula") + r' & '
        + _v("bracing_diag_qty") + r' & '
        + _v("bracing_diag_vol_total") + r' & '
        + _v("bracing_diag_wt_single") + r' & '
        + _v("bracing_diag_wt_total") + r' \\' + '\n\\hline\n'
        + r'3 & Concrete (M40) for Deck Slab & '
        + _v("concrete_deck_vol_formula") + r' & '
        + _v("concrete_deck_qty") + r' & '
        + _v("concrete_deck_vol_total") + r' & '
        + _v("concrete_deck_wt_single") + r' & '
        + _v("concrete_deck_wt_total") + r' \\' + '\n\\hline\n'
        + r'4 & Reinforcement Steel (Fe 500) & '
        + _v("rebar_deck_vol_formula") + r' & '
        + _v("rebar_deck_qty") + r' & '
        + _v("rebar_deck_vol_total") + r' & '
        + _v("rebar_deck_wt_single") + r' & '
        + _v("rebar_deck_wt_total") + r' \\' + '\n\\hline\n'
        + r'5 & Shear Stud Connectors & '
        + _v("shear_studs_vol_formula") + r' & '
        + _v("shear_studs_qty") + r' & '
        + _v("shear_studs_vol_total") + r' & '
        + _v("shear_studs_wt_single") + r' & '
        + _v("shear_studs_wt_total") + r' \\' + '\n\\hline\n'
        + r'6 & Crash Barrier & '
        + _v("crash_barrier_vol_formula") + r' & '
        + _v("crash_barrier_qty") + r' & '
        + _v("crash_barrier_vol_total") + r' & '
        + _v("crash_barrier_wt_single") + r' & '
        + _v("crash_barrier_wt_total") + r' \\' + '\n\\hline\n'
    )

    return (
        r'\chapter{Material Take-off \& Quantity Summary}' + '\n'
        r'\label{ch:material-takeoff}' + '\n\n'
        r'\noindent\textbf{Table 7.1  Bill of Materials'
        r' (Steel, Concrete, and Reinforcement Quantities)}' + '\n\n'
        + longtable(
            '|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|',
            'Bill of Materials',
            'tab:ch7:boq',
            hdr,
            body,
            tabcolsep='3.5pt',
        )
    )
