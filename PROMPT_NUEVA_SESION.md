# PROMPT PARA NUEVA SESIÓN - Dashboards Atilax ThingsBoard

## TU MISIÓN

Crear **4 dashboards funcionales** para la plataforma Atilax de monitoreo petrolero en ThingsBoard PE. **PRIMERO planifica, DESPUÉS ejecuta.** No construyas nada hasta tener todo mapeado.

---

## FASE 1: RECONOCIMIENTO (ejecutar ANTES de planificar)

### 1.1 Verificar que el sistema está activo
```bash
ssh 144 'pm2 status && python3 -c "
import requests
TB=\"http://localhost:8080\"
r=requests.post(f\"{TB}/api/auth/login\",json={\"username\":\"well@atilax.io\",\"password\":\"10203040\"})
token=r.json()[\"token\"]
h={\"X-Authorization\":f\"Bearer {token}\"}
wells=requests.get(f\"{TB}/api/tenant/assets?pageSize=3&page=0&type=well\",headers=h).json()[\"data\"]
for w in wells:
    ts=requests.get(f\"{TB}/api/plugins/telemetry/ASSET/{w[\"id\"][\"id\"]}/values/timeseries?keys=flow_rate_bpd\",headers=h).json()
    val=ts.get(\"flow_rate_bpd\",[{}])[0].get(\"value\",\"N/A\") if ts.get(\"flow_rate_bpd\") else \"N/A\"
    print(f\"{w[\"name\"]}: {val} BPD\")
"'
```

### 1.2 Mapear datos reales (ejecutar y guardar output)
```bash
ssh 144 'python3 << "PYEOF"
import requests, json

TB = "http://localhost:8080"
r = requests.post(f"{TB}/api/auth/login", json={"username":"well@atilax.io","password":"10203040"})
token = r.json()["token"]
h = {"X-Authorization": f"Bearer {token}"}

# 1. Telemetry keys por tipo de pozo
wells = requests.get(f"{TB}/api/tenant/assets?pageSize=100&page=0&type=well", headers=h).json()["data"]
types_seen = {}
for w in wells:
    wid = w["id"]["id"]
    attrs = {a["key"]: a["value"] for a in requests.get(f"{TB}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE", headers=h).json()}
    lt = attrs.get("lift_type", "unknown")
    if lt not in types_seen:
        keys = requests.get(f"{TB}/api/plugins/telemetry/ASSET/{wid}/keys/timeseries", headers=h).json()
        types_seen[lt] = {"name": w["name"], "keys": sorted(keys), "attrs": sorted(attrs.keys())}
        print(f"\n=== {lt.upper()} ({w['name']}) ===")
        print(f"  Telemetry keys: {sorted(keys)}")
        print(f"  Attributes ({len(attrs)}): {sorted(attrs.keys())}")

# 2. Keys comunes a todos los tipos
print("\n=== INTERSECTION ===")
all_sets = [set(v["keys"]) for v in types_seen.values()]
common = set.intersection(*all_sets) if all_sets else set()
print(f"Common to ALL: {sorted(common)}")
for lt, v in types_seen.items():
    unique = set(v["keys"]) - common
    if unique:
        print(f"  {lt} ONLY: {sorted(unique)}")

# 3. Contar wells por campo/macolla/lift_type
print("\n=== COUNTS ===")
from collections import Counter
fields, macollas, lifts = Counter(), Counter(), Counter()
for w in wells:
    wid = w["id"]["id"]
    attrs = {a["key"]: a["value"] for a in requests.get(f"{TB}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE", headers=h).json()}
    fields[attrs.get("field_name","?")] += 1
    macollas[attrs.get("macolla_name","?")] += 1
    lifts[attrs.get("lift_type","?")] += 1
print(f"By field: {dict(fields)}")
print(f"By macolla: {dict(macollas)}")
print(f"By lift_type: {dict(lifts)}")

# 4. Sample atributos completos de un well
print("\n=== SAMPLE ATTRIBUTES ===")
wid = wells[0]["id"]["id"]
attrs = requests.get(f"{TB}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE", headers=h).json()
for a in sorted(attrs, key=lambda x: x["key"]):
    print(f"  {a['key']} = {json.dumps(a['value'])}")

# 5. Dashboards existentes
print("\n=== EXISTING DASHBOARDS ===")
dashboards = requests.get(f"{TB}/api/tenant/dashboards?pageSize=50&page=0", headers=h).json()["data"]
for d in dashboards:
    print(f"  {d['id']['id']} | {d['title']}")
PYEOF
'
```

### 1.3 Examinar plantillas funcionales
Las plantillas que **ya funcionan** están en el repo local:
```
/Users/diazhh/Documents/GitHub/atilax_sim_pozos/dash_plantillas/
├── temperature_&_humidity.json     # entities_table, time_series_chart, state navigation
├── mine_site_monitoring.json       # aggregated_value_card, entity_count, map, multi-state
├── fuel_level_monitoring.json      # ⭐ FILTROS: user-attribute-driven filters con toggles
└── smart_office.json               # value_card, horizontal_value_card
```

**⚠️ Lee las plantillas ANTES de construir widgets.** Copia `config.settings` completo de cada tipo de widget. Un settings incompleto hace que el widget crashee.

---

## FASE 2: PLANIFICACIÓN (crear plan detallado antes de ejecutar)

### 2.1 Plan de datos por dashboard
Para cada dashboard, mapea:
1. **Qué entity aliases necesita** (tipo de filtro, resolveMultiple, etc.)
2. **Qué filtros dinámicos** (si aplica — ver sección de filtros abajo)
3. **Qué keys de telemetría** usa cada widget (verificar que existen)
4. **Qué atributos** muestra (verificar nombres correctos)
5. **Qué estados** tiene el dashboard (default, detail, etc.)
6. **Qué acciones de navegación** conectan widgets con estados

### 2.2 Plan de widgets por dashboard
Para cada widget, especifica:
- `typeFullFqn` exacto
- `type` (latest/timeseries/alarm)
- `sizeX`, `sizeY`, `row`, `col`
- Keys de datos (verificadas contra el mapeo real)
- Si usa `filterId` y cuál
- Si tiene `actions` (rowClick, etc.)

### 2.3 Escribe el plan como JSON schema
```
Dashboard: "Nombre"
  Estado: default
    Widget 1: typeFullFqn, datos, posición
    Widget 2: ...
  Estado: detail
    Widget 3: ...
  Aliases: [...]
  Filters: [...]
```

**No procedas a FASE 3 hasta que el plan esté completo y revisado.**

---

## FASE 3: EJECUCIÓN (crear dashboards)

Crear cada dashboard como un script Python que:
1. Login a TB
2. Construye el JSON completo del dashboard
3. POST a `/api/dashboard`
4. Verifica que se creó correctamente

**Usar scripts Python (no JSON manual)** porque permite:
- UUIDs generados con `str(uuid.uuid4())`
- Funciones reutilizables para widgets
- Validación antes de enviar

---

## CONTEXTO DEL SISTEMA

### Acceso
```
SSH: ssh 144  (configurado en ~/.ssh/config)
     cd /var/proyectos/atilax_sim_pozos && source .venv/bin/activate

ThingsBoard PE v4.3.0.1PE:
  URL: http://144.126.150.120:8080
  Usuario: well@atilax.io
  Password: 10203040
```

### Arquitectura de Entidades
```
Simulador Python (VPS) → MQTT cada 30s → ThingsBoard PE
                                           ↓
                                Devices (RTUs) ──Manages──> Assets (Wells)
                                Assets: Fields → Macollas → Wells (relación Contains)
```

| Tipo | Cant. | Asset/Device Type | Ejemplo |
|------|-------|------------------|---------|
| Fields | 3 | asset: `field` | Campo Boscan, Campo Cerro Negro, Campo Anaco |
| Macollas | 7 | asset: `macolla` | MAC-BOS-01, MAC-BOS-02, MAC-CNE-01, MAC-CNE-02, MAC-ANA-01, MAC-ANA-02, MAC-ANA-03 |
| Wells | 63 | asset: `well` | CA-MAC-BOS-01-001 |
| RTU ESP | ~20 | device: `rtu_esp` | RTU-CA-MAC-BOS-01-005 |
| RTU SRP | ~15 | device: `rtu_srp` | RTU-CA-MAC-BOS-01-001 |
| RTU Gas Lift | ~15 | device: `rtu_gaslift` | RTU-CA-MAC-BOS-01-002 |
| RTU PCP | ~13 | device: `rtu_pcp` | RTU-CA-MAC-BOS-02-008 |

### Relaciones
- RTU → Well: `Manages`
- Field → Macolla: `Contains`
- Macolla → Well: `Contains`

### Estado actual
- ✅ Simulador: 63 pozos transmitiendo cada 30 seg
- ✅ Propagación: telemetría se copia de RTUs a Wells via rule chain
- ✅ Dashboard "Atilax - Campo Petrolero" (ID: `9dfd1110-054b-11f1-8dfb-fb2fc7314bd7`) creado y funcional
- 🔲 Dashboards pendientes: Macolla, Pozo Individual, Optimización

---

## ⚠️ REGLAS CRÍTICAS DE TB PE v4.3

### Formato de Widgets — OBLIGATORIO
```json
// ✅ CORRECTO — usar SIEMPRE
{
  "typeFullFqn": "system.cards.entities_table",
  "type": "latest",
  "sizeX": 11, "sizeY": 8, "row": 0, "col": 0,
  "id": "uuid-generado",
  "config": { "datasources": [...], "settings": {/*COMPLETO*/}, ... }
}

// ❌ INCORRECTO — NUNCA usar (falla con "Problema al cargar configuración")
{
  "bundleAlias": "cards",
  "typeAlias": "simple_card",
  "isSystemType": true
}
```

### Tabla de typeFullFqn
| typeFullFqn | `type` field | Uso |
|-------------|-------------|-----|
| `system.cards.entities_table` | `"latest"` | Tabla de pozos, atributos |
| `system.time_series_chart` | `"timeseries"` | Gráficos de producción, presión |
| `system.cards.aggregated_value_card` | `"timeseries"` | KPIs con mini chart |
| `system.entity_count` | `"latest"` | Contador de pozos |
| `system.cards.value_card` | `"latest"` | Valor puntual |
| `system.cards.horizontal_value_card` | `"latest"` | Métricas en fila |
| `system.map` | `"latest"` | Mapa de pozos |
| `system.alarm_widgets.alarms_table` | `"alarm"` | Tabla de alarmas |
| `system.cards.update_multiple_attributes` | `"latest"` | Toggle switches para filtros |
| `system.cards.markdown_card` | `"static"` | HTML/CSS para layouts y botones |

### Errores Comunes y Soluciones
| Error | Causa | Solución |
|-------|-------|----------|
| "Problema al cargar la configuración del widget" | Usa `bundleAlias`/`typeAlias` | Usar `typeFullFqn` |
| "Cannot read properties of undefined (reading 'enabled')" | `config.settings` incompleto en time_series_chart | Copiar TODOS los campos de settings de plantilla funcional |
| Valores N/A en aggregated_value_card | Key incorrecta o `aggregationType` mal | Verificar keys con API + usar `aggregationType: "NONE"` en latestDataKeys |
| Dashboard redirige a "/" | Navegación directa por URL | Ir a `/dashboards/all` primero |

### Config.settings de time_series_chart — DEBE ser COMPLETO
El `config.settings` del `time_series_chart` DEBE contener TODAS estas propiedades (leer de plantilla `temperature_&_humidity.json`):
- `yAxis`, `xAxis`, `yAxes` (array), `thresholds`
- `tooltipValueFont`, `tooltipDateFont`, `tooltipBackgroundColor`, `tooltipBackgroundBlur`
- `animation`, `grid` (con `outlineWidth`, `verticalLines`, `horizontalLines`)
- `noAggregationBarWidthSettings`, `comparisonXAxis`
- Si falta CUALQUIERA de estas propiedades → el widget crashea

### Config.settings de aggregated_value_card — DEBE incluir
- `stack`, `fontSize`, `fontColor`, `showTooltip`, `grid`, `xaxis`, `yaxis`
- `shadowSize`, `smoothLines`, `comparisonEnabled`, `showLegend`, `legendConfig`
- `showSubtitle`, `showDate`, `showChart`, `chartColor`, `background`, `padding`

### latestDataKeys en aggregated_value_card
- `aggregationType` DEBE ser `"NONE"` para mostrar valor actual
- Si se pone `"SUM"` o `"AVG"` → muestra N/A

---

## MODELO DE DATOS: TELEMETRÍA

### Telemetría por Tipo de Pozo (verificado Feb 2026)

| Key | ESP | SRP | Gas Lift | PCP | Unidad | Descripción |
|-----|-----|-----|----------|-----|--------|-------------|
| `flow_rate_bpd` | ✅ | ✅ | ✅ | ✅ | BPD | Tasa de producción |
| `last_telemetry_ts` | ✅ | ✅ | ✅ | ✅ | ms | Timestamp |
| `motor_current_a` | ✅ | ✅ | ❌ | ✅ | A | Corriente motor |
| `motor_power_kw` | ✅ | ✅ | ❌ | ✅ | kW | Potencia motor |
| `tubing_pressure_psi` | ✅ | ✅ | ❌ | ✅ | PSI | Presión tubing |
| `casing_pressure_psi` | ✅ | ✅ | ❌ | ✅ | PSI | Presión casing |
| `frequency_hz` | ✅ | ❌ | ❌ | ❌ | Hz | Frecuencia VSD |
| `motor_temperature_f` | ✅ | ❌ | ❌ | ❌ | °F | Temp. motor |
| `motor_voltage_v` | ✅ | ❌ | ❌ | ❌ | V | Voltaje motor |
| `intake_pressure_psi` | ✅ | ❌ | ❌ | ✅ | PSI | Presión admisión |
| `discharge_pressure_psi` | ✅ | ❌ | ❌ | ❌ | PSI | Presión descarga |
| `vibration_ips` | ✅ | ❌ | ❌ | ❌ | IPS | Vibración |
| `wellhead_temperature_f` | ✅ | ❌ | ❌ | ❌ | °F | Temp. cabezal |
| `spm` | ❌ | ✅ | ❌ | ❌ | SPM | Golpes/min |
| `pump_fillage_pct` | ❌ | ✅ | ❌ | ❌ | % | Llenado bomba |
| `load_lb` | ❌ | ✅ | ❌ | ❌ | lb | Carga pulido |
| `speed_rpm` | ❌ | ❌ | ❌ | ✅ | RPM | Velocidad rotor |
| `motor_torque_ftlb` | ❌ | ❌ | ❌ | ✅ | ft·lb | Torque motor |

**⚠️ Keys que NO EXISTEN**: `pump_efficiency_pct`, `motor_temp_f`, `thp_psi`

### Atributos de Server Scope (todas las wells)

| Categoría | Keys |
|-----------|------|
| **Identificación** | `well_name`, `field_name`, `macolla_name`, `lift_type`, `status`, `well_code_pdvsa` |
| **Yacimiento** | `reservoir_pressure_psi`, `reservoir_temperature_f`, `bubble_point_psi`, `api_gravity`, `gor_scf_stb`, `water_cut_initial_pct`, `oil_viscosity_cp`, `bo_factor`, `productivity_index_bpd_psi`, `ipr_model`, `ipr_qmax_bpd`, `drive_mechanism` |
| **Mecánica** | `total_depth_md_ft`, `total_depth_tvd_ft`, `pump_depth_ft`, `perforations_top_ft`, `perforations_bottom_ft`, `casing_od_in`, `casing_id_in`, `tubing_od_in`, `tubing_id_in`, `completion_type` |
| **ESP** | `esp_pump_stages`, `esp_design_rate_bpd`, `esp_design_head_ft`, `esp_bep_rate_bpd`, `esp_efficiency_at_bep`, `esp_motor_hp`, `esp_motor_voltage_v`, `esp_motor_amperage_a`, `esp_vsd_installed`, `esp_vsd_nominal_hz` |
| **Optimización** | `opt_last_run`, `opt_current_operating_point_bpd`, `opt_recommended_rate_bpd`, `opt_potential_gain_bpd`, `opt_potential_gain_percent`, `opt_recommended_action`, `opt_efficiency_percent`, `opt_specific_energy_kwh_bbl`, `opt_well_health_score`, `opt_status`, `opt_decline_rate_monthly_percent`, `opt_cluster_id`, `opt_similar_wells` |

---

## SISTEMA DE FILTROS DINÁMICOS (patrón aprendido de Fuel Level Monitoring)

### Arquitectura de Filtros User-Attribute-Driven

ThingsBoard PE soporta **filtros dinámicos** que leen valores de atributos del usuario actual (`CURRENT_USER`) para filtrar entidades. Este es el patrón:

#### Paso 1: Cada entidad tiene un atributo calculado con keywords
Ejemplo: cada well podría tener un atributo `filterTag` con valores como `"active"`, `"alarm"`, `"inactive"`, `"esp"`, `"srp"`, etc. Esto se setea via rule chain o API.

#### Paso 2: Crear toggles que escriben atributos al usuario actual
Widget `update_multiple_attributes` con entity alias `Current User` (`singleEntity` → `CURRENT_USER`):
```json
{
  "typeFullFqn": "system.cards.update_multiple_attributes",
  "type": "latest",
  "config": {
    "datasources": [{
      "type": "entity",
      "entityAliasId": "alias-current-user",
      "dataKeys": [{
        "name": "filterActive",
        "type": "attributes",
        "label": "Pozos Activos",
        "settings": {
          "dataKeyValueType": "booleanSwitch",
          "setValueFunctionBody": "return value ? 'active' : 'unset';"
        }
      }]
    }]
  }
}
```

#### Paso 3: El filtro del dashboard lee del usuario y compara con la entidad
```json
{
  "id": "filter-uuid",
  "filter": "Well Status Filter",
  "keyFilters": [{
    "key": { "type": "ATTRIBUTE", "key": "filterTag" },
    "valueType": "STRING",
    "predicates": [{
      "keyFilterPredicate": {
        "operation": "OR",
        "type": "COMPLEX",
        "predicates": [
          {
            "keyFilterPredicate": {
              "operation": "CONTAINS",
              "type": "STRING",
              "value": {
                "defaultValue": "active",
                "dynamicValue": {
                  "sourceType": "CURRENT_USER",
                  "sourceAttribute": "filterActive"
                }
              }
            }
          }
        ]
      }
    }]
  }]
}
```

#### Paso 4: Widgets referencian el filtro con `filterId`
```json
"datasources": [{
  "type": "entity",
  "entityAliasId": "alias-todos-los-pozos",
  "filterId": "filter-uuid",
  "dataKeys": [...]
}]
```

#### Paso 5: Botones Enable/Disable All (Markdown card)
Se puede crear un `markdown_card` con botones HTML que usan `elementClick` action para setear todos los atributos del usuario de una vez via `attributeService.saveEntityAttributes()`.

### Entity Alias Patterns
```json
// Todos los wells (para tablas, mapas)
{ "type": "assetType", "resolveMultiple": true, "assetType": "well" }

// Usuario actual (para filtros)
{ "type": "singleEntity", "singleEntity": { "entityType": "CURRENT_USER", "id": "13814000-1dd2-11b2-8080-808080808080" } }

// Well seleccionado (para drill-down)
{ "type": "stateEntity", "resolveMultiple": false }

// Wells de una macolla (via relación)
{ "type": "relationsQuery", "rootStateEntity": true, "direction": "FROM", "maxLevel": 1,
  "filters": [{"relationType": "Contains", "entityTypes": ["ASSET"]}] }

// Un field específico
{ "type": "singleEntity", "singleEntity": { "entityType": "ASSET", "id": "field-uuid" } }
```

### Navegación entre Estados
```json
"actions": {
  "rowClick": [{
    "name": "Ver Detalle",
    "icon": "more_horiz",
    "type": "openDashboardState",
    "targetDashboardStateId": "well_detail",
    "setEntityId": true,
    "openInSeparateDialog": false
  }]
}
```

Dashboard settings con entity state controller:
```json
"settings": {
  "stateControllerId": "entity",
  "showTitle": false,
  "showDashboardsSelect": true,
  "showEntitiesSelect": true,
  "showDashboardTimewindow": true,
  "toolbarAlwaysOpen": true
}
```

---

## LOS 4 DASHBOARDS A CREAR

### Dashboard 1: "Atilax - Campo Petrolero" — ✅ CREADO
**ID**: `9dfd1110-054b-11f1-8dfb-fb2fc7314bd7`

**Estado default (Vista de Campo)**:
- KPIs: Pozos Activos (entity_count), Producción Total (aggregated_value_card SUM), Presión Tubing Prom., Corriente Prom., Potencia Motor Prom.
- Tabla de 63 pozos (entities_table) con drill-down
- Gráfico de producción (time_series_chart)

**Estado well_detail**:
- Info del pozo (entities_table con atributos)
- Gráficos: Producción+Eficiencia, Parámetros Motor, Presiones

**Filtros potenciales a agregar**: Por campo, por tipo de levantamiento, por estado

---

### Dashboard 2: "Atilax - Vista Macolla" — 🔲 PENDIENTE

**Propósito**: Vista intermedia por macolla con benchmarking entre pozos.

**Estado default**:
| Widget | typeFullFqn | Datos | Pos |
|--------|------------|-------|-----|
| Selector de Macolla | Alias con `assetType: macolla` + entity selector en toolbar | — | toolbar |
| KPI: Pozos en Macolla | `system.entity_count` | count via relationsQuery | 0,0 |
| KPI: Producción Macolla | `system.cards.aggregated_value_card` | `flow_rate_bpd` SUM | 0,4 |
| KPI: Producción Promedio | `system.cards.aggregated_value_card` | `flow_rate_bpd` AVG | 0,8 |
| Tabla Pozos Macolla | `system.cards.entities_table` | well_name, lift_type, flow_rate_bpd, status + filtro | 3,0 |
| Producción por Pozo | `system.time_series_chart` | flow_rate_bpd multilinea por well | 3,9 |
| Ranking Producción | `system.cards.entities_table` | Ordenado por flow_rate_bpd desc | 11,0 |

**Aliases necesarios**:
- "Todas las Macollas": `assetType: macolla, resolveMultiple: true`
- "Macolla Actual": `stateEntity` (se selecciona con entity selector)
- "Pozos de Macolla": `relationsQuery` desde stateEntity, dirección FROM, relación Contains
- "Current User": `singleEntity → CURRENT_USER`

**Filtros**: Toggle por tipo de levantamiento (ESP, SRP, Gas Lift, PCP), toggle por estado (Activo, Inactivo)

**Navegación**: Tabla de pozos → rowClick → well_detail state (o navegar al Dashboard Pozo Individual)

---

### Dashboard 3: "Atilax - Pozo Individual" — 🔲 PENDIENTE

**Propósito**: Análisis completo de un pozo individual — perfil de producción, condiciones operativas, optimización, alarmas.

**Estado default** (recibe well entity via state navigation):
| Widget | typeFullFqn | Datos |
|--------|------------|-------|
| Info General | `system.cards.entities_table` | well_name, field_name, macolla_name, lift_type, status, well_code_pdvsa |
| Info Yacimiento | `system.cards.entities_table` | reservoir_pressure_psi, reservoir_temperature_f, api_gravity, gor_scf_stb, water_cut_initial_pct, ipr_qmax_bpd |
| Info Mecánica | `system.cards.entities_table` | total_depth_md_ft, pump_depth_ft, perforations_top/bottom, casing/tubing dims |
| Producción (time series) | `system.time_series_chart` | flow_rate_bpd (últimas 24h-7d) |
| Presiones (time series) | `system.time_series_chart` | tubing_pressure_psi, casing_pressure_psi, intake_pressure_psi (si aplica) |
| Motor (time series) | `system.time_series_chart` | motor_current_a, motor_power_kw, motor_temperature_f (si ESP) |
| KPI: Producción Actual | `system.cards.value_card` | flow_rate_bpd latest |
| KPI: Salud del Pozo | `system.cards.value_card` | opt_well_health_score (atributo) |
| KPI: Eficiencia | `system.cards.value_card` | opt_efficiency_percent (atributo) |
| Recomendación | `system.cards.value_card` o entities_table | opt_recommended_action, opt_recommended_rate_bpd, opt_potential_gain_bpd |
| Alarmas | `system.alarm_widgets.alarms_table` | Alarmas de esta entidad |
| Equipo ESP/SRP/PCP | `system.cards.entities_table` | esp_pump_stages, esp_design_rate_bpd, etc. (condicional al lift_type) |

**Aliases necesarios**:
- "Pozo Actual": `stateEntity`

**Navegación**: Este dashboard se abre desde los otros dashboards con `openDashboardState` + `setEntityId: true`, o con `openDashboard` apuntando a este dashboard con la entidad seleccionada.

---

### Dashboard 4: "Atilax - Optimización de Campo" — 🔲 PENDIENTE

**Propósito**: Vista de oportunidades de optimización a nivel de campo.

**Estado default**:
| Widget | typeFullFqn | Datos |
|--------|------------|-------|
| KPI: Ganancia Potencial Total | `system.cards.aggregated_value_card` | opt_potential_gain_bpd SUM (atributo) |
| KPI: Pozos con Recomendación | `system.entity_count` | Filtrar wells con opt_status != null |
| KPI: Health Score Promedio | `system.cards.aggregated_value_card` | opt_well_health_score AVG |
| Ranking Oportunidades | `system.cards.entities_table` | well_name, opt_potential_gain_bpd, opt_recommended_action, opt_status — ordenado desc |
| Actual vs Potencial | `system.time_series_chart` o entities_table | opt_current_operating_point_bpd vs opt_recommended_rate_bpd |
| Health Score por Pozo | `system.cards.entities_table` | well_name, opt_well_health_score, opt_efficiency_percent — color coded |
| Clustering | `system.cards.entities_table` | well_name, opt_cluster_id, opt_similar_wells |
| Energía Específica | `system.cards.entities_table` | well_name, opt_specific_energy_kwh_bbl — eficiencia energética |
| Decline Rate | `system.cards.entities_table` | well_name, opt_decline_rate_monthly_percent — tasa de declinación |

**Aliases**: "Todos los Pozos" con `assetType: well, resolveMultiple: true`

**Filtros**: Toggle por campo, toggle por tipo de levantamiento, toggle por health score (alto/medio/bajo)

**Nota**: Los datos de optimización están en atributos `opt_*` (SERVER_SCOPE), NO en telemetría. Usar `type: "attribute"` en dataKeys, no `type: "timeseries"`.

---

## API DE THINGSBOARD

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"well@atilax.io","password":"10203040"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Assets
curl -s "http://localhost:8080/api/tenant/assets?pageSize=100&page=0&type=well" -H "X-Authorization: Bearer $TOKEN"

# Telemetry keys
curl -s "http://localhost:8080/api/plugins/telemetry/ASSET/$ID/keys/timeseries" -H "X-Authorization: Bearer $TOKEN"

# Telemetry values
curl -s "http://localhost:8080/api/plugins/telemetry/ASSET/$ID/values/timeseries?keys=flow_rate_bpd" -H "X-Authorization: Bearer $TOKEN"

# Attributes
curl -s "http://localhost:8080/api/plugins/telemetry/ASSET/$ID/values/attributes/SERVER_SCOPE" -H "X-Authorization: Bearer $TOKEN"

# Create/Update dashboard
curl -s -X POST http://localhost:8080/api/dashboard \
  -H "X-Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d @dashboard.json

# Get dashboard
curl -s "http://localhost:8080/api/dashboard/$DASH_ID" -H "X-Authorization: Bearer $TOKEN"
```

---

## ARCHIVOS DEL PROYECTO

### Repo Local
```
/Users/diazhh/Documents/GitHub/atilax_sim_pozos/
├── dash_plantillas/          # ✅ Plantillas TB funcionales (REFERENCIA OBLIGATORIA)
├── dashboard/                # ❌ JSONs originales (formato incorrecto, NO usar)
├── rules/                    # Rule Chains
├── tb_client/                # Cliente TB
├── models/                   # Modelos físicos
├── generators/               # Generadores
├── scenarios/                # Escenarios
├── config/                   # Config YAML
└── main.py
```

### VPS
```
/var/proyectos/atilax_sim_pozos/   # Código + venv
/tmp/create_campo_dashboard.py     # ✅ Script referencia (creó dashboard campo exitosamente)
```

### Rule Chains (todas ✅ funcionando)
| Chain | Función |
|-------|---------|
| Ingesta y Normalización (Root) | Recibe telemetría MQTT, normaliza, distribuye |
| Propagación Device→Asset | Copia telemetría de RTU a Well via relación Manages |
| Alarmas Operativas | Genera alarmas basadas en umbrales |
| Publicación a Kafka | Publica a topics Kafka |
| Resultados de Optimización | Procesa resultados de optimización |

---

## CHECKLIST FINAL

Antes de ejecutar cada dashboard:
- [ ] ¿Verificaste las keys de telemetría con el script de la Fase 1?
- [ ] ¿Leíste las plantillas funcionales (`dash_plantillas/`)?
- [ ] ¿Cada widget usa `typeFullFqn` (nunca bundleAlias)?
- [ ] ¿Los `config.settings` de time_series_chart son COMPLETOS (copiados de plantilla)?
- [ ] ¿Los `latestDataKeys` tienen `aggregationType: "NONE"`?
- [ ] ¿Los nombres de keys son correctos (no `pump_efficiency_pct`, no `motor_temp_f`)?
- [ ] ¿Los filtros dinámicos tienen la estructura correcta con `dynamicValue.sourceType: "CURRENT_USER"`?
- [ ] ¿Las acciones de navegación usan `setEntityId: true`?
- [ ] ¿El plan está completo antes de crear el script?
