from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _count_cols(col_spec):
    """Count longtable columns from a LaTeX column spec string.

    Handles modifiers like >{...}, @{...}, repeated specs *{N}{...}, and column types.
    """
    import re
    spec = col_spec.strip()

    def find_closing_brace(s, pos):
        depth = 0
        for i in range(pos, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    return i
        return len(s)

    # expand *{N}{spec}
    while "*{" in spec:
        idx = spec.find("*{")
        end_n = find_closing_brace(spec, idx + 1)
        try:
            n_repeat = int(spec[idx + 2:end_n].strip())
        except ValueError:
            break
        if end_n + 1 < len(spec) and spec[end_n + 1] == "{":
            end_content = find_closing_brace(spec, end_n + 1)
            content = spec[end_n + 2:end_content]
            spec = spec[:idx] + (content * n_repeat) + spec[end_content + 1:]
        else:
            break

    # strip modifiers: >, <, @, !
    out = []
    i = 0
    n = len(spec)
    while i < n:
        if spec[i] in "><@!" and i + 1 < n and spec[i + 1] == "{":
            end_brace = find_closing_brace(spec, i + 1)
            i = end_brace + 1
        else:
            out.append(spec[i])
            i += 1
    spec = "".join(out)

    # strip width arguments for column types L, C, R, p, m, b
    out = []
    i = 0
    n = len(spec)
    while i < n:
        if spec[i] in "LCRpmb" and i + 1 < n and spec[i + 1] == "{":
            out.append(spec[i])
            end_brace = find_closing_brace(spec, i + 1)
            i = end_brace + 1
        else:
            out.append(spec[i])
            i += 1
    spec = "".join(out)

    cols = re.findall(r"[LCRpmbclrXs]", spec)
    return max(1, len(cols))


SHORT_TABLE_ROWS = 12


def _keep_blocks_together(body, ncols):
    """Stop a page break inside a girder block.

    Rows inside a block end with \\osRowKeep (\\\\*), but the \\cline after
    them adds a negative skip that LaTeX can still break at, so blocks split
    and the continued rows lose their girder label. \\hhline has no such skip,
    and the \\nopagebreak after it covers the gap before the next row.
    """
    import re

    def _rule(m):
        a, b = int(m.group(2)), int(m.group(3))
        cells = ['~'] * (a - 1) + ['-'] * (b - a + 1) + ['~'] * (ncols - b)
        # inside longtable \\nopagebreak is already a between-rows command
        return m.group(1) + '\\hhline{|' + '|'.join(cells) + '|}\\nopagebreak'

    return re.sub(r'(\\osRowKeep(?:Lg|Sm)?\{\}\s*)\\cline\{(\d+)-(\d+)\}', _rule, body)


def design_lanes(input_dict):
    """Number of traffic lanes for the report.

    The Lane Details counter is disabled in Additional Inputs, so it is usually
    empty. Then use IRC 6 Table 6 on the carriageway width, the same rule the
    analyser uses. With a median the carriageway is split, so no value is guessed.
    Returns (lanes, from_width) or (None, False).
    """
    from osdagbridge.core.utils.common import (
        KEY_CARRIAGEWAY_WIDTH, KEY_INCLUDE_MEDIAN, KEY_WC_LD_LANE_TABLE_COUNT)
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    val = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    if val not in (None, ''):
        try:
            return int(val), False
        except (TypeError, ValueError):
            pass
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, 'No')).strip().lower() in ('yes', 'true', '1'):
        return None, False
    try:
        width = float(input_dict.get(KEY_CARRIAGEWAY_WIDTH))
        return IRC6_2017.table_6(width), True
    except (TypeError, ValueError):
        return None, False


def longtable(col_spec, caption, label, header_row, body, *, tabcolsep=None, lt_left=None):
    """Build a longtable with repeated headers on every page (R1).

    Args:
        col_spec  : LaTeX column specification string (e.g. from styles.TABLE_SPECS)
        caption   : plain-text caption (will be wrapped in \\textbf inside \\caption)
        label     : LaTeX label string, e.g. 'tab:ch2:typical-section'
        header_row: raw LaTeX for the header row(s) ending with \\\\ (no trailing \\hline)
        body      : raw LaTeX rows for the table body
        tabcolsep : optional override for \\tabcolsep inside this table only (string, e.g. '4pt')
        lt_left   : optional override for \\LTleft inside this table only (string, e.g. '0pt')

    Returns a string of LaTeX that contains \\endfirsthead and \\endhead so the
    scanner exits 0.  The 'continued' header uses \\caption[]{} so the counter
    does not increment and no extra List-of-Tables entry is added.
    """
    overrides = []
    if tabcolsep:
        overrides.append('\\setlength{\\tabcolsep}{' + tabcolsep + '}')
    if lt_left:
        overrides.append('\\setlength{\\LTleft}{' + lt_left + '}')
    grp_open  = ('\\begingroup\n' + '\n'.join(overrides) + '\n') if overrides else ''
    grp_close = '\\endgroup\n' if overrides else ''

    ncols = _count_cols(col_spec)
    body = _keep_blocks_together(body, ncols)

    # Short tables: ask for room for the whole table before it starts, so a
    # 5-row table does not leave one row alone on the next page. Rough height:
    # 2 lines per row + 4 for caption and header. Long tables still split.
    n_rows = body.count('\\hline') + body.count('\\cline')
    if n_rows <= SHORT_TABLE_ROWS:
        grp_open = '\\Needspace*{' + str(2 * n_rows + 4) + '\\baselineskip}\n' + grp_open

    cont_hdr = (
        '\\caption[]{\\textbf{' + caption + '} (continued)}\\\\\n'
        '\\hline\n'
        + header_row + '\n'
        '\\hline\n'
    )

    # endfoot: right-aligned "continued" note spanning all columns
    endfoot = (
        '\\multicolumn{' + str(ncols) + '}{r}{'
        '\\footnotesize\\textit{Continued on next page}}\\\\\n'
    )

    return (
        grp_open
        + '\\begin{longtable}{' + col_spec + '}\n'
        + '\\caption{\\textbf{' + caption + '}}\\label{' + label + '}\\\\\n'
        + '\\hline\n'
        + header_row + '\n'
        + '\\hline\n'
        + '\\endfirsthead\n'
        + cont_hdr
        + '\\endhead\n'
        + endfoot
        + '\\endfoot\n'
        + '\\endlastfoot\n'
        + body
        + '\\end{longtable}\n'
        + grp_close
    )


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')

def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\osFigPreSpace{}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\osFigMidSpace{}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\osFigPostSpace{}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


