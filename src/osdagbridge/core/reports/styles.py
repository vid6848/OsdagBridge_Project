"""Formatting values for the design report, kept in one place."""
from osdagbridge.core.reports.report_utils import _tex


PAGE = dict(
    doc_class="report",
    paper="a4paper",
    top="25mm",
    bottom="22mm",
    left="22mm",
    right="22mm",
    headheight="18pt",
    headsep="8mm",
    footskip="12mm",
    includeheadfoot=True,
)

FONT = dict(
    size="12pt",
    linespread=1.15,
    emergency_stretch="3em",   # lets a long line wrap instead of leaving the margin
    caption_label="bf",
)

COLORS = dict(
    brand="91B014",
    pass_="2E7D32",
    fail="C62828",
    warn="E65100",
    info="0277BD",
    sd_note="black",           # "* Software default value" note
    todo_bg="yellow",
)

TABLE = dict(
    tabcolsep="6pt",
    arraystretch=1.15,
    row_gap="0pt",            # no extra gap, so two girder blocks fit on a page
    row_gap_lg="2pt",
    row_gap_sm="12pt",        # between stacked formulas
    lt_left=r"\fill",
    lt_right=r"\fill",
    lt_pre="0pt",
    lt_post="6pt",
    rule_width="0.5pt",
    extrarowheight="0.6pt",
    needspace_lines=8,
    tabcolsep_dense="3pt",
    tabcolsep_compact="3.5pt",
    tabcolsep_narrow="4pt",
    arraystretch_dense=1.25,
)

SPACING = dict(
    title_gap="2cm",
    title_top="1.5cm",
    title_sub="0.3cm",
    title_block="1cm",
    logo_height="2.2cm",
    table_space="0.4cm",
    table_space_lg="0.8cm",
    table_space_sm="0.2cm",
    section_gap="0.5cm",
    small_gap="4pt",
    mini_gap="2pt",
    fig_pre="-0.5em",
    fig_post="0.5em",
)

# height limits for figures, so they can share a page
FIGURE = dict(
    wide_width=r"0.85\textwidth",
    chart_width=r"0.95\textwidth",
    max_height=r"0.34\textheight",
    plot_height=r"0.29\textheight",
    section_height=r"0.12\textheight",
)

TITLE = dict(
    product=r"\Huge",
    subtitle=r"\large",
    report=r"\Large",
    heading=r"\Large\bfseries",
    chapter_gap="1em",
    chapter_top="0pt",
    chapter_top_main="-30pt",
    chapter_after="10pt",
)

# contents entries: indent and width of the number
TOC = dict(
    chapter=("1.5em", "1.5em"),
    section=("3.8em", "2.3em"),
    subsection=("7.0em", "3.2em"),
)

HEADER_FOOTER = dict(
    left=r"{project} $|$ {job}",
    right=r"{date} $|$ {rev}",
    foot_left=r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay",
    foot_right=r"Page \thepage\ of \pageref{LastPage}",
    rule="1pt",
    headrule_gap="2pt",
    footrule_gap="4pt",
    sd_note=r"* Software default value",
    sd_note_gap="2pt",
)

CHART = dict(
    width_in=6.3,
    dpi=200,
    bar_width=0.55,
    bar_width_steel=0.45,
    bar_width_single=0.35,
    threshold_color="red",
    threshold_style="--",
    pass_color="#91B014",
    fail_color="#C62828",
    grid="#E3E3E3",
    steel_color="#336699",
    concrete_color="#7A8B99",
    rebar_color="#D97724",
    label_color="#333333",
    muted_color="#777777",
)

# short names for the LaTeX macros
ROW_END = r"\osRowEnd{}"
ROW_END_LG = r"\osRowEndLg{}"
ROW_END_SM = r"\osRowEndSm{}"
ROW_KEEP = r"\osRowKeep{}"
ROW_KEEP_LG = r"\osRowKeepLg{}"
ROW_KEEP_SM = r"\osRowKeepSm{}"

VSPACE_TABLE = r"\osTableSpace{}"
VSPACE_TABLE_LG = r"\osTableSpaceLg{}"
VSPACE_TABLE_SM = r"\osTableSpaceSm{}"
VSPACE_SEC = r"\osSectionSpace{}"
VSPACE_SMALL = r"\osSmallSpace{}"
VSPACE_MINI = r"\osMiniSpace{}"
VSPACE_TITLE_TOP = r"\osTitleTopSpace{}"


def status(ok, text=None):
    """PASS or FAIL in the report colours."""
    if ok:
        return r"\osPass{}" if text is None else rf"\osPassText{{{text}}}"
    return r"\osFail{}" if text is None else rf"\osFailText{{{text}}}"


def chapter_format(top):
    """Chapter heading style, with the space above it."""
    return (r"\titleformat{\chapter}[block]{\normalfont" + TITLE["heading"] + r"\centering}{\thechapter}{"
            + TITLE["chapter_gap"] + "}{}\n"
            + r"\titlespacing*{\chapter}{0pt}{" + top + "}{" + TITLE["chapter_after"] + "}")


def toc_format():
    out = []
    for level, (indent, label) in TOC.items():
        space = VSPACE_MINI if level == "chapter" else ""
        out.append(r"\titlecontents{" + level + "}[" + indent + "]\n"
                   + r"  {\normalfont" + space + "}\n"
                   + r"  {\contentslabel{" + label + "}}\n"
                   + r"  {\hspace*{-" + label + "}}\n"
                   + r"  {\hfill\contentspage}")
    return "\n\n".join(out)


def colspec(*cols):
    """Column spec from (align, fraction of the line width) pairs."""
    parts = []
    n_cols = len(cols)
    extra_rule_adj = f"{1.0 / n_cols:.3f}".rstrip("0").rstrip(".")
    for align, frac in cols:
        pct = f"{frac:.3f}".rstrip("0").rstrip(".")
        dim = rf"\dimexpr {pct}\linewidth-2\tabcolsep-\arrayrulewidth-{extra_rule_adj}\arrayrulewidth\relax"
        if align == "p":
            parts.append(rf">{{\arraybackslash}}p{{{dim}}}")
        elif align == "C":
            parts.append(rf">{{\centering\arraybackslash}}p{{{dim}}}")
        elif align == "R":
            parts.append(rf">{{\raggedleft\arraybackslash}}p{{{dim}}}")
        elif align == "L":
            parts.append(rf">{{\raggedright\arraybackslash}}p{{{dim}}}")
        else:
            parts.append(align)
    return "|" + "|".join(parts) + "|"


# column layouts of the report tables
TABLE_SPECS = {
    "ch1_info": colspec(("L", 0.38), ("L", 0.62)),
    "two_col_desc": colspec(("L", 0.35), ("p", 0.65)),
    "two_col_wide_val": colspec(("L", 0.38), ("L", 0.62)),
    "two_col_loads": colspec(("L", 0.35), ("p", 0.65)),
    "two_col_combos": colspec(("C", 0.25), ("p", 0.75)),
    "two_col_defl": colspec(("L", 0.45), ("p", 0.55)),
    "title_meta": colspec(("L", 0.28), ("L", 0.72)),
    "ch2_girder_info": colspec(("L", 0.14), ("L", 0.14), ("p", 0.24), ("p", 0.24), ("p", 0.24)),
    "ch2_girder_dim": colspec(("L", 0.12), ("L", 0.15), ("L", 0.12), ("p", 0.31), ("p", 0.30)),
    "ch2_girder_restraint": colspec(("L", 0.11), ("p", 0.16), ("p", 0.15), ("p", 0.22), ("p", 0.185), ("p", 0.175)),
    "ch2_bracing": colspec(("L", 0.17), ("L", 0.19), ("L", 0.22), ("L", 0.25), ("C", 0.17)),
    "ch2_diaphragm": colspec(("L", 0.22), ("L", 0.22), ("L", 0.26), ("L", 0.30)),
    "five_col_loads": colspec(("L", 0.28), ("C", 0.16), ("C", 0.14), ("C", 0.24), ("C", 0.18)),
    "ch3_vehicle_loads": colspec(("L", 0.19), ("C", 0.16), ("C", 0.12), ("C", 0.19), ("C", 0.15), ("C", 0.19)),
    "ch4_demands": colspec(("C", 0.18), ("C", 0.11), ("C", 0.09), ("C", 0.09), ("C", 0.11), ("C", 0.09), ("C", 0.09), ("C", 0.12), ("C", 0.12)),
    "ch4_reactions": colspec(("C", 0.33), ("C", 0.33), ("C", 0.34)),
    "ch4_deflection": colspec(("L", 0.45), ("p", 0.55)),
    "ch5_sec_prop": colspec(("C", 0.16), ("L", 0.52), ("p", 0.32)),
    "ch5_sec_class": colspec(("C", 0.16), ("L", 0.20), ("C", 0.23), ("C", 0.16), ("p", 0.25)),
    "ch5_moment_cap": colspec(("C", 0.16), ("C", 0.23), ("C", 0.23), ("p", 0.26), ("C", 0.12)),
    "ch5_shear_cap": colspec(("C", 0.16), ("C", 0.23), ("C", 0.23), ("p", 0.26), ("C", 0.12)),
    "ch5_interaction": colspec(("C", 0.16), ("C", 0.23), ("C", 0.23), ("p", 0.26), ("C", 0.12)),
    "ch5_ltb": colspec(("C", 0.16), ("C", 0.23), ("C", 0.23), ("p", 0.26), ("C", 0.12)),
    "ch5_stiffener_summary": colspec(("C", 0.16), ("L", 0.42), ("p", 0.42)),
    "ch5_end_panel": colspec(("C", 0.16), ("L", 0.23), ("C", 0.23), ("p", 0.26), ("C", 0.12)),
    "ch5_serv_defl": colspec(("C", 0.16), ("L", 0.23), ("C", 0.23), ("p", 0.23), ("C", 0.15)),
    "ch5_serv_stress": colspec(("C", 0.16), ("L", 0.23), ("C", 0.23), ("p", 0.23), ("C", 0.15)),
    "ch5_fatigue": colspec(("C", 0.16), ("C", 0.23), ("C", 0.23), ("p", 0.23), ("C", 0.15)),
    "ch5_girder_summary": colspec(("C", 0.11), ("p", 0.24), ("C", 0.16), ("C", 0.13), ("C", 0.14), ("C", 0.11), ("C", 0.11)),
    "ch5_sc_cap": colspec(("L", 0.24), ("C", 0.38), ("p", 0.18), ("L", 0.20)),
    "ch5_sc_spacing": colspec(("L", 0.23), ("p", 0.31), ("p", 0.31), ("C", 0.15)),
    "ch5_sc_transverse": colspec(("L", 0.37), ("p", 0.49), ("C", 0.14)),
    "ch5_deck_loading": colspec(("L", 0.35), ("p", 0.65)),
    "ch5_deck_flexure": colspec(("C", 0.19), ("C", 0.23), ("C", 0.19), ("p", 0.27), ("C", 0.12)),
    "ch5_deck_cantilever": colspec(("L", 0.35), ("C", 0.23), ("p", 0.29), ("C", 0.13)),
    "ch5_deck_punching": colspec(("L", 0.35), ("C", 0.23), ("p", 0.29), ("C", 0.13)),
    "ch5_deck_crack": colspec(("L", 0.45), ("p", 0.55)),
    "ch5_deck_oneway": colspec(("L", 0.35), ("C", 0.23), ("p", 0.29), ("C", 0.13)),
    "ch5_deck_rebar": colspec(("L", 0.35), ("p", 0.27), ("p", 0.26), ("C", 0.12)),
    "ch5_cb_props": colspec(("C", 0.16), ("L", 0.16), ("L", 0.17), ("C", 0.19), ("C", 0.16), ("C", 0.16)),
    "ch5_cb_slenderness": colspec(("C", 0.14), ("L", 0.14), ("L", 0.16), ("C", 0.16), ("C", 0.16), ("p", 0.24)),
    "ch5_cb_capacity": colspec(("C", 0.125), ("L", 0.12), ("C", 0.135), ("C", 0.19), ("C", 0.12), ("C", 0.13), ("C", 0.08), ("C", 0.10)),
    "ch5_ed_props": colspec(("C", 0.16), ("L", 0.16), ("L", 0.17), ("C", 0.19), ("C", 0.16), ("C", 0.16)),
    "ch5_ed_slenderness": colspec(("C", 0.14), ("L", 0.14), ("L", 0.16), ("C", 0.16), ("C", 0.16), ("p", 0.24)),
    "ch5_ed_capacity": colspec(("C", 0.125), ("L", 0.12), ("C", 0.135), ("C", 0.19), ("C", 0.12), ("C", 0.13), ("C", 0.08), ("C", 0.10)),
    "ch5_overall_summary": colspec(("C", 0.24), ("L", 0.32), ("C", 0.16), ("C", 0.16), ("p", 0.12)),
    "ch7_boq": colspec(("C", 0.08), ("L", 0.24), ("C", 0.19), ("C", 0.13), ("C", 0.12), ("C", 0.12), ("C", 0.12)),
    "ch8_history": colspec(("C", 0.10), ("C", 0.10), ("p", 0.80)),
}


def _packages():
    geom_opts = [
        PAGE["paper"],
        f"top={PAGE['top']}",
        f"bottom={PAGE['bottom']}",
        f"left={PAGE['left']}",
        f"right={PAGE['right']}",
        f"headheight={PAGE['headheight']}",
        f"headsep={PAGE['headsep']}",
        f"footskip={PAGE['footskip']}",
    ]
    if PAGE.get("includeheadfoot"):
        geom_opts.append("includeheadfoot")
    return r"""% Packages
\usepackage[""" + ", ".join(geom_opts) + r"""]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=""" + FONT["caption_label"] + r""",
    justification=raggedright,
    singlelinecheck=false,
    format=plain,
    skip=4pt
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{hhline}
\usepackage{longtable}
\setlength{\LTleft}{""" + TABLE["lt_left"] + r"""}
\setlength{\LTright}{""" + TABLE["lt_right"] + r"""}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}
"""


def _table_setup():
    n = str(TABLE["needspace_lines"])
    return r"""
\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\setlength{\tabcolsep}{""" + TABLE["tabcolsep"] + r"""}
\renewcommand{\arraystretch}{""" + str(TABLE["arraystretch"]) + r"""}
\setlength{\LTpre}{""" + TABLE["lt_pre"] + r"""}
\setlength{\LTpost}{""" + TABLE["lt_post"] + r"""}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{""" + TABLE["rule_width"] + r"""}
\setlength{\extrarowheight}{""" + TABLE["extrarowheight"] + r"""}

% Prevent tables from overflowing past the page bottom:
\BeforeBeginEnvironment{table}{\needspace{""" + n + r"""\baselineskip}}
\BeforeBeginEnvironment{longtable}{\Needspace*{""" + n + r"""\baselineskip}}
"""


def _rule(gap):
    hf = HEADER_FOOTER
    return r"\color{osdagGreen}\hrule width\headwidth height " + hf["rule"] + r" \vspace{" + gap + "}"


def _page_style(name, head_l, head_r):
    hf = HEADER_FOOTER
    return r"""\fancypagestyle{""" + name + r"""}{
  \fancyhf{}
  \fancyhead[L]{""" + head_l + r"""}
  \fancyhead[R]{""" + head_r + r"""}
  \fancyfoot[L]{""" + hf["foot_left"] + r"""}
  \fancyfoot[R]{""" + hf["foot_right"] + r"""}
  \renewcommand{\headrule}{""" + _rule(hf["headrule_gap"]) + r"""}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \hbox to \headwidth{\textcolor{""" + COLORS["sd_note"] + r"""}{\footnotesize\textit{""" + hf["sd_note"] + r"""}}\hfil}%
      \vskip """ + hf["sd_note_gap"] + r"""%
    }{}%
    """ + _rule(hf["footrule_gap"]) + r"""%
  }
}
"""


def _first_page_style():
    hf = HEADER_FOOTER
    return r"""\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{""" + hf["foot_left"] + r"""}
  \fancyfoot[R]{""" + hf["foot_right"] + r"""}
  \renewcommand{\footrule}{""" + _rule(hf["footrule_gap"]) + r"""}
}
"""


def _pdf_text(value):
    """Plain text for the PDF title and author fields."""
    return "".join(c for c in str(value or "") if c not in "\\{}%#&$^_~")


def preamble_block(meta):
    vals = {k: _tex(meta.get(k, '')) for k in ('project', 'job', 'date', 'rev')}
    head_l = HEADER_FOOTER["left"].format(**vals)
    head_r = HEADER_FOOTER["right"].format(**vals)
    return (
        "\n\\documentclass[" + FONT["size"] + "," + PAGE["paper"] + "]{" + PAGE["doc_class"] + "}\n\n"
        + _packages()
        + "\\hypersetup{pdftitle={" + _pdf_text(meta.get('project')) + "}, pdfauthor={"
        + _pdf_text(meta.get('author')) + "},pdfcreator={},pdfproducer={}}\n"
        + _table_setup()
        + "\n% Colors\n"
        + "\\definecolor{osdagGreen}{HTML}{" + COLORS["brand"] + "}\n"
        + "\\definecolor{osdagPass}{HTML}{" + COLORS["pass_"] + "}\n"
        + "\\definecolor{osdagFail}{HTML}{" + COLORS["fail"] + "}\n"
        + "\\definecolor{osdagWarn}{HTML}{" + COLORS["warn"] + "}\n"
        + "\\definecolor{osdagInfo}{HTML}{" + COLORS["info"] + "}\n\n"
        + _page_style("main", head_l, head_r)
        + _page_style("plain", head_l, head_r)
        + _first_page_style()
        + r"""\pagestyle{main}
\setstretch{""" + str(FONT["linespread"]) + r"""}
\setlength{\emergencystretch}{""" + FONT["emergency_stretch"] + r"""}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{""" + COLORS["todo_bg"] + r"""}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

\makeatletter
\def\osRowEnd{\@ifnextchar\bgroup{\osRowEnd@gobble}{\\[""" + TABLE["row_gap"] + r"""]}}
\def\osRowEnd@gobble#1{\\[""" + TABLE["row_gap"] + r"""]}
\def\osRowEndLg{\@ifnextchar\bgroup{\osRowEndLg@gobble}{\\[""" + TABLE["row_gap_lg"] + r"""]}}
\def\osRowEndLg@gobble#1{\\[""" + TABLE["row_gap_lg"] + r"""]}
\def\osRowEndSm{\@ifnextchar\bgroup{\osRowEndSm@gobble}{\\[""" + TABLE["row_gap_sm"] + r"""]}}
\def\osRowEndSm@gobble#1{\\[""" + TABLE["row_gap_sm"] + r"""]}

\def\osRowKeep{\@ifnextchar\bgroup{\osRowKeep@gobble}{\\*[""" + TABLE["row_gap"] + r"""]}}
\def\osRowKeep@gobble#1{\\*[""" + TABLE["row_gap"] + r"""]}
\def\osRowKeepLg{\@ifnextchar\bgroup{\osRowKeepLg@gobble}{\\*[""" + TABLE["row_gap_lg"] + r"""]}}
\def\osRowKeepLg@gobble#1{\\*[""" + TABLE["row_gap_lg"] + r"""]}
\def\osRowKeepSm{\@ifnextchar\bgroup{\osRowKeepSm@gobble}{\\*[""" + TABLE["row_gap_sm"] + r"""]}}
\def\osRowKeepSm@gobble#1{\\*[""" + TABLE["row_gap_sm"] + r"""]}
\makeatother
\newcommand{\osTableSpace}{\vspace{""" + SPACING["table_space"] + r"""}}
\newcommand{\osTableSpaceLg}{\vspace{""" + SPACING["table_space_lg"] + r"""}}
\newcommand{\osTableSpaceSm}{\vspace{""" + SPACING["table_space_sm"] + r"""}}
\newcommand{\osSectionSpace}{\vspace{""" + SPACING["section_gap"] + r"""}}
\newcommand{\osSmallSpace}{\vspace{""" + SPACING["small_gap"] + r"""}}
\newcommand{\osMiniSpace}{\vspace{""" + SPACING["mini_gap"] + r"""}}
\newcommand{\osTitleTopSpace}{\vspace*{""" + SPACING["title_top"] + r"""}}
\newcommand{\osFigPreSpace}{\vspace{""" + SPACING["fig_pre"] + r"""}}
\newcommand{\osFigMidSpace}{\vspace{""" + SPACING["fig_post"] + r"""}}
\newcommand{\osFigPostSpace}{\vspace{""" + SPACING["fig_pre"] + r"""}}
\newcommand{\osFigWideW}{""" + FIGURE["wide_width"] + r"""}
\newcommand{\osChartW}{""" + FIGURE["chart_width"] + r"""}
\newcommand{\osFigMaxH}{""" + FIGURE["max_height"] + r"""}
\newcommand{\osFigPlotH}{""" + FIGURE["plot_height"] + r"""}
\newcommand{\osFigSectionH}{""" + FIGURE["section_height"] + r"""}

\newcommand{\osPass}{\textcolor{osdagPass}{\textbf{PASS}}}
\newcommand{\osFail}{\textcolor{osdagFail}{\textbf{FAIL}}}
\newcommand{\osPassText}[1]{\textcolor{osdagPass}{#1}}
\newcommand{\osFailText}[1]{\textcolor{osdagFail}{#1}}
\newcommand{\osWarnText}[1]{\textcolor{osdagWarn}{#1}}
\newcommand{\osLogInfo}[1]{\textcolor{osdagGreen}{#1}}
\newcommand{\osLogWarn}[1]{\textcolor{osdagInfo}{#1}}
\newcommand{\osLogError}[1]{\textcolor{osdagFail}{#1}}
\newcommand{\osNote}[1]{\noindent\textit{#1}}
\newcommand{\osTableFoot}[1]{\par\noindent{\footnotesize\itshape\interlinepenalty=10000 #1\par}}
\newcommand{\osDenseTable}{\footnotesize\setlength{\tabcolsep}{""" + TABLE["tabcolsep_dense"] + r"""}\renewcommand{\arraystretch}{""" + str(TABLE["arraystretch_dense"]) + r"""}}
\newcommand{\osCompactTable}{\setlength{\tabcolsep}{""" + TABLE["tabcolsep_compact"] + r"""}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{""" + SPACING["title_gap"] + r"""} \large Design Report}
\author{}
\date{}

\begin{document}
"""
    )
