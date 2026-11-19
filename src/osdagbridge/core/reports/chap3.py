# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_ECCENTRICITY,
    KEY_BL_IRC_CLASS_A, KEY_BL_IRC_70R_WHEELED, KEY_BL_IRC_70R_TRACKED, KEY_BL_IRC_AA_WHEELED,
    KEY_BL_IRC_AA_TRACKED, KEY_BL_IRC_CLASS_SV, KEY_BL_IRC_70R_BOGIE, KEY_BL_IRC_CLASS_FATIGUE,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, longtable
from osdagbridge.core.reports.styles import TABLE_SPECS, ROW_END, VSPACE_SEC


def _is_on(val):
    """Return True for True / 1 / 'True' / '1' / 'yes', False otherwise."""
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    return str(val).strip().lower() in ('true', '1', 'yes', 'on')

def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # -------------------------------------------------------------------------
    # Vehicle live load rows — only ticked vehicles appear
    # -------------------------------------------------------------------------
    # Vehicles where IRC 6 gives no braking definition (tracked/bogie types)
    _NO_BRAKING = {'Class AA (Tracked)', 'Class 70R (Bogie)'}

    _NA = r'---\textsuperscript{\dag}'

    def _total_kN(fn):
        # total vehicle load from the IRC 6 module (wheel loads are in N)
        try:
            veh = fn()
            if 'total_load_kN' in veh:
                return f"{float(veh['total_load_kN']):.2f}"
            return f"{sum(veh['wheel_loads']) / 1000.0:.2f}"
        except Exception:
            return _NA

    # (key, display_name, impact_clause, no_braking, braking_key, total_load_kN)
    _VEHICLE_DEFS = [
        (KEY_LL_IRC_CLASS_A,       'Class A',              'Class A',  False, KEY_BL_IRC_CLASS_A,       _total_kN(IRC6_2017.cl_204_1_ClassA_vehicle)),
        (KEY_LL_IRC_70R_WHEELED,   'Class 70R (Wheeled)',  'AA/70R',   False, KEY_BL_IRC_70R_WHEELED,   _total_kN(IRC6_2017.cl_204_1_Class70R_vehicle_wheel)),
        (KEY_LL_IRC_70R_TRACKED,   'Class 70R (Tracked)',  'AA/70R',   False, KEY_BL_IRC_70R_TRACKED,   _NA),
        (KEY_LL_IRC_AA_WHEELED,    'Class AA (Wheeled)',   'AA/70R',   False, KEY_BL_IRC_AA_WHEELED,    _NA),
        (KEY_LL_IRC_AA_TRACKED,    'Class AA (Tracked)',   'AA/70R',   True,  KEY_BL_IRC_AA_TRACKED,    _NA),
        (KEY_LL_IRC_CLASS_SV,      'Class SV',             'Class A',  False, KEY_BL_IRC_CLASS_SV,      _total_kN(IRC6_2017.cl_204_5_1_special_vehicle)),
        (KEY_LL_IRC_70R_BOGIE,     'Class 70R (Bogie)',    'AA/70R',   True,  KEY_BL_IRC_70R_BOGIE,     _NA),
        (KEY_LL_IRC_CLASS_FATIGUE, 'Class Fatigue',        'Class A',  False, KEY_BL_IRC_CLASS_FATIGUE, _total_kN(IRC6_2017.cl_204_6_fatigue_load)),
    ]

    span = input_dict.get(KEY_SPAN)
    span_m = None
    if span not in (None, ''):
        try:
            span_m = float(span)
        except (ValueError, TypeError):
            span_m = None

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    lanes_int = None
    if lanes not in (None, ''):
        try:
            lanes_int = int(lanes)
        except (ValueError, TypeError):
            lanes_int = None

    # Pre-compute braking force once (same value for all ticked vehicles)
    braking_kN_str = '---'
    if lanes_int is not None:
        try:
            braking_kN = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_kN_str = f'{braking_kN:.2f}'
        except Exception:
            braking_kN_str = 'N/A'

    # Eccentricity from input
    ecc_val = (
        input_dict.get(KEY_LL_ECCENTRICITY)
        or input_dict.get(KEY_BL_ECCENTRICITY)
        or input_dict.get('bl_eccentricity')
    )
    if ecc_val not in (None, ''):
        try:
            ecc_str = f'{float(ecc_val):.2f}'
        except (ValueError, TypeError):
            ecc_str = _tex(ecc_val)
    else:
        ecc_str = '---'

    # Build one row per ticked vehicle
    veh_rows = []
    for key, name, im_cls, no_braking, bl_key, total_kN in _VEHICLE_DEFS:
        if not _is_on(input_dict.get(key)):
            continue

        # Impact factor
        if span_m is not None:
            try:
                if im_cls == 'Class A':
                    im = IRC6_2017.cl_208_2_impact_factor(span_m)
                else:
                    im = IRC6_2017.cl_208_3_impact_factor(span_m)
                im_str = f'{1.0 + im:.3f}'
            except Exception:
                im_str = 'N/A'
        else:
            im_str = 'N/A'

        # Braking
        if no_braking:
            br_considered = r'---\textsuperscript{\dag}'
            br_value      = r'---\textsuperscript{\dag}'
        elif _is_on(input_dict.get(bl_key, True)):
            br_considered = 'Yes'
            br_value      = braking_kN_str
        else:
            br_considered = 'No'
            br_value      = '---'

        veh_rows.append(
            _tex(name) + r' & ' + total_kN + r' & ' + im_str + r' & ' + br_considered
            + r' & ' + br_value + r' & ' + ecc_str
            + r' \osRowEnd{}' + '\n\\hline'
        )

    # Custom vehicles if specified
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get('name') if isinstance(c, dict) else str(c)
            if c_name:
                veh_rows.append(
                    _tex(c_name) + r' & ' + '---' + r' & ' + '---' + r' & ' + '---'
                    + r' & ' + '---' + r' & ' + ecc_str
                    + r' \osRowEnd{}' + '\n\\hline'
                )

    if not veh_rows:
        veh_rows.append(
            r'---' + r' & ---' * 5 + r' \osRowEnd{}' + '\n\\hline'
        )

    veh_body = '\n'.join(veh_rows)
    veh_hdr  = (
        r'\multirow{2}{*}{\textbf{Vehicle}} & \multirow{2}{*}{\makecell{\textbf{Total}\\\textbf{Load}\\\textbf{(kN)}}}'
        r' & \multirow{2}{*}{\makecell{\textbf{Impact}\\\textbf{Factor}}} & \multicolumn{3}{c|}{\textbf{Braking Load}} \\'
        '\n\\cline{4-6}\n'
        r' & & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity (m)} \\'
    )
    _dag_note = (
        r'\osNote{\textsuperscript{\dag} Not defined for this vehicle type in the IRC~6 module of this version.}'
    )

    # -------------------------------------------------------------------------
    # Footpath / kerb live load
    # -------------------------------------------------------------------------
    fp_cfg   = str(input_dict.get(KEY_FOOTPATH, 'None')).strip()
    if fp_cfg in ('None', '', 'False', '0'):
        fp_present = 'No'
    else:
        fp_present = f'Yes ({fp_cfg})'

    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, '')
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, '')
    if str(fp_mode).strip().lower() in ('as per irc 6', 'as per irc6', 'automatic'):
        try:
            fp_intensity = f'{IRC6_2017.cl_206_1_footway_load():.3f} kN/m\\textsuperscript{{2}}'
            fp_clause    = 'IRC~6 Cl.~206.1'
            fp_mode_str  = 'As per IRC 6'
        except Exception:
            fp_intensity = 'N/A'
            fp_clause    = 'IRC~6 Cl.~206.1'
            fp_mode_str  = 'As per IRC 6'
    elif fp_value not in (None, ''):
        try:
            fp_intensity = f'{float(fp_value):.3f} kN/m\\textsuperscript{{2}}'
        except (TypeError, ValueError):
            fp_intensity = _tex(fp_value)
        fp_clause    = 'User defined'
        fp_mode_str  = 'Custom'
    else:
        fp_intensity = '---'
        fp_clause    = '---'
        fp_mode_str  = '---'

    fp_body = (
        r'\textnormal{Footpaths Present} & ' + fp_present
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Load Mode} & ' + _tex(fp_mode_str)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Intensity} & ' + fp_intensity
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Reference Clause} & ' + fp_clause
        + r' \osRowEnd{}' + '\n\\hline\n'
    )
    _hdr2 = r'\textbf{Parameter} & \textbf{Value} \\'

    # -------------------------------------------------------------------------
    # Centrifugal force note
    # -------------------------------------------------------------------------
    _centrifugal_note = (
        r'\osNote{Centrifugal Force: Not applicable'
        r' --- the design inputs have no horizontal curvature (IRC~6 Cl.~212).}'
    )

    # -------------------------------------------------------------------------
    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    # -------------------------------------------------------------------------
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \osRowEnd{}" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \osRowEnd{}" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    # shared 2-col header for parameter/value tables
    _hdr2 = r'\textbf{Parameter} & \textbf{Value} \\'

    # Dead Load body
    dl_body = (
        r'\textnormal{Steel Self-Weight Applied} & '
        + _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r' kN/m\textsuperscript{3}')
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Concrete Deck Weight} & '
        + _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r' kN/m\textsuperscript{3}')
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Self-Weight Factor} & '
        + _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)
        + r' \osRowEnd{}' + '\n\\hline\n'
    )

    # Surfacing body
    surf_body = (
        r'\textnormal{Wearing Course Load} & '
        + _render_value(input_dict, KEY_WC_MATERIAL)
        + r' x '
        + _render_value(input_dict, KEY_WC_THICKNESS)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Additional SIDL (Crash Barrier)} & '
        + _render_value(input_dict, KEY_CB_LOAD)
        + r' kN/m per barrier \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Railing Load} & '
        + _render_value(input_dict, KEY_RL_LOAD_VALUE)
        + r' kN/m\sdstar{} \osRowEnd{}' + '\n\\hline\n'
    )

    # Wind Load body
    wl_body = (
        r'\textnormal{Basic Wind Speed, Vb} & '
        + _render_value(input_dict, 'wind_speed', ' m/s')
        + r' [from Project Location] \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Terrain Type} & '
        + _render_value(input_dict, KEY_WL_TERRAIN_TYPE)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Average Exposed Height, H (m)} & '
        + _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Hourly Mean Wind Speed, Vz} & '
        + vz_str
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Hourly Wind Pressure, Pz} & '
        + pz_str
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Transverse Wind Force} & '
        + _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Longitudinal Wind Force} & '
        + _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Vertical Wind Force} & '
        + _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')
        + r' \osRowEnd{}' + '\n\\hline\n'
    )

    # Earthquake body
    el_body = (
        r'\textnormal{Seismic Zone} & '
        + _render_value(input_dict, 'seismic_zone')
        + r' [from Project Location] \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Zone Factor, Z} & '
        + _sl(sl_zone_factor)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Importance Factor, I} & '
        + _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Type of Soil} & '
        + _render_value(input_dict, KEY_SL_SOIL_TYPE)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Sa/g} & '
        + _sl(sl_spectral)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Horizontal Seismic Coefficient, Ah} & '
        + _sl(sl_ah)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Vertical Seismic Coefficient, Av} & '
        + _sl(sl_av)
        + r' \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Horizontal Seismic Force (longitudinal)} & '
        + r' kN \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Horizontal Seismic Force (transverse)} & '
        + r' kN \osRowEnd{}' + '\n\\hline\n'
    )

    # Temperature body
    tl_body = (
        r'\textnormal{Maximum Shade Temperature} & '
        + _render_value(input_dict, 'shade_temp_max')
        + r' $^\circ$C \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Minimum Shade Temperature} & '
        + _render_value(input_dict, 'shade_temp_min')
        + r' $^\circ$C \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Effective Bridge Temp. Range} & '
        + tl_temp_min + r' to ' + tl_temp_max
        + r' $^\circ$C \osRowEnd{}' + '\n\\hline\n'
        + r'\textnormal{Temperature Rise / Fall for Design} & +'
        + tl_rise
        + r' $^\circ$C / \textminus{}'
        + tl_fall
        + r' $^\circ$C \osRowEnd{}' + '\n\\hline\n'
    )

    # Load Combinations body
    lc_hdr  = r'\textbf{Combination ID} & \textbf{Load Cases} \osRowEnd{}'
    lc_body = lc_rows_str + '\n'

    return (
        r'\chapter{Loads and Load Combinations}' + '\n\n'
        r'This section summarizes all loads applied to the bridge and the load'
        r' combinations considered for analysis and design.'
        + '\n\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_loads'],
                    'Dead Load -- Self Weight',
                    'tab:ch3:dead-load-sw',
                    _hdr2, dl_body)
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_loads'],
                    'Dead Load for Surfacing (DW)',
                    'tab:ch3:dead-load-dw',
                    _hdr2, surf_body)
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['ch3_vehicle_loads'],
                    'Vehicle Live Loads (LL) --- per IRC~6',
                    'tab:ch3:vehicle-live-loads',
                    veh_hdr, veh_body)
        + '\n'
        + _dag_note
        + '\n\n'
        + _centrifugal_note
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_loads'],
                    'Footpath Live Load --- per IRC~6 Cl.~206.1',
                    'tab:ch3:footpath-load',
                    _hdr2, fp_body)
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_loads'],
                    'Wind Load (WL) --- per IRC 6',
                    'tab:ch3:wind-load',
                    _hdr2, wl_body)
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_loads'],
                    'Earthquake Load (EL) --- per IRC 6',
                    'tab:ch3:earthquake',
                    _hdr2, el_body)
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_loads'],
                    'Temperature Load (TL) --- per IRC 6',
                    'tab:ch3:temperature',
                    _hdr2, tl_body)
        + '\n\\osSectionSpace{}\n'
        + longtable(TABLE_SPECS['two_col_combos'],
                    'Load Combinations',
                    'tab:ch3:load-combos',
                    lc_hdr, lc_body)
        + '\n\n'
        r'\noindent\textit{Note: All IRC 6 load combinations are automatically computed by OsdagBridge.'
        r' User-defined custom combinations, if any, are appended.}'
        + '\n'
    )
