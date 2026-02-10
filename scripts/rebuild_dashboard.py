#!/usr/bin/env python3
"""
Rebuild Atilax Mapa de Campo dashboard v2 - Professional quality.

Based on ThingsBoard template patterns (mine_site_monitoring, fuel_level_monitoring).
Fixes state navigation, adds elegant charts, proper buttons, custom CSS.
"""
import json
import uuid
import requests
import sys

# ── Config ──────────────────────────────────────────────────────────────
TB_URL = "http://144.126.150.120:8080"
TB_USER = "well@atilax.io"
TB_PASS = "10203040"
DASHBOARD_ID = "223efa30-05b8-11f1-8dfb-fb2fc7314bd7"

ALIAS_ALL = "014b1f10-058c-5a66-dd9c-e12ddfdf2d48"
ALIAS_USER = "ad933091-c2b0-621e-d6e3-1b9c496403f4"
ALIAS_WELL = "bd860552-88a3-e657-57a4-ceb226a1cbff"
FILTER_ID = "4b200043-3921-2edd-6283-2d79f9394433"


def tb_login():
    r = requests.post(f"{TB_URL}/api/auth/login",
                      json={"username": TB_USER, "password": TB_PASS})
    r.raise_for_status()
    return r.json()["token"]


def uid():
    return str(uuid.uuid4())


# ── Dashboard-level CSS ─────────────────────────────────────────────────
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
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-in,
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-out {
    color: #4B535B;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-in {
    border-radius: 6px 6px 0 0;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-out {
    border-radius: 0 0 6px 6px;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control {
    border: none;
}
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-popup a.tb-custom-action {
    font-family: 'Roboto'; font-weight: 500; font-size: 14px;
    letter-spacing: 0.25px; border-bottom: none; color: #5469FF;
}
mat-cell { border: none !important; }
"""

# ── Telemetry definitions ───────────────────────────────────────────────
WELL_TYPES = {
    "ESP": {
        "state_id": "detalle_esp", "color": "#4CAF50", "icon": "bolt",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 1},
            {"key": "motor_current_a", "label": "Corriente", "units": "A", "icon": "electrical_services", "color": "#FF9800", "dec": 1},
            {"key": "motor_temperature_f", "label": "Temp Motor", "units": "°F", "icon": "thermostat", "color": "#F44336", "dec": 1},
            {"key": "intake_pressure_psi", "label": "P. Intake", "units": "PSI", "icon": "speed", "color": "#2196F3", "dec": 1},
            {"key": "frequency_hz", "label": "Frecuencia", "units": "Hz", "icon": "tune", "color": "#9C27B0", "dec": 1},
            {"key": "vibration_ips", "label": "Vibracion", "units": "IPS", "icon": "vibration", "color": "#795548", "dec": 2},
        ],
        "systems": [
            {"name": "Electrico", "icon": "electrical_services", "color": "#FF9800", "sid": "modal_esp_electrico",
             "keys": [
                 {"key": "motor_current_a", "label": "Corriente Motor", "u": "A", "c": "#FF9800", "y": "left"},
                 {"key": "motor_voltage_v", "label": "Voltaje Motor", "u": "V", "c": "#2196F3", "y": "right"},
                 {"key": "motor_power_kw", "label": "Potencia Motor", "u": "kW", "c": "#4CAF50", "y": "left"},
                 {"key": "frequency_hz", "label": "Frecuencia", "u": "Hz", "c": "#9C27B0", "y": "right"},
             ]},
            {"name": "Termico", "icon": "thermostat", "color": "#F44336", "sid": "modal_esp_termico",
             "keys": [
                 {"key": "motor_temperature_f", "label": "Temp Motor", "u": "°F", "c": "#F44336", "y": "left"},
                 {"key": "wellhead_temperature_f", "label": "Temp Cabezal", "u": "°F", "c": "#FF9800", "y": "left"},
                 {"key": "motor_current_a", "label": "Corriente", "u": "A", "c": "#2196F3", "y": "right"},
             ]},
            {"name": "Vibracion", "icon": "vibration", "color": "#9C27B0", "sid": "modal_esp_vibracion",
             "keys": [
                 {"key": "vibration_ips", "label": "Vibracion", "u": "IPS", "c": "#9C27B0", "y": "left"},
                 {"key": "motor_current_a", "label": "Corriente", "u": "A", "c": "#FF9800", "y": "right"},
                 {"key": "frequency_hz", "label": "Frecuencia", "u": "Hz", "c": "#2196F3", "y": "right"},
             ]},
            {"name": "Hidraulico", "icon": "water", "color": "#2196F3", "sid": "modal_esp_hidraulico",
             "keys": [
                 {"key": "intake_pressure_psi", "label": "P. Intake", "u": "PSI", "c": "#2196F3", "y": "left"},
                 {"key": "discharge_pressure_psi", "label": "P. Descarga", "u": "PSI", "c": "#00BCD4", "y": "left"},
                 {"key": "tubing_pressure_psi", "label": "P. Tubing", "u": "PSI", "c": "#4CAF50", "y": "left"},
                 {"key": "casing_pressure_psi", "label": "P. Casing", "u": "PSI", "c": "#FF9800", "y": "left"},
             ]},
            {"name": "Produccion", "icon": "oil_barrel", "color": "#4CAF50", "sid": "modal_esp_produccion",
             "keys": [
                 {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
                 {"key": "intake_pressure_psi", "label": "P. Intake", "u": "PSI", "c": "#2196F3", "y": "right"},
                 {"key": "frequency_hz", "label": "Frecuencia", "u": "Hz", "c": "#9C27B0", "y": "right"},
             ]},
        ]
    },
    "SRP": {
        "state_id": "detalle_srp", "color": "#2196F3", "icon": "architecture",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 1},
            {"key": "motor_current_a", "label": "Corriente", "units": "A", "icon": "electrical_services", "color": "#FF9800", "dec": 1},
            {"key": "spm", "label": "SPM", "units": "spm", "icon": "speed", "color": "#2196F3", "dec": 1},
            {"key": "load_lb", "label": "Carga", "units": "lb", "icon": "fitness_center", "color": "#F44336", "dec": 0},
            {"key": "pump_fillage_pct", "label": "Llenado", "units": "%", "icon": "water", "color": "#00BCD4", "dec": 1},
            {"key": "tubing_pressure_psi", "label": "P. Tubing", "units": "PSI", "icon": "compress", "color": "#9C27B0", "dec": 1},
        ],
        "systems": [
            {"name": "Varillas", "icon": "straighten", "color": "#F44336", "sid": "modal_srp_varillas",
             "keys": [
                 {"key": "load_lb", "label": "Carga", "u": "lb", "c": "#F44336", "y": "left"},
                 {"key": "spm", "label": "SPM", "u": "spm", "c": "#2196F3", "y": "right"},
                 {"key": "pump_fillage_pct", "label": "Llenado", "u": "%", "c": "#4CAF50", "y": "right"},
             ]},
            {"name": "Hidraulico", "icon": "water", "color": "#2196F3", "sid": "modal_srp_hidraulico",
             "keys": [
                 {"key": "tubing_pressure_psi", "label": "P. Tubing", "u": "PSI", "c": "#2196F3", "y": "left"},
                 {"key": "casing_pressure_psi", "label": "P. Casing", "u": "PSI", "c": "#FF9800", "y": "left"},
                 {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "right"},
             ]},
            {"name": "Electrico", "icon": "electrical_services", "color": "#FF9800", "sid": "modal_srp_electrico",
             "keys": [
                 {"key": "motor_current_a", "label": "Corriente", "u": "A", "c": "#FF9800", "y": "left"},
                 {"key": "motor_power_kw", "label": "Potencia", "u": "kW", "c": "#4CAF50", "y": "left"},
                 {"key": "spm", "label": "SPM", "u": "spm", "c": "#2196F3", "y": "right"},
             ]},
            {"name": "Produccion", "icon": "oil_barrel", "color": "#4CAF50", "sid": "modal_srp_produccion",
             "keys": [
                 {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
                 {"key": "pump_fillage_pct", "label": "Llenado", "u": "%", "c": "#00BCD4", "y": "right"},
                 {"key": "load_lb", "label": "Carga", "u": "lb", "c": "#F44336", "y": "right"},
             ]},
        ]
    },
    "PCP": {
        "state_id": "detalle_pcp", "color": "#FF9800", "icon": "settings",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 1},
            {"key": "motor_current_a", "label": "Corriente", "units": "A", "icon": "electrical_services", "color": "#FF9800", "dec": 1},
            {"key": "speed_rpm", "label": "RPM", "units": "rpm", "icon": "speed", "color": "#2196F3", "dec": 0},
            {"key": "motor_torque_ftlb", "label": "Torque", "units": "ft-lb", "icon": "rotate_right", "color": "#F44336", "dec": 1},
            {"key": "intake_pressure_psi", "label": "P. Intake", "units": "PSI", "icon": "compress", "color": "#9C27B0", "dec": 1},
            {"key": "tubing_pressure_psi", "label": "P. Tubing", "units": "PSI", "icon": "compress", "color": "#00BCD4", "dec": 1},
        ],
        "systems": [
            {"name": "Cavidad", "icon": "settings", "color": "#F44336", "sid": "modal_pcp_cavidad",
             "keys": [
                 {"key": "speed_rpm", "label": "RPM", "u": "rpm", "c": "#2196F3", "y": "left"},
                 {"key": "motor_torque_ftlb", "label": "Torque", "u": "ft-lb", "c": "#F44336", "y": "right"},
                 {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "right"},
             ]},
            {"name": "Hidraulico", "icon": "water", "color": "#2196F3", "sid": "modal_pcp_hidraulico",
             "keys": [
                 {"key": "intake_pressure_psi", "label": "P. Intake", "u": "PSI", "c": "#2196F3", "y": "left"},
                 {"key": "tubing_pressure_psi", "label": "P. Tubing", "u": "PSI", "c": "#4CAF50", "y": "left"},
                 {"key": "casing_pressure_psi", "label": "P. Casing", "u": "PSI", "c": "#FF9800", "y": "left"},
             ]},
            {"name": "Electrico", "icon": "electrical_services", "color": "#FF9800", "sid": "modal_pcp_electrico",
             "keys": [
                 {"key": "motor_current_a", "label": "Corriente", "u": "A", "c": "#FF9800", "y": "left"},
                 {"key": "motor_power_kw", "label": "Potencia", "u": "kW", "c": "#4CAF50", "y": "left"},
                 {"key": "motor_torque_ftlb", "label": "Torque", "u": "ft-lb", "c": "#F44336", "y": "right"},
             ]},
            {"name": "Produccion", "icon": "oil_barrel", "color": "#4CAF50", "sid": "modal_pcp_produccion",
             "keys": [
                 {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
                 {"key": "speed_rpm", "label": "RPM", "u": "rpm", "c": "#2196F3", "y": "right"},
                 {"key": "motor_torque_ftlb", "label": "Torque", "u": "ft-lb", "c": "#F44336", "y": "right"},
             ]},
        ]
    },
    "gas_lift": {
        "state_id": "detalle_gaslift", "color": "#9C27B0", "icon": "air",
        "kpis": [
            {"key": "flow_rate_bpd", "label": "Produccion", "units": "BPD", "icon": "oil_barrel", "color": "#4CAF50", "dec": 1},
            {"key": "tubing_pressure_psi", "label": "P. Tubing", "units": "PSI", "icon": "compress", "color": "#2196F3", "dec": 1},
            {"key": "casing_pressure_psi", "label": "P. Casing", "units": "PSI", "icon": "compress", "color": "#FF9800", "dec": 1},
        ],
        "systems": [
            {"name": "Inyeccion", "icon": "air", "color": "#9C27B0", "sid": "modal_gl_inyeccion",
             "keys": [
                 {"key": "tubing_pressure_psi", "label": "P. Tubing", "u": "PSI", "c": "#2196F3", "y": "left"},
                 {"key": "casing_pressure_psi", "label": "P. Casing", "u": "PSI", "c": "#FF9800", "y": "left"},
             ]},
            {"name": "Produccion", "icon": "oil_barrel", "color": "#4CAF50", "sid": "modal_gl_produccion",
             "keys": [
                 {"key": "flow_rate_bpd", "label": "Produccion", "u": "BPD", "c": "#4CAF50", "y": "left"},
                 {"key": "tubing_pressure_psi", "label": "P. Tubing", "u": "PSI", "c": "#2196F3", "y": "right"},
             ]},
        ]
    },
}


# ── Navigation JS (shared by table and map) ─────────────────────────────
NAV_JS_TABLE = """var liftType = '';
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
var stateMap = {'ESP':'detalle_esp','SRP':'detalle_srp','PCP':'detalle_pcp',
    'gas_lift':'detalle_gaslift','Gas Lift':'detalle_gaslift'};
var targetState = stateMap[liftType] || 'detalle_esp';
widgetContext.stateController.openState(targetState, {entityId: entityId, entityName: entityName}, false);"""

NAV_JS_MAP = """var liftType = '';
if (additionalParams) {
    if (additionalParams.lift_type) liftType = additionalParams.lift_type;
    else if (additionalParams.datasource && additionalParams.datasource.lift_type) liftType = additionalParams.datasource.lift_type;
    else if (additionalParams.data && additionalParams.data.lift_type) liftType = additionalParams.data.lift_type;
    else if (additionalParams.markerValue && additionalParams.markerValue.lift_type) liftType = additionalParams.markerValue.lift_type;
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
var stateMap = {'ESP':'detalle_esp','SRP':'detalle_srp','PCP':'detalle_pcp',
    'gas_lift':'detalle_gaslift','Gas Lift':'detalle_gaslift'};
var targetState = stateMap[liftType] || 'detalle_esp';
widgetContext.stateController.openState(targetState, {entityId: entityId, entityName: entityName}, false);"""


# ── Widget builders ─────────────────────────────────────────────────────

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


def build_chart(title, keys, alias=ALIAS_WELL):
    """Elegant time_series_chart with dual Y axes, legend, tooltips."""
    dkeys = []
    left_u, right_u = set(), set()
    for k in keys:
        yid = "default" if k["y"] == "left" else "right"
        fill = "gradient" if len(keys) == 1 else "none"
        dkeys.append({
            "name": k["key"], "type": "timeseries", "label": k["label"], "color": k["c"],
            "units": k["u"], "decimals": 1,
            "settings": {
                "yAxisId": yid, "showInLegend": True, "dataHiddenByDefault": False,
                "type": "line", "lineSettings": _line(k["c"], fill),
                "barSettings": {"showBorder": False, "borderWidth": 2, "borderRadius": 0,
                    "showLabel": False, "labelPosition": "top",
                    "labelFont": {"family": "Roboto", "size": 11, "sizeUnit": "px", "style": "normal", "weight": "400", "lineHeight": "1"},
                    "labelColor": "rgba(0,0,0,0.76)", "enableLabelBackground": False,
                    "labelBackground": "rgba(255,255,255,0.56)",
                    "backgroundSettings": {"type": "none", "opacity": 0.4, "gradient": {"start": 100, "end": 0}}},
                "comparisonSettings": {"showValuesForComparison": False, "comparisonValuesLabel": "", "color": ""}
            }
        })
        (left_u if k["y"] == "left" else right_u).add(k["u"])

    yaxes = {"default": _yaxis("default", "/".join(left_u), "left")}
    if right_u:
        yaxes["right"] = _yaxis("right", "/".join(right_u), "right")

    return {
        "typeFullFqn": "system.time_series_chart", "type": "timeseries",
        "sizeX": 24, "sizeY": 10,
        "config": {
            "datasources": [{"type": "entity", "name": "", "entityAliasId": alias, "dataKeys": dkeys}],
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


def build_kpi(key, label, units, icon, color, dec=1):
    """Horizontal value card KPI."""
    return {
        "typeFullFqn": "system.cards.horizontal_value_card", "type": "latest",
        "sizeX": 4, "sizeY": 3,
        "config": {
            "datasources": [{"type": "entity", "entityAliasId": ALIAS_WELL,
                "dataKeys": [{"name": key, "type": "timeseries", "label": label, "color": color, "settings": {}}]}],
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


def build_btn(label, icon, color, target, dialog=True, dw=90, dh=80):
    """system.action_button with filled style."""
    return {
        "typeFullFqn": "system.action_button", "type": "latest",
        "sizeX": 3, "sizeY": 2,
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
                    "type": "filled", "showLabel": True, "label": label,
                    "showIcon": True, "icon": icon, "iconSize": 20, "iconSizeUnit": "px",
                    "mainColor": color, "backgroundColor": "#FFFFFF", "autoScale": True,
                    "customStyle": {"enabled": None, "hovered": None, "pressed": None, "activated": None, "disabled": None}
                }
            },
            "title": "", "dropShadow": True, "enableFullscreen": False, "borderRadius": "8px",
            "configMode": "advanced",
            "actions": {"click": [{
                "id": uid(), "name": "onClick", "icon": "more_horiz",
                "type": "openDashboardState", "targetDashboardStateId": target,
                "setEntityId": True, "stateEntityParamName": None,
                "openRightLayout": False, "openInSeparateDialog": dialog, "openInPopover": False,
                "dialogTitle": label, "dialogHideDashboardToolbar": True,
                "dialogWidth": dw, "dialogHeight": dh,
            }]},
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


def build_title(type_name, type_color):
    return {
        "typeFullFqn": "system.cards.markdown_card", "type": "latest", "sizeX": 21, "sizeY": 2,
        "config": {
            "datasources": [{"type": "entity", "entityAliasId": ALIAS_WELL,
                "dataKeys": [
                    {"name": "entityName", "type": "entityField", "label": "entityName", "color": "#2196f3", "settings": {}},
                    {"name": "field_name", "type": "attribute", "label": "field_name", "color": "#4caf50", "settings": {"dataKeyType": "server"}},
                    {"name": "macolla_name", "type": "attribute", "label": "macolla_name", "color": "#ff9800", "settings": {"dataKeyType": "server"}},
                    {"name": "status", "type": "attribute", "label": "status", "color": "#f44336", "settings": {"dataKeyType": "server"}},
                ]}],
            "showTitle": False, "backgroundColor": "rgba(0,0,0,0)", "padding": "4px",
            "settings": {"useMarkdownTextFunction": True, "markdownTextFunction":
                f"var n=data['entityName']||'Pozo';var f=data['field_name']||'';var m=data['macolla_name']||'';var s=data['status']||'';"
                f"var sc=s==='producing'?'#4CAF50':'#F44336';var sl=s==='producing'?'Produciendo':'Detenido';"
                f"return '<div style=\"display:flex;align-items:center;height:100%;gap:12px;padding:8px 16px;\">"
                f"<div style=\"font-size:22px;font-weight:600;color:#1a1a2e;font-family:Roboto,sans-serif;\">'+n+'</div>"
                f"<div style=\"padding:4px 12px;border-radius:20px;background:{type_color};color:white;font-size:12px;font-weight:600;font-family:Roboto,sans-serif;\">{type_name}</div>"
                f"<div style=\"padding:4px 12px;border-radius:20px;background:'+sc+';color:white;font-size:12px;font-weight:600;font-family:Roboto,sans-serif;\">'+sl+'</div>"
                f"<div style=\"color:#666;font-size:13px;font-family:Roboto,sans-serif;\">'+f+' / '+m+'</div></div>';"},
            "dropShadow": False, "enableFullscreen": False,
        }
    }


# ── Main build ──────────────────────────────────────────────────────────

def build():
    token = tb_login()
    print("Logged in")

    r = requests.get(f"{TB_URL}/api/dashboard/{DASHBOARD_ID}",
                     headers={"X-Authorization": f"Bearer {token}"})
    r.raise_for_status()
    dash = r.json()
    print(f"Loaded: {dash['title']}")

    old_widgets = dash["configuration"]["widgets"]
    old_states = dash["configuration"]["states"]
    widgets = {}
    states = {}

    # ── DEFAULT STATE: keep existing, fix actions + enhance widgets ──
    default_wids = list(old_states["default"]["layouts"]["main"]["widgets"].keys())
    for wid_key in default_wids:
        if wid_key not in old_widgets:
            continue
        w = old_widgets[wid_key]
        fqn = w.get("typeFullFqn", "")

        # Fix table navigation + enhance styling
        if "entities_table" in fqn:
            w["config"]["actions"] = {
                "headerButton": [],
                "rowClick": [{"id": uid(), "name": "Ver Detalle", "icon": "more_horiz",
                    "type": "custom", "customFunction": NAV_JS_TABLE,
                    "setEntityId": True, "stateEntityParamName": None,
                    "openRightLayout": False, "openInSeparateDialog": False,
                    "openInPopover": False}],
                "actionCellButton": [{"id": uid(), "name": "Ver Detalle", "icon": "play_arrow",
                    "type": "custom", "customFunction": NAV_JS_TABLE,
                    "setEntityId": True, "stateEntityParamName": None,
                    "openRightLayout": False, "openInSeparateDialog": False,
                    "openInPopover": False}]
            }
            # Enhance table columns with styled cellContentFunction
            for ds in w["config"].get("datasources", []):
                for dk in ds.get("dataKeys", []):
                    if dk["name"] == "lift_type":
                        dk["settings"] = dk.get("settings", {})
                        dk["settings"]["useCellContentFunction"] = True
                        dk["settings"]["cellContentFunction"] = (
                            "var colors = {'ESP':'#4CAF50','SRP':'#2196F3','PCP':'#FF9800','gas_lift':'#9C27B0','Gas Lift':'#9C27B0'};"
                            "var labels = {'ESP':'ESP','SRP':'SRP','PCP':'PCP','gas_lift':'Gas Lift','Gas Lift':'Gas Lift'};"
                            "var c = colors[value] || '#607D8B'; var l = labels[value] || value;"
                            "return '<div style=\"display:inline-block;padding:3px 10px;border-radius:12px;background:'+c+';color:#fff;"
                            "font-size:11px;font-weight:600;letter-spacing:0.5px;\">'+l+'</div>';"
                        )
                        dk["settings"]["useCellStyleFunction"] = False
                    elif dk["name"] == "status":
                        dk["settings"] = dk.get("settings", {})
                        dk["settings"]["useCellContentFunction"] = True
                        dk["settings"]["cellContentFunction"] = (
                            "var c = value === 'producing' ? '#4CAF50' : '#F44336';"
                            "var l = value === 'producing' ? 'Produciendo' : 'Detenido';"
                            "return '<div style=\"display:inline-flex;align-items:center;gap:4px;\">"
                            "<div style=\"width:8px;height:8px;border-radius:50%;background:'+c+';\"></div>"
                            "<span style=\"font-size:12px;font-weight:500;color:'+c+';\">'+l+'</span></div>';"
                        )
                    elif dk["name"] == "flow_rate_bpd":
                        dk["settings"] = dk.get("settings", {})
                        dk["settings"]["useCellContentFunction"] = True
                        dk["settings"]["cellContentFunction"] = (
                            "var v = Number(value) || 0; var pct = Math.min(100, v / 30);"
                            "return '<div style=\"display:flex;align-items:center;gap:8px;\">"
                            "<div style=\"flex:1;height:6px;background:#eee;border-radius:3px;overflow:hidden;\">"
                            "<div style=\"width:'+pct+'%;height:100%;background:#4CAF50;border-radius:3px;\"></div>"
                            "</div><span style=\"font-size:12px;font-weight:500;min-width:60px;\">'+v.toFixed(0)+' BPD</span></div>';"
                        )
                    elif dk["name"] == "name":
                        dk["settings"] = dk.get("settings", {})
                        dk["settings"]["useCellStyleFunction"] = True
                        dk["settings"]["cellStyleFunction"] = "return {fontWeight: '600', color: '#1a2332'};"
            # Table visual settings
            w["config"]["settings"] = w["config"].get("settings", {})
            w["config"]["settings"]["enableStickyHeader"] = True
            w["config"]["settings"]["enableStickyAction"] = True
            w["config"]["settings"]["displayPagination"] = True
            w["config"]["settings"]["defaultPageSize"] = 20
            w["config"]["settings"]["defaultSortOrder"] = "-flow_rate_bpd"
            w["config"]["showTitle"] = True
            w["config"]["title"] = "Pozos"
            w["config"]["titleStyle"] = {"fontSize": "16px", "fontWeight": "500"}
            w["config"]["borderRadius"] = "8px"
            w["config"]["dropShadow"] = True

        # Fix map navigation + switch to OSM + enhance
        if "map" in fqn.lower():
            # Clear widget-level datasources since markers have their own
            w["config"]["datasources"] = []
            w["config"]["actions"] = {}
            s = w["config"].get("settings", {})
            # Use openstreet provider (matching TB templates)
            s["layers"] = [
                {"label": "Mapa", "provider": "openstreet", "layerType": "OpenStreetMap.Mapnik"},
                {"label": "Satelite", "provider": "openstreet", "layerType": "Esri.WorldImagery"},
                {"label": "Hibrido", "provider": "openstreet", "layerType": "Esri.WorldImagery",
                 "referenceLayer": "openstreetmap_hybrid"},
            ]
            # Map marker config - self-contained with own datasource (matches TB template pattern)
            TOOLTIP_FN = (
                "var lift = data['lift_type'] || 'N/A';\n"
                "var status = data['status'] || 'N/A';\n"
                "var flow = data['flow_rate_bpd'] ? Number(data['flow_rate_bpd']).toFixed(0) : '--';\n"
                "var field = data['field_name'] || 'N/A';\n"
                "var liftColors = {'ESP':'#4CAF50','SRP':'#2196F3','PCP':'#FF9800','gas_lift':'#9C27B0'};\n"
                "var liftColor = liftColors[lift] || '#607D8B';\n"
                "var statusColor = status === 'producing' ? '#4CAF50' : '#F44336';\n"
                "var statusLabel = status === 'producing' ? 'Produciendo' : 'Detenido';\n"
                "return '<div style=\"font-family:Roboto,sans-serif;padding:12px;min-width:200px;\">' +\n"
                "  '<div style=\"font-weight:700;font-size:15px;color:#1a2332;margin-bottom:8px;border-bottom:1px solid #eee;padding-bottom:6px;\">${entityName}</div>' +\n"
                "  '<div style=\"display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:12px;color:#555;\">' +\n"
                "    '<span style=\"color:#999;\">Tipo</span><span style=\"display:inline-block;padding:2px 8px;border-radius:10px;background:'+liftColor+';color:#fff;font-size:10px;font-weight:600;\">' + lift + '</span>' +\n"
                "    '<span style=\"color:#999;\">Campo</span><span>' + field + '</span>' +\n"
                "    '<span style=\"color:#999;\">Produccion</span><span style=\"font-weight:600;\">' + flow + ' BPD</span>' +\n"
                "    '<span style=\"color:#999;\">Estado</span><span style=\"color:'+statusColor+';font-weight:600;\">' + statusLabel + '</span>' +\n"
                "  '</div>' +\n"
                "  '<div style=\"margin-top:8px;text-align:center;\"><link-act name=\"ver-detalle\">Ver Detalle &rarr;</link-act></div></div>';"
            )
            COLOR_FN = (
                "var lift = data['lift_type'];\n"
                "if (lift === 'ESP') return '#4CAF50';\n"
                "if (lift === 'SRP') return '#2196F3';\n"
                "if (lift === 'PCP') return '#FF9800';\n"
                "if (lift === 'gas_lift' || lift === 'Gas Lift') return '#9C27B0';\n"
                "return '#607D8B';"
            )
            s["markers"] = [{
                "dsType": "entity",
                "dsLabel": "",
                "dsDeviceId": None,
                "dsEntityAliasId": ALIAS_ALL,
                "dsFilterId": FILTER_ID,
                "additionalDataSources": None,
                "additionalDataKeys": [
                    {"name": "lift_type", "type": "attribute", "label": "lift_type", "color": "#2196f3", "settings": {}},
                    {"name": "status", "type": "attribute", "label": "status", "color": "#2196f3", "settings": {}},
                    {"name": "field_name", "type": "attribute", "label": "field_name", "color": "#2196f3", "settings": {}},
                    {"name": "flow_rate_bpd", "type": "timeseries", "label": "flow_rate_bpd", "color": "#4CAF50", "settings": {}},
                ],
                "xKey": {"name": "latitude", "type": "attribute", "label": "latitude", "color": "#2196f3", "settings": {}},
                "yKey": {"name": "longitude", "type": "attribute", "label": "longitude", "color": "#2196f3", "settings": {}},
                "markerType": "shape",
                "markerShape": {"shape": "markerShape1", "size": 28,
                    "color": {"type": "function", "color": "#4CAF50",
                        "colorFunction": COLOR_FN}},
                "markerIcon": {"iconContainer": "iconContainer1", "icon": "mdi:oil", "size": 28,
                    "color": {"type": "constant", "color": "#4CAF50"}},
                "markerImage": {"type": "default", "image": "/assets/markers/shape1.svg", "imageSize": 34,
                    "imageFunction": "", "images": []},
                "markerOffsetX": 0.5,
                "markerOffsetY": 1,
                "markerClustering": {"enable": False},
                "label": {"show": False, "type": "pattern", "pattern": "${entityName}", "patternFunction": None},
                "tooltip": {
                    "show": True, "type": "function",
                    "pattern": "<b>${entityName}</b><br/><b>Tipo:</b> ${lift_type}<br/><b>Produccion:</b> ${flow_rate_bpd} BPD",
                    "patternFunction": TOOLTIP_FN,
                    "trigger": "hover", "autoclose": True,
                    "offsetX": 0, "offsetY": -1,
                    "tagActions": [{"name": "ver-detalle", "type": "custom",
                        "customFunction": NAV_JS_MAP,
                        "setEntityId": True, "stateEntityParamName": None,
                        "openRightLayout": False, "openInSeparateDialog": False,
                        "openInPopover": False}],
                },
                "click": {"type": "doNothing"},
                "groups": None,
                "edit": {"enabledActions": [], "attributeScope": "SERVER_SCOPE", "snappable": False},
            }]
            s["fitMapBounds"] = True
            s["useDefaultCenterPosition"] = True
            s["defaultCenterPosition"] = "9.3,-66.9"
            s["defaultZoomLevel"] = 8
            s["mapPageSize"] = 16384
            w["config"]["settings"] = s
            w["config"]["showTitle"] = True
            w["config"]["title"] = "Mapa de Campo"
            w["config"]["titleStyle"] = {"fontSize": "16px", "fontWeight": "500"}
            w["config"]["borderRadius"] = "8px"
            w["config"]["dropShadow"] = True

        widgets[wid_key] = w

    states["default"] = old_states["default"]

    # ── Helper: register widget with top-level id/row/col (TB requirement) ──
    def add_widget(wid, widget, row, col, sx, sy):
        """Add widget to dict with top-level id, row, col, sizeX, sizeY matching TB template format."""
        widget["id"] = wid
        widget["row"] = row
        widget["col"] = col
        widget["sizeX"] = sx
        widget["sizeY"] = sy
        widgets[wid] = widget
        return {"row": row, "col": col, "sizeX": sx, "sizeY": sy}

    # ── DETAIL STATES per well type ─────────────────────────────────
    for wtype, cfg in WELL_TYPES.items():
        layout = {}

        # Back + Title
        bid = uid()
        layout[bid] = add_widget(bid, build_back(), 0, 0, 3, 2)

        tid = uid()
        layout[tid] = add_widget(tid, build_title(wtype.upper().replace("_", " "), cfg["color"]), 0, 3, 21, 2)

        # KPIs
        nk = len(cfg["kpis"])
        kw = max(4, 24 // nk)
        for i, kpi in enumerate(cfg["kpis"]):
            kid = uid()
            w = build_kpi(kpi["key"], kpi["label"], kpi["units"], kpi["icon"], kpi["color"], kpi["dec"])
            layout[kid] = add_widget(kid, w, 2, i * kw, kw, 3)

        # Main chart
        chart_keys = [{"key": k["key"], "label": k["label"], "u": k["units"], "c": k["color"],
                       "y": "left" if i < 2 else "right"} for i, k in enumerate(cfg["kpis"][:4])]
        cid = uid()
        c = build_chart(f"Tendencia - {wtype.upper().replace('_',' ')}", chart_keys)
        layout[cid] = add_widget(cid, c, 5, 0, 24, 8)

        # Systems label
        slid = uid()
        slw = {
            "typeFullFqn": "system.cards.markdown_card", "type": "latest", "sizeX": 3, "sizeY": 2,
            "config": {"datasources": [], "showTitle": False, "backgroundColor": "rgba(0,0,0,0)", "padding": "4px",
                "settings": {"useMarkdownTextFunction": False,
                    "markdownTextPattern": '<div style="display:flex;align-items:center;height:100%;padding:8px;font-family:Roboto,sans-serif;font-size:14px;font-weight:600;color:#333;">Sistemas</div>'},
                "dropShadow": False, "enableFullscreen": False}
        }
        layout[slid] = add_widget(slid, slw, 13, 0, 3, 2)

        # System buttons
        ns = len(cfg["systems"])
        bw = max(3, 21 // ns)
        for i, s in enumerate(cfg["systems"]):
            sbid = uid()
            layout[sbid] = add_widget(sbid, build_btn(s["name"], s["icon"], s["color"], s["sid"]), 13, 3 + i * bw, bw, 2)

        states[cfg["state_id"]] = {
            "name": "${entityName} - " + wtype.upper().replace("_", " "),
            "root": False,
            "layouts": {"main": {
                "widgets": layout,
                "gridSettings": {"backgroundColor": "#f5f7fa", "columns": 24, "margin": 8,
                    "outerMargin": True, "backgroundSizeMode": "100%", "layoutType": "default",
                    "autoFillHeight": False, "rowHeight": 70}
            }}
        }

    # ── MODAL STATES with charts ────────────────────────────────────
    for wtype, cfg in WELL_TYPES.items():
        for s in cfg["systems"]:
            cid = uid()
            c = build_chart(f"{s['name']} - {wtype.upper().replace('_',' ')}", s["keys"])
            layout_m = {}
            layout_m[cid] = add_widget(cid, c, 0, 0, 24, 10)
            states[s["sid"]] = {
                "name": s["name"], "root": False,
                "layouts": {"main": {
                    "widgets": layout_m,
                    "gridSettings": {"backgroundColor": "#fff", "columns": 24, "margin": 8,
                        "outerMargin": True, "backgroundSizeMode": "100%", "layoutType": "default"}
                }}
            }

    # ── Assemble ────────────────────────────────────────────────────
    dash["configuration"]["widgets"] = widgets
    dash["configuration"]["states"] = states
    # Add dashboard CSS
    if "settings" not in dash["configuration"]:
        dash["configuration"]["settings"] = {}
    dash["configuration"]["settings"]["stateControllerId"] = "entity"
    dash["configuration"]["settings"]["showTitle"] = False
    dash["configuration"]["settings"]["showDashboardsSelect"] = True
    dash["configuration"]["settings"]["showEntitiesSelect"] = True
    dash["configuration"]["settings"]["showDashboardTimewindow"] = True
    dash["configuration"]["settings"]["showDashboardExport"] = True
    dash["configuration"]["settings"]["toolbarAlwaysOpen"] = True
    dash["configuration"]["settings"]["showFilters"] = True
    dash["configuration"]["settings"]["css"] = DASHBOARD_CSS

    # Ensure table widget has lift_type in its dataKeys for navigation
    for wid_key, w in widgets.items():
        if "entities_table" in w.get("typeFullFqn", ""):
            for ds in w["config"].get("datasources", []):
                dk_names = [dk["name"] for dk in ds.get("dataKeys", [])]
                if "lift_type" not in dk_names:
                    ds.setdefault("dataKeys", []).append({
                        "name": "lift_type", "type": "attribute", "label": "lift_type",
                        "color": "#607d8b", "settings": {"dataKeyType": "server",
                            "columnWidth": "0px", "useCellStyleFunction": False,
                            "cellStyleFunction": "", "useCellContentFunction": False}
                    })

    # Save locally
    out = "/Users/diazhh/Documents/GitHub/atilax_sim_pozos/dash_actual/atilax_-_mapa_de_campo_v2.json"
    with open(out, "w") as f:
        json.dump(dash, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out}")

    # Upload
    r = requests.post(f"{TB_URL}/api/dashboard", json=dash,
        headers={"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    if r.status_code == 200:
        print(f"Uploaded! -> {TB_URL}/dashboards/all/{DASHBOARD_ID}")
    else:
        print(f"Error {r.status_code}: {r.text[:500]}")

    return dash


if __name__ == "__main__":
    build()
