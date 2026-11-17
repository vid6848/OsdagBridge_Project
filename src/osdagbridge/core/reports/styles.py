"""Formatting values for the design report, kept in one place.

The values below are the ones the report already used, so the PDF looks
the same. Change a value here instead of editing the chapter files.
"""
from osdagbridge.core.reports.report_utils import _tex


PAGE = dict(
    doc_class="report",
    paper="a4paper",
    margin="1in",
)

FONT = dict(
    size="12pt",
    linespread=1.15,           # used with \setstretch
    caption_label="bf",
)

COLORS = dict(
    brand="91B014",            # osdagGreen
    sd_note="black",           # "* Software default value" note
    todo_bg="yellow",
)

TABLE = dict(
    tabcolsep="6pt",
    arraystretch=1.12,
    lt_left=r"\fill",
    lt_right=r"\fill",
    lt_pre="0pt",
    lt_post="6pt",
    rule_width="0.5pt",
    extrarowheight="0.6pt",
    needspace_lines=5,         # break page first if less space is left
)

SPACING = dict(
    title_gap="2cm",           # gap in \title before "Design Report"
)

HEADER_FOOTER = dict(
    left=r"{project} $|$ {job}",
    right=r"{date} $|$ {rev}",
    foot_left=r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay",
    foot_right=r"Page \thepage\ of \pageref{LastPage}",
    rule="1pt",
    headrule_gap="2pt",
    footrule_gap="6pt",
    footrule_raise="-8pt",
    sd_note=r"* Software default value",
    sd_note_raise="-20pt",
    sd_note_gap="4pt",
)

# no charts in the report yet, values get added with the chart code
CHART = dict()


def _packages():
    return r"""% Packages
\usepackage[""" + PAGE["paper"] + ", margin=" + PAGE["margin"] + r"""]{geometry}
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
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
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
% if fewer than """ + n + r""" baseline-skips remain, break to the next page first.
\BeforeBeginEnvironment{table}{\needspace{""" + n + r"""\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{""" + n + r"""\baselineskip}}
"""


def _rule(gap):
    hf = HEADER_FOOTER
    return r"\color{osdagGreen}\hrule width\headwidth height " + hf["rule"] + r" \vspace{" + gap + "}"


def _page_style(name, head_l, head_r):
    # same header and footer for the main and plain styles
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
      \vspace{""" + hf["sd_note_raise"] + r"""}%
      \hbox to \headwidth{\textcolor{""" + COLORS["sd_note"] + r"""}{\footnotesize\textit{""" + hf["sd_note"] + r"""}}\hfil}%
      \vspace{""" + hf["sd_note_gap"] + r"""}%
    }{%
      \vspace{""" + hf["footrule_raise"] + r"""}%
    }%
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
  \renewcommand{\footrule}{\vspace{""" + hf["footrule_raise"] + "}" + _rule(hf["footrule_gap"]) + r"""}
}
"""


def preamble_block(meta):
    """Return the LaTeX preamble up to \\begin{document}.

    meta has the keys project, job, date and rev (plain text, escaped here).
    """
    vals = {k: _tex(meta.get(k, '')) for k in ('project', 'job', 'date', 'rev')}
    head_l = HEADER_FOOTER["left"].format(**vals)
    head_r = HEADER_FOOTER["right"].format(**vals)
    return (
        "\n\\documentclass[" + FONT["size"] + "," + PAGE["paper"] + "]{" + PAGE["doc_class"] + "}\n\n"
        + _packages()
        + _table_setup()
        + "\n\\definecolor{osdagGreen}{HTML}{" + COLORS["brand"] + "}\n\n"
        + _page_style("main", head_l, head_r)
        + _page_style("plain", head_l, head_r)
        + _first_page_style()
        + r"""\pagestyle{main}
\setstretch{""" + str(FONT["linespread"]) + r"""}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{""" + COLORS["todo_bg"] + r"""}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

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
