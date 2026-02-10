#!/usr/bin/env python3
"""
Build Atilax Optimization Dashboard - Full implementation.

Creates dashboard "Atilax - Optimizacion de Campo" with:
- Default state: Field-level optimization summary (KPIs, tables, health, field optimization)
- 4 detail states: opt_esp, opt_srp, opt_pcp, opt_gaslift (type-specific optimization detail)

Features:
- KPI aggregation (SUM, AVG, MIN)
- Dynamic health distribution
- Per-type detail with real timeseries charts
- Type-specific diagnostics and optimization cards
- Smart lift_type-based navigation via JS action
"""
import json
import uuid
import requests
import sys

# -- Config ------------------------------------------------------------------
TB_URL = "http://144.126.150.120:8080"
TB_USER = "well@atilax.io"
TB_PASS = "10203040"
DASHBOARD_TITLE = "Atilax - Optimizacion de Campo"

# Entity alias IDs (generated once, stable)
ALIAS_ALL = str(uuid.uuid4())      # All wells
ALIAS_WELL = str(uuid.uuid4())     # State entity (selected well)


def tb_login():
    r = requests.post(f"{TB_URL}/api/auth/login",
                      json={"username": TB_USER, "password": TB_PASS})
    r.raise_for_status()
    return r.json()["token"]


def uid():
    return str(uuid.uuid4())


# -- Dashboard-level CSS -----------------------------------------------------
DASHBOARD_CSS = """.tb-widget-container > .tb-widget {
    border-radius: 8px;
    box-shadow: 0px 2px 8px rgba(222, 223, 224, 0.25);
}
.tb-dashboard-page .tb-widget-container > .tb-widget {
    color: #4B535B !important;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-mdc-table .mat-mdc-header-cell {
    color: rgba(0, 0, 0, 0.38) !important;
    font-weight: 500; font-size: 12px; line-height: 16px; letter-spacing: 0.25px;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-mdc-table .mat-mdc-cell {
    color: #4B535B; border-bottom-color: transparent; font-size: 14px; line-height: 20px;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-table .mat-row:hover:not(.tb-current-entity) {
    background-color: #F9F9FB !important;
}
mat-cell { border: none !important; }
"""


# -- Helper: build a complete dataKey (TB-compatible) -------------------------
def make_dk(name, dtype="attribute", label=None, color="#2196f3", settings=None,
            post_func=None, func_body=None, units=None, decimals=None):
    """Build a complete dataKey with ALL TB-required fields."""
    dk = {
        "name": name,
        "type": dtype,
        "label": label or name,
        "color": color,
        "settings": settings or {},
        "aggregationType": None,
        "units": units,
        "decimals": decimals,
        "funcBody": func_body,
        "usePostProcessing": bool(post_func),
        "postFuncBody": post_func,
    }
    if dtype == "attribute" and "dataKeyType" not in dk["settings"]:
        dk["settings"]["dataKeyType"] = "server"
    return dk


# -- Helper: build a complete datasource (TB-compatible) ----------------------
def make_ds(alias, data_keys, filter_id=None):
    """Build a complete datasource with ALL TB-required fields."""
    return {
        "type": "entity",
        "name": "",
        "entityAliasId": alias,
        "filterId": filter_id,
        "dataKeys": data_keys,
        "alarmFilterConfig": None,
    }


# -- Widget builders (following exact TB patterns) ----------------------------

def _line(color, fill="none", smooth=True, w=2.5):
    return {
        "showLine": True, "step": False, "smooth": smooth,
        "lineType": "solid", "lineWidth": w, "showPoints": False,
        "pointShape": "emptyCircle", "pointSize": 4,
        "fillAreaSettings": {"type": fill, "opacity": 0.3, "gradient": {"start": 100, "end": 0}},
        "showPointLabel": False,
        "pointLabelFont": {"family": "Roboto", "size": 11, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "1"},
        "pointLabelColor": "rgba(0,0,0,0.76)",
        "pointLabelPosition": "top", "stepType": "start",
        "enablePointLabelBackground": False, "pointLabelBackground": "rgba(255,255,255,0.56)",
    }


def _yaxis(aid, units, pos="left"):
    return {
        "id": aid, "order": 0 if pos == "left" else 1, "units": units, "decimals": None,
        "show": True, "label": "", "position": pos, "showTickLabels": True,
        "tickLabelFont": {"family": "Roboto", "size": 11, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "1"},
        "tickLabelColor": "#9FA6B4", "showTicks": False, "showLine": False,
        "showSplitLines": True, "splitLinesColor": "rgba(0,0,0,0.08)",
        "labelFont": {"family": "Roboto", "size": 12, "sizeUnit": "px", "style": "normal", "weight": "600", "lineHeight": "1"},
        "labelColor": "rgba(0,0,0,0.54)", "ticksColor": "rgba(0,0,0,0.54)", "lineColor": "rgba(0,0,0,0.54)",
    }


def build_chart(title, keys, alias=None):
    """Time series chart with dual Y axes."""
    if alias is None:
        alias = ALIAS_WELL
    dkeys = []
    left_u, right_u = set(), set()
    for k in keys:
        yid = "default" if k["y"] == "left" else "right"
        fill = "gradient" if len(keys) == 1 else "none"
        dk = make_dk(k["key"], "timeseries", k["label"], k["c"], settings={
            "yAxisId": yid, "showInLegend": True, "dataHiddenByDefault": False,
            "type": "line", "lineSettings": _line(k["c"], fill),
            "barSettings": {"showBorder": False, "borderWidth": 2, "borderRadius": 0,
                "showLabel": False, "labelPosition": "top",
                "labelFont": {"family": "Roboto", "size": 11, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "1"},
                "labelColor": "rgba(0,0,0,0.76)", "enableLabelBackground": False,
                "labelBackground": "rgba(255,255,255,0.56)",
                "backgroundSettings": {"type": "none", "opacity": 0.4, "gradient": {"start": 100, "end": 0}}},
            "comparisonSettings": {"showValuesForComparison": False, "comparisonValuesLabel": "", "color": ""}
        })
        dk["units"] = k["u"]
        dk["decimals"] = 1
        dkeys.append(dk)
        (left_u if k["y"] == "left" else right_u).add(k["u"])

    yaxes = {"default": _yaxis("default", "/".join(left_u), "left")}
    if right_u:
        yaxes["right"] = _yaxis("right", "/".join(right_u), "right")

    return {
        "typeFullFqn": "system.time_series_chart", "type": "timeseries",
        "sizeX": 24, "sizeY": 10,
        "config": {
            "datasources": [make_ds(alias, dkeys)],
            "showTitle": True, "title": title, "dropShadow": True, "enableFullscreen": True,
            "backgroundColor": "rgba(0,0,0,0)", "color": "rgba(0,0,0,0.87)",
            "padding": "0px", "configMode": "basic", "borderRadius": "8px",
            "titleStyle": {"padding": "5px 10px"},
            "titleFont": {"size": 16, "sizeUnit": "px", "family": "Roboto", "weight": "500", "style": "normal", "lineHeight": "24px"},
            "titleColor": "rgba(0,0,0,0.87)",
            "useDashboardTimewindow": True, "enableDataExport": True,
            "settings": {
                "comparisonEnabled": False,
                "xAxis": {"show": True, "label": "", "position": "bottom", "showTickLabels": True,
                    "tickLabelFont": {"family": "Roboto", "size": 10, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "1"},
                    "tickLabelColor": "#9FA6B4", "showTicks": False, "showLine": False,
                    "showSplitLines": False, "ticksFormat": {},
                    "labelFont": {"family": "Roboto", "size": 12, "sizeUnit": "px", "style": "normal", "weight": "600", "lineHeight": "1"},
                    "labelColor": "rgba(0,0,0,0.54)", "ticksColor": "rgba(0,0,0,0.54)",
                    "lineColor": "rgba(0,0,0,0.54)", "splitLinesColor": "rgba(0,0,0,0.12)"},
                "yAxes": yaxes,
                "showLegend": True,
                "legendLabelFont": {"family": "Roboto", "size": 12, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "16px"},
                "legendLabelColor": "rgba(0,0,0,0.76)",
                "legendConfig": {"direction": "row", "position": "bottom", "sortDataKeys": False,
                    "showMin": False, "showMax": False, "showAvg": True, "showTotal": False, "showLatest": True},
                "showTooltip": True, "tooltipTrigger": "axis",
                "tooltipValueFont": {"family": "Roboto", "size": 12, "sizeUnit": "px", "style": "normal", "weight": "500", "lineHeight": "16px"},
                "tooltipValueColor": "rgba(0,0,0,0.76)",
                "tooltipShowDate": True,
                "tooltipDateFormat": {"format": None, "lastUpdateAgo": False, "custom": False, "auto": True},
                "tooltipDateFont": {"family": "Roboto", "size": 11, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "16px"},
                "tooltipDateColor": "rgba(0,0,0,0.76)",
                "tooltipBackgroundColor": "rgba(255,255,255,0.76)", "tooltipBackgroundBlur": 4,
                "animation": {"animation": True, "animationThreshold": 2000, "animationDuration": 500,
                    "animationEasing": "cubicOut", "animationDelay": 0, "animationDurationUpdate": 300,
                    "animationEasingUpdate": "cubicOut", "animationDelayUpdate": 0},
                "background": {"type": "color", "color": "#fff",
                    "overlay": {"enabled": False, "color": "rgba(255,255,255,0.72)", "blur": 3}},
                "padding": "12px", "dataZoom": True, "stack": False, "thresholds": [],
            }
        }
    }


def build_kpi(key, label, units, icon, color, dec=1, alias=None, key_type="timeseries",
              post_func=None):
    """Horizontal value card KPI."""
    if alias is None:
        alias = ALIAS_WELL
    dk_settings = {}
    if key_type == "attribute":
        dk_settings["dataKeyType"] = "server"
    dk = make_dk(key, key_type, label, color, settings=dk_settings, post_func=post_func)

    return {
        "typeFullFqn": "system.cards.horizontal_value_card", "type": "latest",
        "sizeX": 4, "sizeY": 3,
        "config": {
            "datasources": [make_ds(alias, [dk])],
            "settings": {
                "labelPosition": "top", "layout": "horizontal", "showLabel": True,
                "labelFont": {"family": "Roboto", "size": 14, "sizeUnit": "px", "style": "normal", "weight": "500"},
                "labelColor": {"type": "constant", "color": "rgba(0,0,0,0.54)"},
                "showIcon": True, "iconSize": 32, "iconSizeUnit": "px", "icon": icon,
                "iconColor": {"type": "constant", "color": color},
                "valueFont": {"size": 28, "sizeUnit": "px", "family": "Roboto", "weight": "500", "style": "normal"},
                "valueColor": {"type": "constant", "color": "rgba(0,0,0,0.87)"},
                "showDate": True, "dateFormat": {"format": None, "lastUpdateAgo": True, "custom": False},
                "dateFont": {"family": "Roboto", "size": 12, "sizeUnit": "px", "style": "normal", "weight": "400"},
                "dateColor": {"type": "constant", "color": "rgba(0,0,0,0.38)"},
                "background": {"type": "color", "color": "#fff", "overlay": {"enabled": False}},
                "autoScale": True, "padding": "8px",
            },
            "showTitle": False, "backgroundColor": "rgba(0,0,0,0)", "padding": "0px",
            "borderRadius": "8px", "dropShadow": True, "units": units, "decimals": dec,
            "enableFullscreen": False, "enableDataExport": False, "configMode": "basic",
        }
    }


def build_markdown(html, alias=None, data_keys=None, use_func=False, func_code=None):
    """Markdown/HTML Value Card with full TB-compatible datasource."""
    if alias is None:
        alias = ALIAS_WELL
    ds = []
    if data_keys:
        dks = []
        for dk_spec in data_keys:
            dk = make_dk(
                dk_spec["name"],
                dk_spec.get("type", "attribute"),
                dk_spec.get("label", dk_spec["name"]),
                dk_spec.get("color", "#2196f3"),
            )
            dks.append(dk)
        ds = [make_ds(alias, dks)]

    settings = {}
    if use_func and func_code:
        settings["useMarkdownTextFunction"] = True
        settings["markdownTextFunction"] = func_code
    else:
        settings["useMarkdownTextFunction"] = False
        settings["markdownTextPattern"] = html

    return {
        "typeFullFqn": "system.cards.markdown_card", "type": "latest",
        "sizeX": 24, "sizeY": 2,
        "config": {
            "datasources": ds,
            "showTitle": False, "backgroundColor": "rgba(0,0,0,0)", "padding": "0px",
            "settings": settings,
            "dropShadow": False, "enableFullscreen": False, "borderRadius": "8px",
        }
    }


def build_back():
    return {
        "typeFullFqn": "system.action_button", "type": "latest", "sizeX": 3, "sizeY": 2,
        "config": {
            "datasources": [], "showTitle": False,
            "backgroundColor": "#FFFFFF01", "color": "rgba(0,0,0,0.87)", "padding": "0px",
            "settings": {
                "activatedState": {"action": "DO_NOTHING", "defaultValue": False,
                    "getAttribute": {"key": "state", "scope": None}, "getTimeSeries": {"key": "state"},
                    "dataToValue": {"type": "NONE", "compareToValue": True, "dataToValueFunction": "return data;"}},
                "disabledState": {"action": "DO_NOTHING", "defaultValue": False,
                    "getAttribute": {"key": "state", "scope": None}, "getTimeSeries": {"key": "state"},
                    "dataToValue": {"type": "NONE", "compareToValue": True, "dataToValueFunction": "return data;"}},
                "appearance": {
                    "type": "outlined", "showLabel": True, "label": "Volver",
                    "showIcon": True, "icon": "arrow_back", "iconSize": 20, "iconSizeUnit": "px",
                    "mainColor": "#666", "backgroundColor": "#FFF", "autoScale": True,
                    "customStyle": {"enabled": None, "hovered": None, "pressed": None, "activated": None, "disabled": None}
                }
            },
            "title": "", "dropShadow": False, "borderRadius": "8px", "configMode": "advanced",
            "actions": {"click": [{
                "id": uid(), "name": "onClick", "icon": "arrow_back",
                "type": "openDashboardState", "targetDashboardStateId": "default",
                "setEntityId": False, "openRightLayout": False,
                "openInSeparateDialog": False, "openInPopover": False,
            }]},
        }
    }


def build_entities_table(title, columns, alias, sort_col, sort_order="DESC", page_size=15,
                         show_pagination=True, row_click_state=None, row_click_js=None,
                         cell_styles=None, cell_contents=None):
    """Professional entities table widget with full TB-compatible structure."""
    dkeys = []
    for col in columns:
        settings = {}
        dtype = col.get("type", "attribute")
        if dtype == "attribute":
            settings["dataKeyType"] = "server"
        if cell_styles and col["name"] in cell_styles:
            settings["useCellStyleFunction"] = True
            settings["cellStyleFunction"] = cell_styles[col["name"]]
        if cell_contents and col["name"] in cell_contents:
            settings["useCellContentFunction"] = True
            settings["cellContentFunction"] = cell_contents[col["name"]]
        dk = make_dk(col["name"], dtype, col.get("label", col["name"]), col.get("color", "#2196f3"), settings=settings)
        dkeys.append(dk)

    actions = {}
    if row_click_js:
        _action_base = {
            "name": "Ver Detalle", "type": "custom",
            "customFunction": row_click_js,
            "setEntityId": True, "stateEntityParamName": None,
            "openRightLayout": False, "openInSeparateDialog": False,
            "openInPopover": False,
        }
        actions["headerButton"] = []
        actions["rowClick"] = [{"id": uid(), "icon": "more_horiz", **_action_base}]
        actions["actionCellButton"] = [{"id": uid(), "icon": "play_arrow", **_action_base}]
    elif row_click_state:
        actions["rowClick"] = [{
            "id": uid(), "name": "Ver Detalle", "icon": "more_horiz",
            "type": "openDashboardState", "targetDashboardStateId": row_click_state,
            "setEntityId": True, "stateEntityParamName": None,
            "openRightLayout": False, "openInSeparateDialog": False, "openInPopover": False,
        }]

    return {
        "typeFullFqn": "system.cards.entities_table", "type": "latest",
        "config": {
            "datasources": [make_ds(alias, dkeys)],
            "showTitle": True, "title": title,
            "backgroundColor": "rgba(0,0,0,0)", "color": "rgba(0,0,0,0.87)",
            "padding": "0px", "borderRadius": "8px", "dropShadow": True,
            "titleStyle": {"fontSize": "16px", "fontWeight": "500"},
            "titleFont": {"size": 16, "sizeUnit": "px", "family": "Roboto", "weight": "500"},
            "titleColor": "rgba(0,0,0,0.87)",
            "enableFullscreen": True, "enableDataExport": True,
            "settings": {
                "enableStickyHeader": True, "enableStickyAction": True,
                "displayPagination": show_pagination, "defaultPageSize": page_size,
                "defaultSortOrder": f"-{sort_col}" if sort_order == "DESC" else sort_col,
                "enableSearch": show_pagination, "enableSelectColumnDisplay": True,
                "reserveSpaceForHiddenAction": True,
                "displayEntityName": False, "displayEntityLabel": False, "displayEntityType": False,
            },
            "actions": actions,
        }
    }


# -- Cell Style & Content Functions -------------------------------------------

CELL_STYLE_HEALTH = (
    "var score = Number(value);"
    "if (isNaN(score) || score === 0) return {color: '#9FA6B4', fontStyle: 'italic'};"
    "if (score >= 80) return {backgroundColor: '#E8F5E9', color: '#4CAF50', fontWeight: '600', borderRadius: '4px', padding: '2px 8px'};"
    "if (score >= 60) return {backgroundColor: '#FFF3E0', color: '#FF9800', fontWeight: '600', borderRadius: '4px', padding: '2px 8px'};"
    "return {backgroundColor: '#FFEBEE', color: '#F44336', fontWeight: '600', borderRadius: '4px', padding: '2px 8px'};"
)

CELL_STYLE_STATUS = (
    "if (!value || value === '' || value === '0') return {color: '#9FA6B4', fontStyle: 'italic'};"
    "var styles = {"
    "'optimized': {backgroundColor:'#E8F5E9',color:'#4CAF50',fontWeight:'600',borderRadius:'4px',padding:'2px 8px'},"
    "'optimal': {backgroundColor:'#E8F5E9',color:'#4CAF50',fontWeight:'600',borderRadius:'4px',padding:'2px 8px'},"
    "'pending': {backgroundColor:'#FFF3E0',color:'#FF9800',fontWeight:'600',borderRadius:'4px',padding:'2px 8px'},"
    "'error': {backgroundColor:'#FFEBEE',color:'#F44336',fontWeight:'600',borderRadius:'4px',padding:'2px 8px'},"
    "'not_analyzed': {color:'#9FA6B4',fontStyle:'italic'},"
    "'suboptimal': {backgroundColor:'#FFEBEE',color:'#F44336',fontWeight:'600',borderRadius:'4px',padding:'2px 8px'},"
    "'critical': {backgroundColor:'#B71C1C',color:'#FFFFFF',fontWeight:'700',borderRadius:'4px',padding:'2px 8px'}"
    "}; return styles[value] || {color: '#4B535B'};"
)

CELL_STYLE_ANOMALY = (
    "var score = Number(value);"
    "if (isNaN(score) || score === 0) return {color: '#9FA6B4'};"
    "if (score >= 0.8) return {backgroundColor: '#FFEBEE', color: '#F44336', fontWeight: '700', borderRadius: '4px', padding: '2px 8px'};"
    "if (score >= 0.5) return {backgroundColor: '#FFF3E0', color: '#FF9800', fontWeight: '600', borderRadius: '4px', padding: '2px 8px'};"
    "return {color: '#4CAF50'};"
)

CELL_CONTENT_ACTION = (
    "if (!value || value === '' || value === '0' || value === 0) "
    "return '<span style=\"color:#9FA6B4; font-style: italic;\">Sin recomendacion</span>';"
    "var icons = {"
    "'increase_frequency': '<span style=\"color:#4CAF50;\">&#9650; Aumentar frecuencia</span>',"
    "'increase_vsd_frequency': '<span style=\"color:#4CAF50;\">&#9650; Aumentar VSD Hz</span>',"
    "'decrease_frequency': '<span style=\"color:#FF9800;\">&#9660; Reducir frecuencia</span>',"
    "'decrease_vsd_frequency': '<span style=\"color:#FF9800;\">&#9660; Reducir VSD Hz</span>',"
    "'increase_spm': '<span style=\"color:#4CAF50;\">&#9650; Aumentar SPM</span>',"
    "'decrease_spm': '<span style=\"color:#FF9800;\">&#9660; Reducir SPM</span>',"
    "'increase_injection': '<span style=\"color:#4CAF50;\">&#9650; Aumentar inyeccion</span>',"
    "'decrease_injection': '<span style=\"color:#FF9800;\">&#9660; Reducir inyeccion</span>',"
    "'adjust_gas_injection': '<span style=\"color:#2196F3;\">&#128260; Ajustar inyeccion GL</span>',"
    "'increase_speed': '<span style=\"color:#4CAF50;\">&#9650; Aumentar RPM</span>',"
    "'increase_rpm': '<span style=\"color:#4CAF50;\">&#9650; Aumentar RPM</span>',"
    "'decrease_speed': '<span style=\"color:#FF9800;\">&#9660; Reducir RPM</span>',"
    "'decrease_rpm': '<span style=\"color:#FF9800;\">&#9660; Reducir RPM</span>',"
    "'workover': '<span style=\"color:#F44336;\">&#128295; Workover requerido</span>',"
    "'review_gaslift': '<span style=\"color:#2196F3;\">&#128260; Revisar inyeccion GL</span>',"
    "'monitor': '<span style=\"color:#9FA6B4;\">&#128065; Monitorear</span>',"
    "'no_action': '<span style=\"color:#4CAF50;\">&#10004; Sin accion necesaria</span>'"
    "}; return icons[value] || '<span style=\"color:#305680;\">' + value + '</span>';"
)

CELL_CONTENT_LIFT_TYPE = (
    "var colors = {'ESP':'#4CAF50','SRP':'#2196F3','PCP':'#FF9800','gas_lift':'#9C27B0','Gas Lift':'#9C27B0'};"
    "var labels = {'ESP':'ESP','SRP':'SRP','PCP':'PCP','gas_lift':'Gas Lift','Gas Lift':'Gas Lift'};"
    "var c = colors[value] || '#607D8B'; var l = labels[value] || value;"
    "return '<div style=\"display:inline-block;padding:3px 10px;border-radius:12px;background:'+c+';color:#fff;"
    "font-size:11px;font-weight:600;letter-spacing:0.5px;\">'+l+'</div>';"
)

CELL_STYLE_GAIN = (
    "var v = Number(value);"
    "if (isNaN(v) || v === 0) return {color: '#9FA6B4'};"
    "if (v > 100) return {color: '#4CAF50', fontWeight: '700'};"
    "if (v > 0) return {color: '#4CAF50', fontWeight: '600'};"
    "return {color: '#F44336', fontWeight: '600'};"
)


# -- PostProcessing functions for KPI aggregation -----------------------------

POST_FUNC_SUM = (
    "var result = 0; var count = 0;"
    "if (data && data.length) {"
    "  for (var i = 0; i < data.length; i++) {"
    "    var v = Number(data[i][1]);"
    "    if (!isNaN(v)) { result += v; count++; }"
    "  }"
    "}"
    "return count > 0 ? result : 'N/A';"
)

POST_FUNC_AVG = (
    "var result = 0; var count = 0;"
    "if (data && data.length) {"
    "  for (var i = 0; i < data.length; i++) {"
    "    var v = Number(data[i][1]);"
    "    if (!isNaN(v) && v > 0) { result += v; count++; }"
    "  }"
    "}"
    "return count > 0 ? (result / count).toFixed(1) : 'N/A';"
)

POST_FUNC_MIN = (
    "var result = Infinity; var count = 0;"
    "if (data && data.length) {"
    "  for (var i = 0; i < data.length; i++) {"
    "    var v = Number(data[i][1]);"
    "    if (!isNaN(v) && v > 0) { result = Math.min(result, v); count++; }"
    "  }"
    "}"
    "return count > 0 ? result : 'N/A';"
)

POST_FUNC_COUNT_ANOMALIES = (
    "var count = 0;"
    "if (data && data.length) {"
    "  for (var i = 0; i < data.length; i++) {"
    "    var v = Number(data[i][1]);"
    "    if (!isNaN(v) && v >= 0.5) count++;"
    "  }"
    "}"
    "return count;"
)


# -- HTML Templates -----------------------------------------------------------

# --- HEADER with cycle indicators ---
HEADER_FUNC = (
    "var lastRun = data['opt_last_run'] || '--';"
    "var ago = '--';"
    "if (lastRun && lastRun !== '--') {"
    "  try {"
    "    var d = new Date(lastRun);"
    "    var now = new Date();"
    "    var diff = Math.floor((now - d) / 60000);"
    "    if (diff < 60) ago = diff + ' min';"
    "    else if (diff < 1440) ago = Math.floor(diff/60) + ' h';"
    "    else ago = Math.floor(diff/1440) + ' d';"
    "  } catch(e) { ago = '--'; }"
    "}"
    "return '<div style=\"display:flex;justify-content:space-between;align-items:center;padding:8px 16px;\">"
    "<div><h2 style=\"margin:0;color:#305680;font-weight:700;\">Centro de Optimizacion</h2>"
    "<span style=\"color:#9FA6B4;font-size:13px;\">Analisis y recomendaciones del servicio de optimizacion</span></div>"
    "<div style=\"display:flex;gap:8px;align-items:center;\">"
    "<div style=\"text-align:right;margin-right:12px;\"><div style=\"font-size:10px;color:#9FA6B4;text-transform:uppercase;\">Ultima ejecucion</div>"
    "<div style=\"font-size:14px;font-weight:600;color:#305680;\">hace '+ago+'</div></div>"
    "<div style=\"display:flex;gap:6px;\">"
    "<div style=\"padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#E8F5E9;color:#4CAF50;\">RT 5min</div>"
    "<div style=\"padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#E3F2FD;color:#2196F3;\">Horario</div>"
    "<div style=\"padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#FFF3E0;color:#FF9800;\">Diario 6AM</div>"
    "<div style=\"padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#F3E5F5;color:#9C27B0;\">Semanal Lun</div>"
    "<div style=\"padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#EFEBE9;color:#795548;\">Mensual D1</div>"
    "</div></div></div>';"
)

# --- Dynamic Health Distribution ---
HEALTH_DIST_FUNC = (
    "var good=0,med=0,low=0,crit=0,total=0;"
    "for (var i=0; i<data.length; i++) {"
    "  var v = Number(data[i]['opt_well_health_score'])||0;"
    "  if (v > 0) {"
    "    total++;"
    "    if (v >= 80) good++;"
    "    else if (v >= 60) med++;"
    "    else if (v >= 40) low++;"
    "    else crit++;"
    "  }"
    "}"
    "return '<div style=\"padding:16px;\">"
    "<h3 style=\"color:#305680;margin:0 0 16px 0;font-size:15px;font-weight:600;\">Distribucion de Salud del Campo</h3>"
    "<div style=\"display:flex;gap:12px;\">"
    "<div style=\"flex:1;text-align:center;padding:16px;background:#E8F5E9;border-radius:8px;\">"
    "<div style=\"font-size:36px;font-weight:700;color:#4CAF50;\">'+good+'</div>"
    "<div style=\"font-size:12px;color:#4CAF50;margin-top:4px;font-weight:600;\">OPTIMO (&gt;80)</div></div>"
    "<div style=\"flex:1;text-align:center;padding:16px;background:#FFF3E0;border-radius:8px;\">"
    "<div style=\"font-size:36px;font-weight:700;color:#FF9800;\">'+med+'</div>"
    "<div style=\"font-size:12px;color:#FF9800;margin-top:4px;font-weight:600;\">SUBOPTIMO (60-80)</div></div>"
    "<div style=\"flex:1;text-align:center;padding:16px;background:#FFF9C4;border-radius:8px;\">"
    "<div style=\"font-size:36px;font-weight:700;color:#FFC107;\">'+low+'</div>"
    "<div style=\"font-size:12px;color:#FFC107;margin-top:4px;font-weight:600;\">ATENCION (40-60)</div></div>"
    "<div style=\"flex:1;text-align:center;padding:16px;background:#FFEBEE;border-radius:8px;\">"
    "<div style=\"font-size:36px;font-weight:700;color:#F44336;\">'+crit+'</div>"
    "<div style=\"font-size:12px;color:#F44336;margin-top:4px;font-weight:600;\">CRITICO (&lt;40)</div></div>"
    "</div>"
    "<div style=\"margin-top:10px;font-size:11px;color:#9FA6B4;text-align:center;\">Total: '+total+' pozos evaluados</div>"
    "</div>';"
)

# --- Field Optimization (Gas Allocation + Constraints) ---
FIELD_OPT_FUNC = (
    "return '<div style=\"padding:16px;\">"
    "<h3 style=\"color:#305680;margin:0 0 12px 0;font-size:15px;font-weight:600;\">Optimizacion de Campo</h3>"
    "<div style=\"display:flex;gap:12px;margin-bottom:12px;\">"
    "<div style=\"flex:1;padding:12px;background:#F5F7FA;border-radius:8px;border-left:4px solid #9C27B0;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Asignacion Gas (Equal-Slope)</div>"
    "<div style=\"font-size:14px;font-weight:500;color:#305680;margin-top:4px;\">Pozos GL con inyeccion activa</div>"
    "<div style=\"font-size:11px;color:#9FA6B4;margin-top:4px;\">Metodo: Pendiente igual para maximizar produccion marginal</div></div>"
    "<div style=\"flex:1;padding:12px;background:#F5F7FA;border-radius:8px;border-left:4px solid #2196F3;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Restricciones Activas</div>"
    "<div style=\"display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;\">"
    "<div style=\"padding:3px 8px;border-radius:12px;background:#E3F2FD;color:#2196F3;font-size:11px;font-weight:600;\">Separador</div>"
    "<div style=\"padding:3px 8px;border-radius:12px;background:#F3E5F5;color:#9C27B0;font-size:11px;font-weight:600;\">Gas Disponible</div>"
    "<div style=\"padding:3px 8px;border-radius:12px;background:#FFF3E0;color:#FF9800;font-size:11px;font-weight:600;\">Potencia Electrica</div>"
    "<div style=\"padding:3px 8px;border-radius:12px;background:#FFEBEE;color:#F44336;font-size:11px;font-weight:600;\">Manejo de Agua</div>"
    "</div></div></div>"
    "<div style=\"padding:12px;background:#FAFAFA;border-radius:8px;color:#9FA6B4;text-align:center;font-size:12px;\">"
    "El servicio evalua restricciones de campo en cada ciclo horario y ajusta recomendaciones.</div>"
    "</div>';"
)

# --- Action Card ---
ACTION_CARD_FUNC = (
    "var action = data['opt_recommended_action'] || 'Sin datos';"
    "var detail = data['opt_recommended_action_detail'] || '';"
    "var decline = data['opt_decline_rate_monthly_percent'] || '0';"
    "var actionLabels = {"
    "  'increase_spm': '&#9650; Aumentar SPM', 'decrease_spm': '&#9660; Reducir SPM',"
    "  'increase_vsd_frequency': '&#9650; Aumentar Frecuencia VSD', 'decrease_vsd_frequency': '&#9660; Reducir Frecuencia VSD',"
    "  'increase_frequency': '&#9650; Aumentar Frecuencia', 'decrease_frequency': '&#9660; Reducir Frecuencia',"
    "  'adjust_gas_injection': '&#128260; Ajustar Inyeccion Gas', 'increase_injection': '&#9650; Aumentar Inyeccion',"
    "  'decrease_injection': '&#9660; Reducir Inyeccion',"
    "  'increase_rpm': '&#9650; Aumentar RPM', 'decrease_rpm': '&#9660; Reducir RPM',"
    "  'increase_speed': '&#9650; Aumentar RPM', 'decrease_speed': '&#9660; Reducir RPM',"
    "  'workover': '&#128295; Workover', 'monitor': '&#128065; Monitorear',"
    "  'no_action': '&#10004; Sin accion necesaria'"
    "};"
    "var actionLabel = actionLabels[action] || action;"
    "return '<div style=\"display:flex;gap:16px;padding:8px 16px;\">"
    "<div style=\"flex:2;padding:16px;background:#E3F2FD;border-radius:8px;border-left:4px solid #2196F3;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;\">Accion Recomendada</div>"
    "<div style=\"font-size:16px;font-weight:600;color:#305680;\">'+actionLabel+'</div>"
    "<div style=\"font-size:12px;color:#4B535B;margin-top:6px;\">'+detail+'</div></div>"
    "<div style=\"flex:1;padding:16px;background:#FFF3E0;border-radius:8px;border-left:4px solid #FF9800;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;margin-bottom:4px;\">Declive Mensual</div>"
    "<div style=\"font-size:24px;font-weight:700;color:#FF9800;\">'+decline+'%</div></div></div>';"
)


# -- Lift-Type Specific Optimization Cards (complete with all variables) ------

ESP_OPT_FUNC = (
    "var freq = data['opt_esp_current_freq_hz'] || '--';"
    "var recVal = data['opt_recommended_value'] || '--';"
    "var pctBep = data['opt_esp_pct_bep'] || '--';"
    "var head = data['opt_esp_head_generated_ft'] || '--';"
    "var temp = data['opt_esp_motor_temp_f'] || '--';"
    "var vib = data['opt_esp_vibration_ips'] || '--';"
    "var power = data['opt_esp_power_kw'] || '--';"
    "return '<div style=\"padding:12px 16px;\">"
    "<h3 style=\"color:#305680;margin:0 0 12px 0;font-weight:600;\">Optimizacion ESP</h3>"
    "<div style=\"display:flex;gap:16px;margin-bottom:12px;\">"
    "<div style=\"flex:1;padding:16px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Frecuencia Actual</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#305680;\">'+Number(freq).toFixed(1)+' <span style=\"font-size:14px;\">Hz</span></div></div>"
    "<div style=\"flex:0 0 60px;display:flex;align-items:center;justify-content:center;\">"
    "<div style=\"font-size:24px;color:#4CAF50;\">&#10140;</div></div>"
    "<div style=\"flex:1;padding:16px;background:#E8F5E9;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#4CAF50;text-transform:uppercase;\">Frecuencia Recomendada</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#4CAF50;\">'+Number(recVal).toFixed(1)+' <span style=\"font-size:14px;\">Hz</span></div></div></div>"
    "<div style=\"display:flex;gap:8px;\">"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">% BEP</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(pctBep).toFixed(0)+'%</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Head</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(head).toFixed(0)+' ft</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Temp Motor</div><div style=\"font-size:14px;font-weight:600;color:'+(Number(temp)>200?'#F44336':'#305680')+';\">'+Number(temp).toFixed(0)+' F</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Vibracion</div><div style=\"font-size:14px;font-weight:600;color:'+(Number(vib)>1.5?'#F44336':'#305680')+';\">'+Number(vib).toFixed(2)+' ips</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Potencia</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(power).toFixed(1)+' kW</div></div>"
    "</div></div>';"
)

SRP_OPT_FUNC = (
    "var spm = data['opt_srp_spm'] || '--';"
    "var recSpm = data['opt_srp_recommended_spm'] || data['opt_recommended_value'] || '--';"
    "var fillage = data['opt_srp_fillage_pct'] || '--';"
    "var pumpSt = data['opt_srp_pump_status'] || '--';"
    "var disp = data['opt_srp_displacement_bpd'] || '--';"
    "var loadMax = data['opt_srp_load_max_lbs'] || '--';"
    "var loadMin = data['opt_srp_load_min_lbs'] || '--';"
    "var fluidLvl = data['opt_srp_fluid_level_ft'] || '--';"
    "return '<div style=\"padding:12px 16px;\">"
    "<h3 style=\"color:#305680;margin:0 0 12px 0;font-weight:600;\">Optimizacion SRP (Bombeo Mecanico)</h3>"
    "<div style=\"display:flex;gap:16px;margin-bottom:12px;\">"
    "<div style=\"flex:1;padding:16px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">SPM Actual</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#305680;\">'+Number(spm).toFixed(1)+' <span style=\"font-size:14px;\">SPM</span></div></div>"
    "<div style=\"flex:0 0 60px;display:flex;align-items:center;justify-content:center;\">"
    "<div style=\"font-size:24px;color:#4CAF50;\">&#10140;</div></div>"
    "<div style=\"flex:1;padding:16px;background:#E8F5E9;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#4CAF50;text-transform:uppercase;\">SPM Recomendado</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#4CAF50;\">'+Number(recSpm).toFixed(1)+' <span style=\"font-size:14px;\">SPM</span></div></div></div>"
    "<div style=\"display:flex;gap:8px;\">"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Fillage</div><div style=\"font-size:14px;font-weight:600;color:'+(Number(fillage)<60||Number(fillage)>95?'#FF9800':'#4CAF50')+';\">'+Number(fillage).toFixed(0)+'%</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Bomba</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+pumpSt+'</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Desplazam.</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(disp).toFixed(0)+' BPD</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Carga Max</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(loadMax).toFixed(0)+' lbs</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Nivel Fluido</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(fluidLvl).toFixed(0)+' ft</div></div>"
    "</div></div>';"
)

GL_OPT_FUNC = (
    "var injRate = data['opt_gl_injection_rate_mscfd'] || 0;"
    "var optRate = data['opt_gl_optimal_rate_mscfd'] || data['opt_recommended_value'] || '--';"
    "var heading = data['opt_gl_heading_detected'];"
    "var injPres = data['opt_gl_injection_pressure_psi'] || '--';"
    "var headingStr = heading === true || heading === 'true' ? '<span style=\"color:#F44336;font-weight:700;\">DETECTADO</span>' : '<span style=\"color:#4CAF50;\">No detectado</span>';"
    "return '<div style=\"padding:12px 16px;\">"
    "<h3 style=\"color:#305680;margin:0 0 12px 0;font-weight:600;\">Optimizacion Gas Lift</h3>"
    "<div style=\"display:flex;gap:16px;margin-bottom:12px;\">"
    "<div style=\"flex:1;padding:16px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Inyeccion Actual</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#305680;\">'+Number(injRate).toFixed(0)+' <span style=\"font-size:14px;\">MSCFD</span></div></div>"
    "<div style=\"flex:0 0 60px;display:flex;align-items:center;justify-content:center;\">"
    "<div style=\"font-size:24px;color:#4CAF50;\">&#10140;</div></div>"
    "<div style=\"flex:1;padding:16px;background:#E8F5E9;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#4CAF50;text-transform:uppercase;\">Inyeccion Optima</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#4CAF50;\">'+Number(optRate).toFixed(0)+' <span style=\"font-size:14px;\">MSCFD</span></div></div></div>"
    "<div style=\"display:flex;gap:8px;\">"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Heading</div><div style=\"font-size:14px;\">'+headingStr+'</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Presion Iny.</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(injPres).toFixed(0)+' psi</div></div>"
    "</div></div>';"
)

PCP_OPT_FUNC = (
    "var rpm = data['opt_pcp_rpm'] || '--';"
    "var recRpm = data['opt_pcp_recommended_rpm'] || data['opt_recommended_value'] || '--';"
    "var torque = data['opt_pcp_torque_ft_lbs'] || 0;"
    "var torquePct = data['opt_pcp_torque_pct_max'] || 0;"
    "var volEff = data['opt_pcp_vol_efficiency_pct'] || 0;"
    "var wear = data['opt_pcp_wear_indicator'] || 0;"
    "var power = data['opt_pcp_power_kw'] || 0;"
    "return '<div style=\"padding:12px 16px;\">"
    "<h3 style=\"color:#305680;margin:0 0 12px 0;font-weight:600;\">Optimizacion PCP (Cavidad Progresiva)</h3>"
    "<div style=\"display:flex;gap:16px;margin-bottom:12px;\">"
    "<div style=\"flex:1;padding:16px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">RPM Actual</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#305680;\">'+Number(rpm).toFixed(0)+' <span style=\"font-size:14px;\">RPM</span></div></div>"
    "<div style=\"flex:0 0 60px;display:flex;align-items:center;justify-content:center;\">"
    "<div style=\"font-size:24px;color:#4CAF50;\">&#10140;</div></div>"
    "<div style=\"flex:1;padding:16px;background:#E8F5E9;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:11px;color:#4CAF50;text-transform:uppercase;\">RPM Recomendada</div>"
    "<div style=\"font-size:28px;font-weight:700;color:#4CAF50;\">'+Number(recRpm).toFixed(0)+' <span style=\"font-size:14px;\">RPM</span></div></div></div>"
    "<div style=\"display:flex;gap:8px;\">"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Torque</div><div style=\"font-size:14px;font-weight:600;color:'+(Number(torquePct)>80?'#F44336':'#305680')+';\">'+Number(torque).toFixed(0)+' ft-lbs ('+Number(torquePct).toFixed(0)+'%)</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Efic. Volum.</div><div style=\"font-size:14px;font-weight:600;color:'+(Number(volEff)<70?'#FF9800':'#4CAF50')+';\">'+Number(volEff).toFixed(0)+'%</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Desgaste</div><div style=\"font-size:14px;font-weight:600;color:'+(Number(wear)>0.7?'#F44336':Number(wear)>0.4?'#FF9800':'#4CAF50')+';\">'+Number(wear).toFixed(2)+'</div></div>"
    "<div style=\"flex:1;padding:8px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
    "<div style=\"font-size:10px;color:#9FA6B4;\">Potencia</div><div style=\"font-size:14px;font-weight:600;color:#305680;\">'+Number(power).toFixed(1)+' kW</div></div>"
    "</div></div>';"
)


# -- OPT_WELL_TYPES: Per-type detail state configuration ----------------------

OPT_WELL_TYPES = {
    "ESP": {
        "state_id": "opt_esp", "color": "#4CAF50", "icon": "bolt",
        "label": "Bombeo Electrosumergible",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 0, "type": "timeseries"},
            {"key": "frequency_hz", "label": "Frecuencia VSD", "units": "Hz", "icon": "tune", "color": "#9C27B0", "dec": 1, "type": "timeseries"},
            {"key": "opt_recommended_rate_bpd", "label": "Prod Recomendada", "units": "BPD", "icon": "trending_up", "color": "#2196F3", "dec": 0, "type": "attribute"},
            {"key": "opt_potential_gain_bpd", "label": "Ganancia", "units": "BPD", "icon": "add_circle", "color": "#00C853", "dec": 0, "type": "attribute"},
            {"key": "opt_well_health_score", "label": "Salud", "units": "%", "icon": "favorite", "color": "#FF5722", "dec": 0, "type": "attribute"},
            {"key": "opt_efficiency_pct", "label": "Eficiencia", "units": "%", "icon": "speed", "color": "#FF9800", "dec": 1, "type": "attribute"},
        ],
        "main_chart": [
            {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
            {"key": "frequency_hz", "label": "Frecuencia VSD", "u": "Hz", "c": "#9C27B0", "y": "right"},
        ],
        "secondary_chart": [
            {"key": "intake_pressure_psi", "label": "P. Intake", "u": "PSI", "c": "#2196F3", "y": "left"},
            {"key": "discharge_pressure_psi", "label": "P. Descarga", "u": "PSI", "c": "#00BCD4", "y": "left"},
            {"key": "motor_temperature_f", "label": "Temp Motor", "u": "F", "c": "#F44336", "y": "right"},
        ],
        "opt_card_keys": [
            "opt_esp_current_freq_hz", "opt_recommended_value", "opt_esp_pct_bep",
            "opt_esp_head_generated_ft", "opt_esp_motor_temp_f", "opt_esp_vibration_ips", "opt_esp_power_kw",
        ],
        "diag_label": "Diagnostico ESP",
        "diag_items": [
            ("Temp Motor", "opt_esp_motor_temp_f", "F", "#F44336", 200),
            ("Vibracion", "opt_esp_vibration_ips", "IPS", "#9C27B0", 1.5),
            ("% BEP", "opt_esp_pct_bep", "%", "#2196F3", None),
            ("Frecuencia Actual", "opt_esp_current_freq_hz", "Hz", "#305680", None),
            ("Head Generado", "opt_esp_head_generated_ft", "ft", "#305680", None),
            ("Potencia", "opt_esp_power_kw", "kW", "#305680", None),
        ],
    },
    "SRP": {
        "state_id": "opt_srp", "color": "#2196F3", "icon": "architecture",
        "label": "Bombeo Mecanico",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 0, "type": "timeseries"},
            {"key": "spm", "label": "SPM", "units": "spm", "icon": "speed", "color": "#2196F3", "dec": 1, "type": "timeseries"},
            {"key": "load_lb", "label": "Carga", "units": "lb", "icon": "fitness_center", "color": "#F44336", "dec": 0, "type": "timeseries"},
            {"key": "opt_recommended_rate_bpd", "label": "Prod Recomendada", "units": "BPD", "icon": "trending_up", "color": "#00C853", "dec": 0, "type": "attribute"},
            {"key": "opt_well_health_score", "label": "Salud", "units": "%", "icon": "favorite", "color": "#FF5722", "dec": 0, "type": "attribute"},
            {"key": "opt_potential_gain_bpd", "label": "Ganancia", "units": "BPD", "icon": "add_circle", "color": "#4CAF50", "dec": 0, "type": "attribute"},
        ],
        "main_chart": [
            {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
            {"key": "spm", "label": "SPM", "u": "spm", "c": "#2196F3", "y": "right"},
        ],
        "secondary_chart": [
            {"key": "load_lb", "label": "Carga", "u": "lb", "c": "#F44336", "y": "left"},
            {"key": "pump_fillage_pct", "label": "Llenado", "u": "%", "c": "#00BCD4", "y": "right"},
            {"key": "tubing_pressure_psi", "label": "P. Tubing", "u": "PSI", "c": "#FF9800", "y": "right"},
        ],
        "opt_card_keys": [
            "opt_srp_spm", "opt_srp_recommended_spm", "opt_recommended_value",
            "opt_srp_fillage_pct", "opt_srp_pump_status", "opt_srp_displacement_bpd",
            "opt_srp_load_max_lbs", "opt_srp_fluid_level_ft",
        ],
        "diag_label": "Diagnostico SRP",
        "diag_items": [
            ("Fillage", "opt_srp_fillage_pct", "%", "#00BCD4", None),
            ("Estado Bomba", "opt_srp_pump_status", "", "#305680", None),
            ("SPM Actual", "opt_srp_spm", "spm", "#2196F3", None),
            ("SPM Recomendado", "opt_srp_recommended_spm", "spm", "#4CAF50", None),
            ("Carga Max", "opt_srp_load_max_lbs", "lbs", "#F44336", None),
            ("Nivel Fluido", "opt_srp_fluid_level_ft", "ft", "#305680", None),
        ],
    },
    "PCP": {
        "state_id": "opt_pcp", "color": "#FF9800", "icon": "settings",
        "label": "Bombeo Cavidad Progresiva",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 0, "type": "timeseries"},
            {"key": "speed_rpm", "label": "RPM", "units": "rpm", "icon": "speed", "color": "#2196F3", "dec": 0, "type": "timeseries"},
            {"key": "motor_torque_ftlb", "label": "Torque", "units": "ft-lb", "icon": "rotate_right", "color": "#F44336", "dec": 1, "type": "timeseries"},
            {"key": "opt_recommended_rate_bpd", "label": "Prod Recomendada", "units": "BPD", "icon": "trending_up", "color": "#00C853", "dec": 0, "type": "attribute"},
            {"key": "opt_well_health_score", "label": "Salud", "units": "%", "icon": "favorite", "color": "#FF5722", "dec": 0, "type": "attribute"},
            {"key": "opt_efficiency_pct", "label": "Eficiencia", "units": "%", "icon": "speed", "color": "#FF9800", "dec": 1, "type": "attribute"},
        ],
        "main_chart": [
            {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
            {"key": "speed_rpm", "label": "RPM", "u": "rpm", "c": "#FF9800", "y": "right"},
        ],
        "secondary_chart": [
            {"key": "motor_torque_ftlb", "label": "Torque", "u": "ft-lb", "c": "#F44336", "y": "left"},
            {"key": "motor_current_a", "label": "Corriente", "u": "A", "c": "#FF9800", "y": "left"},
            {"key": "intake_pressure_psi", "label": "P. Intake", "u": "PSI", "c": "#2196F3", "y": "right"},
        ],
        "opt_card_keys": [
            "opt_pcp_rpm", "opt_pcp_recommended_rpm", "opt_recommended_value",
            "opt_pcp_torque_ft_lbs", "opt_pcp_torque_pct_max",
            "opt_pcp_vol_efficiency_pct", "opt_pcp_wear_indicator", "opt_pcp_power_kw",
        ],
        "diag_label": "Diagnostico PCP",
        "diag_items": [
            ("Torque", "opt_pcp_torque_ft_lbs", "ft-lbs", "#F44336", None),
            ("% Torque Max", "opt_pcp_torque_pct_max", "%", "#FF9800", 80),
            ("Efic. Volumetrica", "opt_pcp_vol_efficiency_pct", "%", "#4CAF50", None),
            ("Desgaste", "opt_pcp_wear_indicator", "", "#F44336", 0.7),
            ("RPM Actual", "opt_pcp_rpm", "rpm", "#2196F3", None),
            ("RPM Recomendada", "opt_pcp_recommended_rpm", "rpm", "#4CAF50", None),
        ],
    },
    "gas_lift": {
        "state_id": "opt_gaslift", "color": "#9C27B0", "icon": "air",
        "label": "Levantamiento por Gas",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 0, "type": "timeseries"},
            {"key": "opt_gl_injection_rate_mscfd", "label": "Inyeccion Gas", "units": "MSCFD", "icon": "air", "color": "#9C27B0", "dec": 0, "type": "attribute"},
            {"key": "opt_gl_optimal_rate_mscfd", "label": "Iny. Optima", "units": "MSCFD", "icon": "check_circle", "color": "#4CAF50", "dec": 0, "type": "attribute"},
            {"key": "opt_recommended_rate_bpd", "label": "Prod Recomendada", "units": "BPD", "icon": "trending_up", "color": "#00C853", "dec": 0, "type": "attribute"},
            {"key": "opt_well_health_score", "label": "Salud", "units": "%", "icon": "favorite", "color": "#FF5722", "dec": 0, "type": "attribute"},
            {"key": "opt_potential_gain_bpd", "label": "Ganancia", "units": "BPD", "icon": "add_circle", "color": "#4CAF50", "dec": 0, "type": "attribute"},
        ],
        "main_chart": [
            {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
        ],
        "secondary_chart": None,  # Gas lift only has flow_rate as timeseries on asset
        "opt_card_keys": [
            "opt_gl_injection_rate_mscfd", "opt_gl_optimal_rate_mscfd", "opt_recommended_value",
            "opt_gl_heading_detected", "opt_gl_injection_pressure_psi",
        ],
        "diag_label": "Diagnostico Gas Lift",
        "diag_items": [
            ("Inyeccion Actual", "opt_gl_injection_rate_mscfd", "MSCFD", "#9C27B0", None),
            ("Inyeccion Optima", "opt_gl_optimal_rate_mscfd", "MSCFD", "#4CAF50", None),
            ("Heading", "opt_gl_heading_detected", "", "#F44336", None),
            ("Presion Inyeccion", "opt_gl_injection_pressure_psi", "PSI", "#305680", None),
        ],
    },
}


# -- Navigation JS for row click (routes to type-specific state) --------------

OPT_NAV_JS = """var liftType = '';
if (additionalParams && additionalParams.entity) {
    liftType = additionalParams.entity.lift_type || '';
}
if (!liftType && widgetContext && widgetContext.data) {
    var eid = entityId ? (entityId.id || entityId) : '';
    for (var i = 0; i < widgetContext.data.length; i++) {
        var d = widgetContext.data[i];
        if (d && d.dataKey && d.dataKey.name === 'lift_type') {
            if (eid && d.datasource && d.datasource.entityId === eid) {
                var vals = d.data;
                if (vals && vals.length > 0) { liftType = vals[vals.length-1][1]; break; }
            }
            if (!liftType && d.data && d.data.length > 0) {
                liftType = d.data[d.data.length-1][1];
            }
        }
    }
}
var stateMap = {'ESP':'opt_esp','SRP':'opt_srp','PCP':'opt_pcp',
    'gas_lift':'opt_gaslift','Gas Lift':'opt_gaslift'};
var targetState = stateMap[liftType] || 'opt_esp';
widgetContext.stateController.openState(targetState, {entityId: entityId, entityName: entityName}, false);"""


# -- Helper functions for per-type detail content -----------------------------

def _build_header_func(cfg):
    """Build markdownTextFunction for detail header with type hardcoded."""
    color = cfg["color"]
    label = cfg["label"]
    return (
        "var n=data['entityName']||'Pozo';var score=data['opt_well_health_score']||'--';"
        "var sc=Number(score);var scoreColor=sc>=80?'#4CAF50':sc>=60?'#FF9800':sc>=40?'#FFC107':'#F44336';"
        "if(isNaN(sc)||sc===0)scoreColor='#9FA6B4';"
        "var lastRun=data['opt_last_run']||'--';var ago='--';"
        "if(lastRun&&lastRun!=='--'){try{var d=new Date(lastRun);var now=new Date();var diff=Math.floor((now-d)/60000);"
        "if(diff<60)ago=diff+' min';else if(diff<1440)ago=Math.floor(diff/60)+' h';else ago=Math.floor(diff/1440)+' d';}catch(e){}}"
        "return '<div style=\"display:flex;align-items:center;gap:16px;padding:8px 16px;\">"
        "<div style=\"flex:1;\"><span style=\"font-size:22px;font-weight:700;color:#305680;\">'+n+'</span>"
        f"<span style=\"margin-left:8px;display:inline-block;padding:4px 12px;border-radius:20px;background:{color};color:white;font-size:12px;font-weight:600;\">{label}</span>"
        "<span style=\"margin-left:8px;font-size:12px;color:#9FA6B4;\">Ultima opt: hace '+ago+'</span></div>"
        "<div style=\"text-align:right;\"><div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;letter-spacing:0.5px;\">Score de Salud</div>"
        "<div style=\"font-size:32px;font-weight:700;color:'+scoreColor+';\">'+score+'</div></div></div>';"
    )


def _build_diag_func(cfg):
    """Build markdownTextFunction for diagnostics table."""
    parts = []
    parts.append("var html='';")
    parts.append(
        f"html+='<div style=\"padding:16px;\">"
        f"<h3 style=\"color:{cfg['color']};margin:0 0 12px 0;font-weight:600;\">"
        f"<span class=\"material-icons\" style=\"vertical-align:middle;margin-right:8px;\">{cfg['icon']}</span>"
        f"{cfg['diag_label']}</h3>';"
    )
    parts.append(
        "html+='<table style=\"width:100%;border-collapse:collapse;\">"
        "<tr style=\"background:#f5f7fa;\">"
        "<th style=\"padding:8px 12px;text-align:left;color:#9FA6B4;font-size:12px;\">Parametro</th>"
        "<th style=\"padding:8px 12px;text-align:left;color:#9FA6B4;font-size:12px;\">Valor</th>"
        "<th style=\"padding:8px 12px;text-align:left;color:#9FA6B4;font-size:12px;\">Unidad</th></tr>';"
    )
    for label, key, unit, item_color, threshold in cfg["diag_items"]:
        parts.append(
            f"html+='<tr>"
            f"<td style=\"padding:8px 12px;border-bottom:1px solid #f0f0f0;color:#4B535B;\">{label}</td>"
            f"<td style=\"padding:8px 12px;border-bottom:1px solid #f0f0f0;font-weight:600;color:{item_color};\">'+(data['{key}']||'--')+'</td>"
            f"<td style=\"padding:8px 12px;border-bottom:1px solid #f0f0f0;color:#9FA6B4;\">{unit}</td></tr>';"
        )
    parts.append("html+='</table></div>';")
    parts.append("return html;")
    return "".join(parts)


def _build_gl_secondary_func():
    """Gas Lift secondary panel (markdown instead of chart since no timeseries)."""
    return (
        "var injRate=data['opt_gl_injection_rate_mscfd']||'--';"
        "var optRate=data['opt_gl_optimal_rate_mscfd']||'--';"
        "var heading=data['opt_gl_heading_detected'];"
        "var injPres=data['opt_gl_injection_pressure_psi']||'--';"
        "var headingStr=(heading===true||heading==='true')?'<span style=\"color:#F44336;font-weight:700;\">DETECTADO</span>':'<span style=\"color:#4CAF50;\">No detectado</span>';"
        "return '<div style=\"padding:16px;\">"
        "<h3 style=\"color:#9C27B0;margin:0 0 16px 0;font-weight:600;\"><span class=\"material-icons\" style=\"vertical-align:middle;margin-right:8px;\">air</span>Parametros de Inyeccion</h3>"
        "<div style=\"display:flex;gap:12px;margin-bottom:16px;\">"
        "<div style=\"flex:1;padding:16px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
        "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Inyeccion Actual</div>"
        "<div style=\"font-size:28px;font-weight:700;color:#9C27B0;\">'+injRate+' <span style=\"font-size:13px;\">MSCFD</span></div></div>"
        "<div style=\"flex:1;padding:16px;background:#E8F5E9;border-radius:8px;text-align:center;\">"
        "<div style=\"font-size:11px;color:#4CAF50;text-transform:uppercase;\">Inyeccion Optima</div>"
        "<div style=\"font-size:28px;font-weight:700;color:#4CAF50;\">'+optRate+' <span style=\"font-size:13px;\">MSCFD</span></div></div></div>"
        "<div style=\"display:flex;gap:12px;\">"
        "<div style=\"flex:1;padding:12px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
        "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Heading</div>"
        "<div style=\"font-size:16px;margin-top:4px;\">'+headingStr+'</div></div>"
        "<div style=\"flex:1;padding:12px;background:#F5F7FA;border-radius:8px;text-align:center;\">"
        "<div style=\"font-size:11px;color:#9FA6B4;text-transform:uppercase;\">Presion Inyeccion</div>"
        "<div style=\"font-size:20px;font-weight:700;color:#305680;margin-top:4px;\">'+injPres+' psi</div></div></div>"
        "</div>';"
    )


# -- Main build ---------------------------------------------------------------

def build():
    token = tb_login()
    print("Logged in")

    headers = {"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Check if dashboard already exists - delete if so
    r = requests.get(f"{TB_URL}/api/tenant/dashboards?pageSize=100&page=0", headers=headers)
    r.raise_for_status()
    existing = [d for d in r.json().get("data", []) if d["title"] == DASHBOARD_TITLE]

    if existing:
        dash_id = existing[0]["id"]["id"]
        print(f"Deleting existing dashboard: {dash_id}")
        requests.delete(f"{TB_URL}/api/dashboard/{dash_id}", headers=headers)

    widgets = {}
    states = {}

    # -- Entity Aliases --
    entity_aliases = {
        ALIAS_ALL: {
            "id": ALIAS_ALL, "alias": "Todos los Pozos",
            "filter": {
                "type": "assetType", "resolveMultiple": True,
                "assetTypes": ["well"], "assetNameFilter": ""
            }
        },
        ALIAS_WELL: {
            "id": ALIAS_WELL, "alias": "Pozo Seleccionado",
            "filter": {
                "type": "stateEntity", "resolveMultiple": False,
                "stateEntityParamName": None, "defaultStateEntity": None
            }
        },
    }

    # -- Helper: register widget --
    def add_widget(wid, widget, row, col, sx, sy):
        widget["id"] = wid
        widget["row"] = row
        widget["col"] = col
        widget["sizeX"] = sx
        widget["sizeY"] = sy
        widgets[wid] = widget
        return {"row": row, "col": col, "sizeX": sx, "sizeY": sy}

    # ===================================================================
    # DEFAULT STATE: Optimization Summary
    # ===================================================================
    default_layout = {}

    # Row 0: Header with cycle indicators (uses first well's opt_last_run)
    hid = uid()
    hw = build_markdown("", alias=ALIAS_ALL,
        data_keys=[{"name": "opt_last_run", "type": "attribute"}],
        use_func=True, func_code=HEADER_FUNC)
    default_layout[hid] = add_widget(hid, hw, 0, 0, 24, 2)

    # Row 2: 6 KPIs using markdown cards with widgetContext.data aggregation
    def _kpi_md_func(key_name, label, units, icon, color, agg_type, dec=0):
        """Build a markdownTextFunction that aggregates a key across all entities."""
        agg_loop = {
            "SUM": (
                "var result=0;var count=0;"
                f"var values=data.filter(function(d){{return d['{key_name}']!==undefined&&d['{key_name}']!==null&&d['{key_name}']!=='';}});"
                f"for(var i=0;i<values.length;i++){{var v=Number(values[i]['{key_name}'])||0;result+=v;count++;}}"
                f"var display=count>0?result.toFixed({dec}):'--';"
            ),
            "AVG": (
                "var result=0;var count=0;"
                f"for(var i=0;i<data.length;i++){{var v=Number(data[i]['{key_name}'])||0;if(v>0){{result+=v;count++;}}}}"
                f"var display=count>0?(result/count).toFixed({dec}):'--';"
            ),
            "MIN": (
                "var result=Infinity;var count=0;"
                f"for(var i=0;i<data.length;i++){{var v=Number(data[i]['{key_name}'])||0;if(v>0){{result=Math.min(result,v);count++;}}}}"
                f"var display=count>0&&result!==Infinity?result.toFixed({dec}):'--';"
            ),
        }[agg_type]
        return (
            f"{agg_loop}"
            f"return '<div style=\"padding:8px 12px;\">"
            f"<div style=\"display:flex;align-items:center;gap:10px;\">"
            f"<div style=\"width:40px;height:40px;border-radius:50%;background:{color}20;display:flex;align-items:center;justify-content:center;\">"
            f"<span style=\"color:{color};font-size:20px;\" class=\"material-icons\">{icon}</span></div>"
            f"<div><div style=\"font-size:12px;color:rgba(0,0,0,0.54);font-weight:500;\">{label}</div>"
            f"<div style=\"font-size:24px;font-weight:600;color:rgba(0,0,0,0.87);\">'+display+' <span style=\"font-size:13px;font-weight:400;color:rgba(0,0,0,0.38);\">{units}</span></div>"
            f"</div></div></div>';"
        )

    kpi_specs = [
        ("opt_potential_gain_bpd", "Ganancia Total Campo", "BPD", "trending_up", "#4CAF50", "SUM", 0),
        ("opt_well_health_score", "Salud Promedio", "/100", "favorite", "#FF9800", "AVG", 1),
        ("opt_efficiency_pct", "Eficiencia Promedio", "%", "speed", "#2196F3", "AVG", 1),
        ("opt_current_rate_bpd", "Produccion Total", "BPD", "show_chart", "#305680", "SUM", 0),
        ("opt_specific_energy_kwh_bbl", "Energia Promedio", "kWh/bbl", "bolt", "#FF9800", "AVG", 2),
        ("opt_recommended_rate_bpd", "Prod. Potencial Total", "BPD", "rocket_launch", "#4CAF50", "SUM", 0),
    ]
    for i, (key, label, units, icon, color, agg, dec) in enumerate(kpi_specs):
        kid = uid()
        func = _kpi_md_func(key, label, units, icon, color, agg, dec)
        w = build_markdown("", alias=ALIAS_ALL,
            data_keys=[{"name": key, "type": "attribute"}],
            use_func=True, func_code=func)
        default_layout[kid] = add_widget(kid, w, 2, i * 4, 4, 3)

    # Row 5: Main Recommendations Table (18 cols) with OPT_NAV_JS row click
    table_columns = [
        {"name": "name", "type": "entityField", "label": "Pozo"},
        {"name": "lift_type", "type": "attribute", "label": "Tipo"},
        {"name": "opt_status", "type": "attribute", "label": "Estado"},
        {"name": "opt_well_health_score", "type": "attribute", "label": "Salud"},
        {"name": "opt_current_rate_bpd", "type": "attribute", "label": "Actual BPD"},
        {"name": "opt_recommended_rate_bpd", "type": "attribute", "label": "Recom. BPD"},
        {"name": "opt_recommended_action", "type": "attribute", "label": "Accion"},
        {"name": "opt_potential_gain_bpd", "type": "attribute", "label": "Ganancia BPD"},
        {"name": "opt_efficiency_pct", "type": "attribute", "label": "Eficiencia %"},
    ]
    cell_styles = {
        "opt_well_health_score": CELL_STYLE_HEALTH,
        "opt_status": CELL_STYLE_STATUS,
        "opt_potential_gain_bpd": CELL_STYLE_GAIN,
    }
    cell_contents = {
        "opt_recommended_action": CELL_CONTENT_ACTION,
        "lift_type": CELL_CONTENT_LIFT_TYPE,
    }

    tid = uid()
    tw = build_entities_table(
        "Recomendaciones de Optimizacion", table_columns, ALIAS_ALL,
        sort_col="opt_potential_gain_bpd", page_size=15,
        row_click_js=OPT_NAV_JS, cell_styles=cell_styles, cell_contents=cell_contents)
    default_layout[tid] = add_widget(tid, tw, 5, 0, 18, 10)

    # Row 5 right: Health Distribution (dynamic)
    hdid = uid()
    hdw = build_markdown("", alias=ALIAS_ALL,
        data_keys=[{"name": "opt_well_health_score", "type": "attribute"}],
        use_func=True, func_code=HEALTH_DIST_FUNC)
    default_layout[hdid] = add_widget(hdid, hdw, 5, 18, 6, 5)

    # Row 10 right: Top 5 Opportunities
    top5_cols = [
        {"name": "name", "type": "entityField", "label": "Pozo"},
        {"name": "lift_type", "type": "attribute", "label": "Tipo"},
        {"name": "opt_potential_gain_bpd", "type": "attribute", "label": "Ganancia BPD"},
        {"name": "opt_recommended_action", "type": "attribute", "label": "Accion"},
    ]
    t5id = uid()
    t5w = build_entities_table(
        "Top 5 Oportunidades", top5_cols, ALIAS_ALL,
        sort_col="opt_potential_gain_bpd", page_size=5, show_pagination=False,
        row_click_js=OPT_NAV_JS,
        cell_styles={"opt_potential_gain_bpd": CELL_STYLE_GAIN},
        cell_contents={"opt_recommended_action": CELL_CONTENT_ACTION, "lift_type": CELL_CONTENT_LIFT_TYPE})
    default_layout[t5id] = add_widget(t5id, t5w, 10, 18, 6, 5)

    # Row 15: Field Optimization (Gas Allocation + Constraints)
    foid = uid()
    fow = build_markdown("", alias=ALIAS_ALL,
        data_keys=[],
        use_func=True, func_code=FIELD_OPT_FUNC)
    default_layout[foid] = add_widget(foid, fow, 15, 0, 24, 4)

    states["default"] = {
        "name": DASHBOARD_TITLE,
        "root": True,
        "layouts": {"main": {
            "widgets": default_layout,
            "gridSettings": {
                "backgroundColor": "#f5f7fa", "columns": 24, "margin": 8,
                "outerMargin": True, "backgroundSizeMode": "100%",
                "layoutType": "default", "autoFillHeight": False, "rowHeight": 70
            }
        }}
    }

    # ===================================================================
    # PER-TYPE DETAIL STATES (opt_esp, opt_srp, opt_pcp, opt_gaslift)
    # ===================================================================
    opt_card_funcs = {
        "ESP": ESP_OPT_FUNC,
        "SRP": SRP_OPT_FUNC,
        "PCP": PCP_OPT_FUNC,
        "gas_lift": GL_OPT_FUNC,
    }

    grid_detail = {
        "backgroundColor": "#f5f7fa", "columns": 24, "margin": 8,
        "outerMargin": True, "backgroundSizeMode": "100%",
        "layoutType": "default", "autoFillHeight": False, "rowHeight": 70
    }

    for wtype, cfg in OPT_WELL_TYPES.items():
        detail_layout = {}
        state_id = cfg["state_id"]

        # Row 0: Back button
        bid = uid()
        detail_layout[bid] = add_widget(bid, build_back(), 0, 0, 3, 2)

        # Row 0: Header with type hardcoded
        dhid = uid()
        dhw = build_markdown("", alias=ALIAS_WELL,
            data_keys=[
                {"name": "entityName", "type": "entityField"},
                {"name": "opt_well_health_score", "type": "attribute"},
                {"name": "opt_last_run", "type": "attribute"},
            ],
            use_func=True, func_code=_build_header_func(cfg))
        detail_layout[dhid] = add_widget(dhid, dhw, 0, 3, 21, 2)

        # Row 2: 6 KPIs (type-specific mix of timeseries + attributes)
        for i, kpi in enumerate(cfg["kpis"]):
            kid = uid()
            w = build_kpi(kpi["key"], kpi["label"], kpi["units"], kpi["icon"], kpi["color"],
                           kpi["dec"], alias=ALIAS_WELL,
                           key_type=kpi.get("type", "timeseries"))
            detail_layout[kid] = add_widget(kid, w, 2, i * 4, 4, 3)

        # Row 5: Action Card
        acid = uid()
        acw = build_markdown("", alias=ALIAS_WELL,
            data_keys=[
                {"name": "opt_recommended_action", "type": "attribute"},
                {"name": "opt_recommended_action_detail", "type": "attribute"},
                {"name": "opt_decline_rate_monthly_percent", "type": "attribute"},
            ],
            use_func=True, func_code=ACTION_CARD_FUNC)
        detail_layout[acid] = add_widget(acid, acw, 5, 0, 24, 3)

        # Row 8 left: Main chart (production + control variable)
        pcid = uid()
        pcw = build_chart(f"Produccion - {cfg['label']}", cfg["main_chart"], alias=ALIAS_WELL)
        detail_layout[pcid] = add_widget(pcid, pcw, 8, 0, 12, 8)

        # Row 8 right: Secondary chart OR gas lift injection panel
        scid = uid()
        if cfg.get("secondary_chart"):
            scw = build_chart(f"Sistema - {cfg['label']}", cfg["secondary_chart"], alias=ALIAS_WELL)
        else:
            # Gas lift: markdown panel with injection parameters
            gl_keys = [
                {"name": "opt_gl_injection_rate_mscfd", "type": "attribute"},
                {"name": "opt_gl_optimal_rate_mscfd", "type": "attribute"},
                {"name": "opt_gl_heading_detected", "type": "attribute"},
                {"name": "opt_gl_injection_pressure_psi", "type": "attribute"},
            ]
            scw = build_markdown("", alias=ALIAS_WELL, data_keys=gl_keys,
                use_func=True, func_code=_build_gl_secondary_func())
        detail_layout[scid] = add_widget(scid, scw, 8, 12, 12, 8)

        # Row 16 left: Diagnostics (opt_* per-type parameters)
        did = uid()
        diag_keys = [{"name": k, "type": "attribute"} for _, k, _, _, _ in cfg["diag_items"]]
        dw = build_markdown("", alias=ALIAS_WELL, data_keys=diag_keys,
            use_func=True, func_code=_build_diag_func(cfg))
        detail_layout[did] = add_widget(did, dw, 16, 0, 12, 6)

        # Row 16 right: Optimization card (current vs recommended)
        ocid = uid()
        opt_keys = [{"name": k, "type": "attribute"} for k in cfg["opt_card_keys"]]
        ocw = build_markdown("", alias=ALIAS_WELL, data_keys=opt_keys,
            use_func=True, func_code=opt_card_funcs[wtype])
        detail_layout[ocid] = add_widget(ocid, ocw, 16, 12, 12, 6)

        states[state_id] = {
            "name": f"${{entityName}} - Opt {cfg['label']}",
            "root": False,
            "layouts": {"main": {
                "widgets": detail_layout,
                "gridSettings": grid_detail
            }}
        }

    # ===================================================================
    # Assemble Dashboard
    # ===================================================================
    dash = {
        "title": DASHBOARD_TITLE,
        "configuration": {
            "description": "Dashboard de resultados del servicio de optimizacion - 4 estados tipo-especificos",
            "widgets": widgets,
            "states": states,
            "entityAliases": entity_aliases,
            "filters": {},
            "settings": {
                "stateControllerId": "entity",
                "showTitle": False,
                "showDashboardsSelect": True,
                "showEntitiesSelect": True,
                "showDashboardTimewindow": True,
                "showDashboardExport": True,
                "toolbarAlwaysOpen": True,
                "showFilters": True,
                "css": DASHBOARD_CSS,
            },
        }
    }

    # Save locally
    out = "/Users/diazhh/Documents/GitHub/atilax_sim_pozos/dash_actual/atilax_-_optimizacion_de_campo.json"
    with open(out, "w") as f:
        json.dump(dash, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out}")

    # Upload
    r = requests.post(f"{TB_URL}/api/dashboard", json=dash, headers=headers)
    if r.status_code == 200:
        resp = r.json()
        new_id = resp["id"]["id"]
        print(f"Uploaded! -> {TB_URL}/dashboards/all/{new_id}")
        wcount = len(widgets)
        scount = len(states)
        print(f"Stats: {scount} states, {wcount} widgets, {len(entity_aliases)} aliases")
    else:
        print(f"Error {r.status_code}: {r.text[:500]}")

    return dash


if __name__ == "__main__":
    build()
