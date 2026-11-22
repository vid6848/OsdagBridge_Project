from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_TS_NO_OF_GIRDERS
)

# shown instead of an empty cell, explained by not_stored_note()
NOT_STORED = r'-\textsuperscript{\S}'


def not_stored_note(tex):
    """The footnote for NOT_STORED, only if the given table uses it."""
    if NOT_STORED not in tex:
        return ''
    return '\\osTableFoot{\\textsuperscript{\\S} Not available in the design output.}\n'


def main_girder_keys(per_girder, n_girders):
    """Design result keys of the bridge's own girders, in order G1..Gn.

    The design checks every longitudinal grid line and numbers them G1..Gm.
    With a deck overhang the first and the last line are edge beams, so a
    5 girder bridge has G1..G7 and the girders are G2..G6. The deflection and
    Chapter 4 values already leave the edge beams out.
    Returns [] if the lines cannot be matched, so no row gets a wrong label.
    """
    def order(key):
        num = str(key)[1:]
        return int(num) if num.isdigit() else 0

    lines = sorted((k for k in per_girder if not str(k).startswith('EB')), key=order)
    if not lines or n_girders < 1:
        return []
    if len(lines) == n_girders:
        return lines
    if len(lines) == n_girders + 2:
        return lines[1:-1]
    return []


def girder_dims_mm(input_dict, index):
    """[D, tw, bf top, tf top, bf bottom, tf bottom] of girder Gi in mm, or None."""
    keys = (KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_THICKNESS,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS)
    dims = [_size_mm(input_dict.get(f"{k}.G{index}.M1")) for k in keys]
    return None if None in dims else dims


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


def _keep_closing_rules(body):
    """Keep the rule under a row on the same page as the row.

    A plain row end allows a break before \\hline, which leaves the last block
    on a page open at the bottom.
    """
    import re

    body = re.sub(r'\\osRowEnd(Lg|Sm)?\{\}(?:\s*\\cline\{\d+-\d+\})?(\s*\\hline)',
                  r'\\osRowKeep\1{}\2', body)
    return re.sub(r'\\\\(\s*\n\\hline)', r'\\\\*\1', body)


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
    import re

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
    # 1.3 lines per row + 4 for caption and header. Long tables still split.
    n_rows = body.count('\\hline') + body.count('\\cline')
    if n_rows <= SHORT_TABLE_ROWS:
        grp_open = '\\Needspace*{' + str(int(1.3 * n_rows) + 4) + '\\baselineskip}\n' + grp_open

    body = _keep_closing_rules(body)
    # no empty cells. The first column is left alone, it is empty under a girder label
    body = re.sub(r'(?<!\\)&(?=[ \t]*(?:&|\\osRow))',
                  lambda _m: '& ' + NOT_STORED + ' ', body)

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
        + not_stored_note(body)
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
    # pdflatex drops these in text, so use the math symbols
    return s.replace('≤', r'$\leq$').replace('≥', r'$\geq$')


def _size_mm(value):
    '''A girder size in mm. After Design the inputs hold metres, before it mm.'''
    try:
        val = float(value)
    except (TypeError, ValueError):
        return None
    # no plate is under 5 mm and no girder here is 5 m deep
    if val < 5:
        val *= 1000
    return round(val, 1)


def _render_size_mm(source_dict, key):
    val = _size_mm(source_dict.get(key))
    if val is None:
        return _render_value(source_dict, key)
    return f"{val:g} mm"


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return NOT_STORED
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
                r'\includegraphics[width=' + width + r',height=\osFigMaxH,keepaspectratio]{' + p + '}\n'
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


