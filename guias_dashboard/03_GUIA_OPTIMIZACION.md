# Guia Paso a Paso: Dashboard "Optimizacion de Campo" en ThingsBoard PE v4.3

## Sistema Atilax - Plataforma de Monitoreo y Optimizacion Petrolera

> **Version:** 1.0
> **Fecha:** Febrero 2026
> **Servidor ThingsBoard:** `http://144.126.150.120:8080`
> **Usuario:** `well@atilax.io` / **Password:** `10203040`

---

## Tabla de Contenidos

1. [Introduccion y Contexto](#1-introduccion-y-contexto)
2. [Modelo de Datos de Optimizacion](#2-modelo-de-datos-de-optimizacion)
3. [PASO 1: Crear Dashboard y Configuracion General](#3-paso-1-crear-dashboard-y-configuracion-general)
4. [PASO 2: Configurar Entity Aliases](#4-paso-2-configurar-entity-aliases)
5. [PASO 3: Estado Principal - Resumen de Optimizacion](#5-paso-3-estado-principal---resumen-de-optimizacion)
6. [PASO 4: Estado de Detalle de Optimizacion (opt_detalle)](#6-paso-4-estado-de-detalle-de-optimizacion-opt_detalle)
7. [PASO 5: Preparacion para el Servicio de Optimizacion](#7-paso-5-preparacion-para-el-servicio-de-optimizacion)
8. [Tips de Implementacion Avanzada](#8-tips-de-implementacion-avanzada)
9. [Referencia Rapida de Atributos](#9-referencia-rapida-de-atributos)

---

## 1. Introduccion y Contexto

### Que es este Dashboard

Este dashboard de **"Optimizacion de Campo"** es la interfaz visual para los resultados del servicio de optimizacion de Atilax. Muestra recomendaciones, scores de salud, oportunidades de ganancia y alertas generadas por los motores de calculo (analisis nodal, optimizadores por tipo de levantamiento, DCA, modelos de ML).

### Estado Actual del Servicio

El servicio de optimizacion esta **en desarrollo**. Esto significa que:

- Todos los atributos `opt_*` existen en los assets de pozo, pero estan inicializados en cero o vacio.
- El dashboard se puede construir **ahora** y estara listo para "cobrar vida" cuando el servicio comience a publicar resultados.
- Los widgets mostraran valores en cero o placeholders hasta que el servicio este activo. **Esto es esperado y no indica un error de configuracion.**
- Los KPIs agregados (SUM, AVG, MIN) mostraran 0 porque todos los atributos `opt_*` estan en 0. Las tablas mostraran filas con valores vacios o en cero. Los color functions mostraran colores de "inactivo" (gris).
- **No se requiere modificar el dashboard** cuando el servicio se active; los datos fluiran automaticamente.

### Flujo de Datos

```
Pozos (Assets) ──telemetria──> Kafka ──> Servicio de Optimizacion
                                              |
                                              v
                                    Calcula: nodal, eficiencia,
                                    DCA, ML, scoring, anomalias
                                              |
                                              v
                              Publica resultados como SERVER_SCOPE
                              attributes (opt_*) en cada pozo
                                              |
                                              v
                              Este Dashboard lee y visualiza
                              esos atributos automaticamente
```

### Motores de Optimizacion

| Motor | Descripcion | Frecuencia |
|-------|-------------|------------|
| `nodal_analysis` | Analisis nodal (IPR/VLP) | Cada hora |
| `esp_optimizer` | Optimizador ESP (frecuencia, punto operacion) | Cada hora |
| `srp_optimizer` | Optimizador SRP (SPM, contrapeso) | Cada hora |
| `gaslift_optimizer` | Optimizador Gas Lift (inyeccion, valvulas) | Cada hora |
| `pcp_optimizer` | Optimizador PCP (velocidad, torque) | Cada hora |
| `decline_analysis` | Analisis de declive (Arps) | Diario |
| `field_optimizer` | Optimizador de campo (distribucion recursos) | Diario |
| `well_health` | Salud del pozo (scoring) | Diario |
| `energy_optimizer` | Optimizacion energetica | Diario |

### Modelos de ML

| Modelo | Descripcion | Frecuencia |
|--------|-------------|------------|
| `production_forecast` | Pronostico de produccion | Diario |
| `anomaly_detector` | Detector de anomalias | Cada 5 min |
| `esp_failure_predictor` | Predictor de falla ESP | Diario |
| `dynamo_classifier` | Clasificador de dinamometros | Cada 15 min |
| `virtual_flow_meter` | Medidor de flujo virtual | Tiempo real |
| `well_clustering` | Agrupamiento de pozos | Semanal |

---

## 2. Modelo de Datos de Optimizacion

### Atributos de Resultado (SERVER_SCOPE en asset "well")

Estos son los atributos que el servicio de optimizacion publicara en cada pozo. Todos son de tipo `SERVER_SCOPE`.

#### Atributos Generales

| Atributo | Tipo | Descripcion | Ejemplo |
|----------|------|-------------|---------|
| `opt_status` | str | Estado de optimizacion | "optimized", "suboptimal", "pending", "error", "not_analyzed" |
| `opt_current_rate_bpd` | float | Tasa actual calculada | 850 |
| `opt_recommended_rate_bpd` | float | Tasa recomendada | 1050 |
| `opt_potential_gain_bpd` | float | Ganancia potencial | 200 |
| `opt_recommended_action` | str | Accion recomendada | "increase_frequency" |
| `opt_recommended_action_detail` | str | Detalle de la accion | "Incrementar frecuencia VSD de 58 Hz a 65 Hz" |
| `opt_efficiency_pct` | float | Eficiencia del sistema (0-100) | 72 |
| `opt_energy_kwh_bbl` | float | Consumo energetico por barril | 8.5 |
| `opt_well_health_score` | float | Score de salud del pozo (0-100) | 68 |
| `opt_decline_rate_monthly_pct` | float | Tasa de declive mensual | 2.1 |
| `opt_eur_mstb` | float | Reservas remanentes estimadas (MSTB) | 450 |
| `opt_days_to_predicted_failure` | float | Dias para falla predicha | 120 |
| `opt_failure_probability` | float | Probabilidad de falla (0-1) | 0.12 |
| `opt_cluster_id` | str | Cluster de pozo similar | "3" |
| `opt_similar_wells` | str | Pozos similares (JSON array) | '["BOS-1207","BOS-1312"]' |
| `opt_anomaly_score` | float | Score de anomalia (0-1) | 0.15 |
| `opt_anomaly_type` | str | Tipo de anomalia detectada | "sensor_drift" |

#### Atributos de Curvas (JSON para graficos)

| Atributo | Tipo | Descripcion |
|----------|------|-------------|
| `opt_nodal_ipr_curve` | str (JSON) | Curva IPR: `[[q1,pwf1],[q2,pwf2],...]` |
| `opt_nodal_vlp_curve` | str (JSON) | Curva VLP: `[[q1,pwf1],[q2,pwf2],...]` |
| `opt_dca_forecast` | str (JSON) | Pronostico DCA: `[["2025-03",830],["2025-04",815],...]` |
| `opt_glpc_curve` | str (JSON) | Curva GLPC (solo Gas Lift): `[[qgl1,qo1],[qgl2,qo2],...]` |

#### Atributos Especificos por Tipo de Levantamiento

| Atributo | Tipo | Aplica a | Descripcion |
|----------|------|----------|-------------|
| `opt_recommended_frequency_hz` | float | ESP | Frecuencia recomendada |
| `opt_current_operating_point_bpd` | float | ESP | Punto de operacion actual |
| `opt_recommended_spm` | float | SRP | SPM recomendado |
| `opt_recommended_injection_rate_mcfd` | float | Gas Lift | Tasa de inyeccion recomendada |
| `opt_recommended_speed_rpm` | float | PCP | Velocidad recomendada |

### Tipos de Alarma de Optimizacion

| Tipo de Alarma | Severidad | Condicion |
|----------------|-----------|-----------|
| `WELL_SUBOPTIMAL` | WARNING | Pozo opera >20% debajo del potencial |
| `PUMP_DEGRADATION` | MAJOR | Eficiencia de bomba <55% |
| `ACCELERATED_DECLINE` | WARNING | Declive >5%/mes |
| `ESP_FAILURE_PREDICTED` | CRITICAL | Probabilidad falla >70% |
| `ANOMALY_DETECTED` | WARNING/MAJOR | Score anomalia >0.8 |
| `CASING_HEADING` | WARNING | Cabeceo de casing detectado |
| `LIFT_METHOD_REVIEW` | INFO | Candidato a cambio de levantamiento |

---

## 3. PASO 1: Crear Dashboard y Configuracion General

### 3.1 Crear el Dashboard

1. Ir a **Dashboards** en el menu lateral izquierdo.
2. Click en el boton **"+"** (esquina inferior derecha).
3. Seleccionar **"Create new dashboard"**.
4. Completar:
   - **Title:** `Atilax - Optimizacion de Campo`
   - **Description:** `Dashboard de resultados del servicio de optimizacion. Muestra recomendaciones, scores de salud, oportunidades de ganancia y alertas para todos los pozos del campo.`
5. Click en **"Add"**.

### 3.2 Configurar Settings del Dashboard

1. Abrir el dashboard creado.
2. Click en el icono de **lapiz** (Edit mode) en la esquina inferior derecha.
3. Click en el icono de **engranaje** (Dashboard settings) en la barra superior.

Configurar:

| Opcion | Valor |
|--------|-------|
| State controller | `entity` |
| Toolbar | Always open |
| Display dashboard timewindow | Si (activado) |
| Display dashboard export | Si |
| Display dashboard update | Si |
| Display entities selection | Si |

4. Click en **"Save"**.

### 3.3 Agregar CSS Personalizado

1. En modo edicion, click en el icono de **engranaje** (Dashboard settings).
2. Ir a la seccion **"Custom CSS"** o **"Advanced"** segun la version.
3. Pegar el siguiente CSS:

```css
.tb-widget-container > .tb-widget {
    border-radius: 8px;
    box-shadow: 0px 2px 8px rgba(222, 223, 224, 0.25);
}

.tb-dashboard-page .tb-widget-container > .tb-widget {
    color: #4B535B !important;
}

/* Estilos especificos de optimizacion */
.opt-score-high {
    color: #4CAF50;
    font-weight: 700;
}

.opt-score-medium {
    color: #FF9800;
    font-weight: 700;
}

.opt-score-low {
    color: #F44336;
    font-weight: 700;
}

.opt-gain-positive {
    color: #4CAF50;
}

.opt-gain-negative {
    color: #F44336;
}

.opt-action-card {
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 4px solid;
    margin-bottom: 8px;
    background: #F5F7FA;
}

.opt-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}
```

4. Click en **"Apply"** o **"Save"**.

---

## 4. PASO 2: Configurar Entity Aliases

Los Entity Aliases son las fuentes de datos que los widgets usaran. Se deben configurar antes de crear los widgets.

1. En modo edicion del dashboard, click en **"Entity aliases"** (icono de lista en la barra superior).
2. Crear los siguientes aliases:

### Alias 1: "Todos los Pozos"

| Campo | Valor |
|-------|-------|
| Alias name | `Todos los Pozos` |
| Filter type | `Entity list` |
| Entity type | `Asset` |
| Asset type | `well` |
| Resolve as multiple entities | **Si** (activado) |

Click en **"Add"**.

### Alias 2: "Pozo Seleccionado"

| Campo | Valor |
|-------|-------|
| Alias name | `Pozo Seleccionado` |
| Filter type | `Entity from dashboard state` |

> **Nota:** Este alias se resuelve automaticamente cuando el usuario navega a un estado del dashboard que tiene una entidad seleccionada (por ejemplo, al hacer click en una fila de la tabla).

Click en **"Add"**.

### Alias 3: "Pozos con Alarma"

| Campo | Valor |
|-------|-------|
| Alias name | `Pozos con Alarma` |
| Filter type | `Entity list` |
| Entity type | `Asset` |
| Asset type | `well` |
| Resolve as multiple entities | **Si** |

Agregar **Key filter**:
1. Click en **"Add key filter"**.
2. Configurar:
   - **Key:** `opt_anomaly_score`
   - **Key type:** `Attribute` (Server)
   - **Value type:** `Numeric`
   - **Operation:** `Greater than`
   - **Value:** `0.5`

Click en **"Add"**.

### Alias 4: "Pozos Suboptimos"

| Campo | Valor |
|-------|-------|
| Alias name | `Pozos Suboptimos` |
| Filter type | `Entity list` |
| Entity type | `Asset` |
| Asset type | `well` |
| Resolve as multiple entities | **Si** |

Agregar **Key filter**:
1. Click en **"Add key filter"**.
2. Configurar:
   - **Key:** `opt_status`
   - **Key type:** `Attribute` (Server)
   - **Value type:** `String`
   - **Operation:** `Equal`
   - **Value:** `suboptimal`

Click en **"Add"**.

### Alias 5: "Usuario Actual"

| Campo | Valor |
|-------|-------|
| Alias name | `Usuario Actual` |
| Filter type | `Current User` |

Click en **"Add"**.

### Resumen de Aliases

| # | Alias | Tipo | Proposito |
|---|-------|------|-----------|
| 1 | Todos los Pozos | Entity list (well) | Tablas y KPIs agregados |
| 2 | Pozo Seleccionado | Dashboard state | Detalle de un pozo |
| 3 | Pozos con Alarma | Entity list + filter | Pozos con anomalia > 0.5 |
| 4 | Pozos Suboptimos | Entity list + filter | Pozos con status "suboptimal" |
| 5 | Usuario Actual | Current User | Personalizacion |

5. Click en **"Save"** para guardar todos los aliases.

---

## 5. PASO 3: Estado Principal - Resumen de Optimizacion

Este es el estado por defecto del dashboard. Muestra un resumen ejecutivo de la optimizacion de todo el campo.

**Layout:** Grid de 24 columnas.

### 5.1 Header - Titulo del Dashboard

**Posicion:** Row 0, Col 0 | **Tamano:** sizeX: 24, sizeY: 2

1. Click en **"Add new widget"**.
2. Buscar: `Markdown/HTML Value Card` en el bundle `Cards`.
   - Widget exacto: **`system.cards.markdown_card`** (tambien puede aparecer como "HTML Card" o "Markdown/HTML Value Card").
3. Configurar el widget:

**Datasource:** Ninguno requerido (contenido estatico). Si el widget requiere un datasource, usar el alias "Usuario Actual" con cualquier atributo.

**Contenido Markdown/HTML:**

```html
<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 16px;">
    <div>
        <h2 style="margin: 0; color: #305680; font-weight: 700;">Centro de Optimizacion</h2>
        <span style="color: #9FA6B4; font-size: 13px;">Analisis y recomendaciones del servicio de optimizacion</span>
    </div>
    <div style="display: flex; gap: 8px;">
        <div class="opt-badge" style="background: #E8F5E9; color: #4CAF50;">Servicio Activo</div>
    </div>
</div>
```

**Configuracion de apariencia:**

| Opcion | Valor |
|--------|-------|
| Background color | `#FFFFFF` |
| Padding | `0` |
| Show card header | No |
| Show card border | No |

4. Ajustar posicion y tamano en el grid:
   - **col:** 0, **row:** 0
   - **sizeX:** 24, **sizeY:** 2

5. Click en **"Save"** en el widget.

---

### 5.2 KPIs de Resumen (6 tarjetas)

Crear 6 tarjetas de KPI en la fila 3. Cada una ocupa **sizeX: 4, sizeY: 3**.

#### KPI 1: Produccion Potencial Adicional

**Posicion:** Row 3, Col 0 | **Tamano:** sizeX: 4, sizeY: 3

1. **"Add new widget"** > Buscar `Aggregated value card` en el bundle `Cards`.
   - Widget: **`system.cards.aggregated_value_card`**
2. Configurar:

**Datasource:**
- Type: `Entity`
- Entity alias: `Todos los Pozos`
- Data key: `opt_potential_gain_bpd` (tipo: `Attribute`, scope: `Server`)

**Agregacion:**
- Aggregation: `SUM`

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Produccion Potencial Adicional` |
| Subtitle | `Ganancia si se optimizan todos` |
| Units | `BPD` |
| Decimals | `0` |
| Icon | `trending_up` |
| Icon color | `#4CAF50` |
| Value color | `#4CAF50` |

> **Nota importante sobre agregacion:** El datasource usa tipo `Attribute` (Server scope), lo cual significa que el widget obtiene el **ultimo valor** de cada entidad y aplica SUM sobre esos valores. Esto es correcto para sumar `opt_potential_gain_bpd` de todos los pozos. Si en cambio se usara un datasource tipo `Timeseries`, SUM sumaria **todos los data points** en la ventana de tiempo, lo cual daria un resultado incorrecto.
>
> Si el widget `aggregated_value_card` no soporta directamente la funcion de agregacion SUM sobre multiples entidades con atributos, hay dos alternativas:
> - Usar un widget `Value card` con datasource configurado para agregacion.
> - Usar un `Markdown/HTML Value Card` con una funcion JavaScript personalizada que sume los valores.

---

#### KPI 2: Salud Promedio del Campo

**Posicion:** Row 3, Col 4 | **Tamano:** sizeX: 4, sizeY: 3

1. **"Add new widget"** > `Aggregated value card`.
2. Configurar:

**Datasource:**
- Entity alias: `Todos los Pozos`
- Data key: `opt_well_health_score` (Attribute, Server)

**Agregacion:**
- Aggregation: `AVG`

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Salud Promedio del Campo` |
| Units | `/100` |
| Decimals | `1` |
| Icon | `favorite` |

**Color Function (en la seccion Advanced o Value color function):**

```javascript
var score = value;
if (score >= 80) return '#4CAF50';
if (score >= 60) return '#FF9800';
return '#F44336';
```

> Esta funcion colorea el valor en verde si la salud es >= 80, naranja si >= 60, y rojo si < 60.

---

#### KPI 3: Eficiencia Promedio

**Posicion:** Row 3, Col 8 | **Tamano:** sizeX: 4, sizeY: 3

1. **"Add new widget"** > `Aggregated value card`.
2. Configurar:

**Datasource:**
- Entity alias: `Todos los Pozos`
- Data key: `opt_efficiency_pct` (Attribute, Server)

**Agregacion:**
- Aggregation: `AVG`

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Eficiencia Promedio` |
| Units | `%` |
| Decimals | `1` |
| Icon | `speed` |

**Color Function:**

```javascript
var eff = value;
if (eff >= 75) return '#4CAF50';
if (eff >= 55) return '#FF9800';
return '#F44336';
```

---

#### KPI 4: Pozos con Anomalias

**Posicion:** Row 3, Col 12 | **Tamano:** sizeX: 4, sizeY: 3

> **Opcion A:** Usar un widget `Entity count` con el alias "Pozos con Alarma" (que ya esta filtrado por `opt_anomaly_score > 0.5`).

1. **"Add new widget"** > Buscar `Entity count` en el bundle `Cards`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozos con Alarma`

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Pozos con Anomalias` |
| Subtitle | `Score de anomalia > 0.5` |
| Icon | `warning` |
| Icon color | `#F44336` |
| Value color | `#F44336` |

> **Opcion B (alternativa):** Si `Entity count` no esta disponible, usar un `Aggregated value card` con el alias "Pozos con Alarma", data key `entityName` (tipo: **Entity field**, NO timeseries ni attribute), y la agregacion `COUNT`. Es importante usar un Entity field como `entityName` porque COUNT sobre un Entity field cuenta **entidades**, mientras que COUNT sobre un dato de timeseries contaria **data points** en la ventana de tiempo (no entidades).

---

#### KPI 5: Energia Promedio

**Posicion:** Row 3, Col 16 | **Tamano:** sizeX: 4, sizeY: 3

1. **"Add new widget"** > `Aggregated value card`.
2. Configurar:

**Datasource:**
- Entity alias: `Todos los Pozos`
- Data key: `opt_energy_kwh_bbl` (Attribute, Server)

**Agregacion:**
- Aggregation: `AVG`

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Energia Promedio` |
| Units | `kWh/bbl` |
| Decimals | `2` |
| Icon | `bolt` |
| Icon color | `#FF9800` |

---

#### KPI 6: Dias para Falla (Pozo Mas Critico)

**Posicion:** Row 3, Col 20 | **Tamano:** sizeX: 4, sizeY: 3

1. **"Add new widget"** > `Aggregated value card`.
2. Configurar:

**Datasource:**
- Entity alias: `Todos los Pozos`
- Data key: `opt_days_to_predicted_failure` (Attribute, Server)

**Agregacion:**
- Aggregation: `MIN`

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Dias para Falla` |
| Subtitle | `Pozo mas critico` |
| Units | `dias` |
| Decimals | `0` |
| Icon | `report_problem` |

**Color Function:**

```javascript
var days = value;
if (days <= 0 || days === null) return '#9FA6B4';
if (days < 30) return '#F44336';
if (days < 90) return '#FF9800';
return '#4CAF50';
```

> **Nota sobre todos los KPIs de esta seccion:** Todos los datasources usan data keys de tipo **Attribute (Server)**, no Timeseries. Esto es intencional: las agregaciones (SUM, AVG, MIN) se aplican sobre el **ultimo valor del atributo por entidad**. Si se cambiaran a tipo Timeseries, las agregaciones operarian sobre **todos los data points en la ventana de tiempo**, dando resultados incorrectos para KPIs agregados a nivel de campo.

---

### 5.3 Tabla de Recomendaciones

**Posicion:** Row 7, Col 0 | **Tamano:** sizeX: 16, sizeY: 10

Esta es la tabla principal. Muestra todos los pozos con sus resultados de optimizacion, ordenados por ganancia potencial descendente.

1. **"Add new widget"** > Buscar `Entities table` en el bundle `Cards` o `Tables`.
   - Widget: **`system.cards.entities_table`**
2. Configurar:

**Datasource:**
- Type: `Entity`
- Entity alias: `Todos los Pozos`

**Data Keys (columnas):**

Agregar las siguientes claves en orden. Para cada una, click en **"Add"** y configurar:

| # | Data Key | Key Type | Label (titulo columna) |
|---|----------|----------|----------------------|
| 1 | `entityName` | Entity field | `Pozo` |
| 2 | `lift_type` | Attribute (Server) | `Tipo` |
| 3 | `opt_status` | Attribute (Server) | `Estado Opt.` |
| 4 | `opt_well_health_score` | Attribute (Server) | `Salud` |
| 5 | `opt_recommended_action` | Attribute (Server) | `Accion Recomendada` |
| 6 | `opt_potential_gain_bpd` | Attribute (Server) | `Ganancia (BPD)` |
| 7 | `opt_efficiency_pct` | Attribute (Server) | `Eficiencia %` |
| 8 | `opt_anomaly_score` | Attribute (Server) | `Anomalia` |

**Configuracion de columnas:**

Para la columna **"Salud"** (`opt_well_health_score`), configurar **Cell style function**:

1. Click en la columna `opt_well_health_score` en la lista de data keys.
2. Ir a la seccion "Cell style function" o "Advanced".
3. Pegar:

```javascript
var score = Number(value);
if (isNaN(score) || score === 0) {
    return {
        color: '#9FA6B4',
        fontStyle: 'italic'
    };
}
if (score >= 80) {
    return {
        backgroundColor: '#E8F5E9',
        color: '#4CAF50',
        fontWeight: '600',
        borderRadius: '4px',
        padding: '2px 8px'
    };
}
if (score >= 60) {
    return {
        backgroundColor: '#FFF3E0',
        color: '#FF9800',
        fontWeight: '600',
        borderRadius: '4px',
        padding: '2px 8px'
    };
}
return {
    backgroundColor: '#FFEBEE',
    color: '#F44336',
    fontWeight: '600',
    borderRadius: '4px',
    padding: '2px 8px'
};
```

Para la columna **"Accion Recomendada"** (`opt_recommended_action`), configurar **Cell content function**:

1. Click en la columna `opt_recommended_action`.
2. Ir a "Cell content function".
3. Pegar:

```javascript
if (!value || value === '' || value === '0' || value === 0) {
    return '<span style="color:#9FA6B4; font-style: italic;">Sin recomendacion</span>';
}
var icons = {
    'increase_frequency': '<span style="color:#4CAF50;">&#9650; Aumentar frecuencia</span>',
    'decrease_frequency': '<span style="color:#FF9800;">&#9660; Reducir frecuencia</span>',
    'increase_spm': '<span style="color:#4CAF50;">&#9650; Aumentar SPM</span>',
    'decrease_spm': '<span style="color:#FF9800;">&#9660; Reducir SPM</span>',
    'increase_injection': '<span style="color:#4CAF50;">&#9650; Aumentar inyeccion</span>',
    'decrease_injection': '<span style="color:#FF9800;">&#9660; Reducir inyeccion</span>',
    'increase_speed': '<span style="color:#4CAF50;">&#9650; Aumentar RPM</span>',
    'decrease_speed': '<span style="color:#FF9800;">&#9660; Reducir RPM</span>',
    'workover': '<span style="color:#F44336;">&#128295; Workover requerido</span>',
    'review_gaslift': '<span style="color:#2196F3;">&#128260; Revisar inyeccion GL</span>',
    'monitor': '<span style="color:#9FA6B4;">&#128065; Monitorear</span>',
    'no_action': '<span style="color:#4CAF50;">&#10004; Sin accion necesaria</span>'
};
return icons[value] || '<span style="color:#305680;">' + value + '</span>';
```

Para la columna **"Estado Opt."** (`opt_status`), configurar **Cell style function**:

```javascript
if (!value || value === '' || value === '0') {
    return { color: '#9FA6B4', fontStyle: 'italic' };
}
var styles = {
    'optimized': { backgroundColor: '#E8F5E9', color: '#4CAF50', fontWeight: '600', borderRadius: '4px', padding: '2px 8px' },
    'pending': { backgroundColor: '#FFF3E0', color: '#FF9800', fontWeight: '600', borderRadius: '4px', padding: '2px 8px' },
    'error': { backgroundColor: '#FFEBEE', color: '#F44336', fontWeight: '600', borderRadius: '4px', padding: '2px 8px' },
    'not_analyzed': { color: '#9FA6B4', fontStyle: 'italic' },
    'suboptimal': { backgroundColor: '#FFEBEE', color: '#F44336', fontWeight: '600', borderRadius: '4px', padding: '2px 8px' }
};
return styles[value] || { color: '#4B535B' };
```

Para la columna **"Anomalia"** (`opt_anomaly_score`), configurar **Cell style function**:

```javascript
var score = Number(value);
if (isNaN(score) || score === 0) {
    return { color: '#9FA6B4' };
}
if (score >= 0.8) {
    return { backgroundColor: '#FFEBEE', color: '#F44336', fontWeight: '700', borderRadius: '4px', padding: '2px 8px' };
}
if (score >= 0.5) {
    return { backgroundColor: '#FFF3E0', color: '#FF9800', fontWeight: '600', borderRadius: '4px', padding: '2px 8px' };
}
return { color: '#4CAF50' };
```

**Configuracion de la tabla:**

| Opcion | Valor |
|--------|-------|
| Title | `Recomendaciones de Optimizacion` |
| Display pagination | Si |
| Default page size | 15 |
| Default sort order | `opt_potential_gain_bpd` (descendente) |
| Enable search | Si |
| Enable column selection | Si |
| Row style function | (ver abajo) |

**Row style function (opcional, para resaltar filas criticas):**

```javascript
if (entity && entity.opt_anomaly_score && Number(entity.opt_anomaly_score) > 0.8) {
    return { borderLeft: '3px solid #F44336' };
}
return {};
```

**Configurar accion de click en fila:**

1. En la configuracion del widget, ir a **"Actions"**.
2. Click en **"Add action"**.
3. Configurar:

| Campo | Valor |
|-------|-------|
| Action source | `Row click` (o `On row click`) |
| Name | `Ver detalle optimizacion` |
| Action type | `Navigate to new dashboard state` |
| Target dashboard state | `opt_detalle` |
| Set entity from widget | **Si** (activado) |

4. Click en **"Add"**.

> **Importante:** El estado `opt_detalle` se creara en el PASO 4. Por ahora solo se referencia por nombre.

---

### 5.4 Tabla de Alarmas de Optimizacion

**Posicion:** Row 7, Col 16 | **Tamano:** sizeX: 8, sizeY: 10

1. **"Add new widget"** > Buscar `Alarms table` en el bundle `Alarm widgets`.
   - Widget: **`system.alarm_widgets.alarms_table`**
2. Configurar:

**Datasource:**
- Entity alias: `Todos los Pozos`

**Filtros de alarma:**

En la seccion de configuracion del widget, filtrar por tipos de alarma:

| Campo | Valor |
|-------|-------|
| Alarm type list | `WELL_SUBOPTIMAL`, `PUMP_DEGRADATION`, `ACCELERATED_DECLINE`, `ESP_FAILURE_PREDICTED`, `ANOMALY_DETECTED`, `CASING_HEADING`, `LIFT_METHOD_REVIEW` |
| Alarm status list | `ACTIVE_UNACK`, `ACTIVE_ACK` |
| Alarm severity list | Todos (CRITICAL, MAJOR, MINOR, WARNING, INDETERMINATE) |

**Configuracion de la tabla:**

```json
{
    "enableSearch": true,
    "enableFilter": true,
    "allowAcknowledgment": true,
    "allowClear": true,
    "displayDetails": true,
    "displayPagination": true,
    "defaultPageSize": 10,
    "defaultSortOrder": "-createdTime"
}
```

**Columnas a mostrar:**

| Columna | Descripcion |
|---------|-------------|
| Created time | Fecha de creacion |
| Originator | Pozo que genero la alarma |
| Type | Tipo de alarma |
| Severity | Severidad |
| Status | Estado (activa, reconocida, limpiada) |

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Alarmas de Optimizacion` |
| Background color | `#FFFFFF` |

---

### 5.5 Distribucion de Salud del Campo

**Posicion:** Row 18, Col 0 | **Tamano:** sizeX: 12, sizeY: 6

Crear una visualizacion que muestre la distribucion de salud de los pozos en tres categorias: verde (>80), naranja (60-80), rojo (<60).

**Opcion A: Tres widgets Entity Count lado a lado**

Crear tres widgets pequenos, cada uno con sizeX: 4, sizeY: 6:

**Widget "Salud Alta" (Col 0):**

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Crear un alias temporal o usar el alias "Todos los Pozos" con filtro.

> Como ThingsBoard no permite facilmente contar entidades por rangos de atributos en un solo widget, se recomienda usar la **Opcion B**.

**Opcion B: Markdown Card con representacion visual**

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Datasource: `Todos los Pozos`, data key: `opt_well_health_score` (Attribute, Server).

**Contenido HTML:**

```html
<div style="padding: 16px;">
    <h3 style="color: #305680; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">Distribucion de Salud del Campo</h3>
    <div style="display: flex; gap: 12px; height: 100%;">
        <div style="flex: 1; text-align: center; padding: 16px; background: #E8F5E9; border-radius: 8px;">
            <div style="font-size: 36px; font-weight: 700; color: #4CAF50;">--</div>
            <div style="font-size: 12px; color: #4CAF50; margin-top: 4px; font-weight: 600;">BUENA (>80)</div>
            <div style="font-size: 11px; color: #9FA6B4; margin-top: 2px;">pozos</div>
        </div>
        <div style="flex: 1; text-align: center; padding: 16px; background: #FFF3E0; border-radius: 8px;">
            <div style="font-size: 36px; font-weight: 700; color: #FF9800;">--</div>
            <div style="font-size: 12px; color: #FF9800; margin-top: 4px; font-weight: 600;">MEDIA (60-80)</div>
            <div style="font-size: 11px; color: #9FA6B4; margin-top: 2px;">pozos</div>
        </div>
        <div style="flex: 1; text-align: center; padding: 16px; background: #FFEBEE; border-radius: 8px;">
            <div style="font-size: 36px; font-weight: 700; color: #F44336;">--</div>
            <div style="font-size: 12px; color: #F44336; margin-top: 4px; font-weight: 600;">BAJA (<60)</div>
            <div style="font-size: 11px; color: #9FA6B4; margin-top: 2px;">pozos</div>
        </div>
    </div>
    <div style="margin-top: 12px; font-size: 11px; color: #9FA6B4; text-align: center;">
        Los conteos se actualizaran automaticamente cuando el servicio de optimizacion este activo.
    </div>
</div>
```

> **Nota avanzada:** Cuando los datos esten disponibles, se puede convertir este widget en un Custom Widget con logica JavaScript que lea todos los valores de `opt_well_health_score`, los clasifique y renderice los conteos. La seccion de Tips de Implementacion Avanzada (seccion 8) incluye el codigo para esto.

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Background color | `#FFFFFF` |
| Padding | `0` |
| Show card header | No |

---

### 5.6 Top 5 Oportunidades de Optimizacion

**Posicion:** Row 18, Col 12 | **Tamano:** sizeX: 12, sizeY: 6

1. **"Add new widget"** > `Entities table`.
2. Configurar:

**Datasource:**
- Entity alias: `Todos los Pozos`

**Data Keys:**

| # | Data Key | Key Type | Label |
|---|----------|----------|-------|
| 1 | `entityName` | Entity field | `Pozo` |
| 2 | `lift_type` | Attribute (Server) | `Tipo` |
| 3 | `opt_potential_gain_bpd` | Attribute (Server) | `Ganancia Potencial (BPD)` |
| 4 | `opt_recommended_action` | Attribute (Server) | `Accion` |
| 5 | `opt_well_health_score` | Attribute (Server) | `Salud` |

**Configuracion:**

| Opcion | Valor |
|--------|-------|
| Title | `Top 5 Oportunidades de Optimizacion` |
| Default sort order | `opt_potential_gain_bpd` (descendente) |
| Default page size | 5 |
| Display pagination | No |
| Enable search | No |

Reutilizar las mismas **Cell style functions** y **Cell content functions** definidas en la seccion 5.3 para las columnas de Salud y Accion.

**Accion de click en fila:**

| Campo | Valor |
|-------|-------|
| Action source | `Row click` |
| Action type | `Navigate to new dashboard state` |
| Target state | `opt_detalle` |
| Set entity from widget | Si |

---

### Resumen Visual del Estado Principal

```
  Col 0         Col 4         Col 8         Col 12        Col 16        Col 20      Col 24
   |              |             |              |             |             |            |
   v              v             v              v             v             v            v

   ╔══════════════════════════════════════════════════════════════════════════════════════╗
   ║  Centro de Optimizacion                                        ┌────────────────┐  ║
   ║  Analisis y recomendaciones del servicio de optimizacion       │ Servicio Activo │  ║ Row 0-2
   ║                                                                └────────────────┘  ║ sizeX:24
   ╚══════════════════════════════════════════════════════════════════════════════════════╝ sizeY:2
   Widget: markdown_card | Alias: Usuario Actual (estatico) | Sin header                  Tipo: Markdown/HTML Value Card

   ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
   │  trending_up │   favorite   │    speed     │   warning    │     bolt     │report_problem│
   │              │              │              │              │              │              │
   │  Produccion  │    Salud     │  Eficiencia  │  Pozos con   │   Energia    │  Dias para   │ Row 3-6
   │  Potencial   │  Promedio    │  Promedio    │  Anomalias   │  Promedio    │    Falla     │ sizeX:4
   │  Adicional   │  del Campo   │              │              │              │              │ sizeY:3
   │              │              │              │              │              │ (Mas critico)│
   │   +1,247     │    72.3      │    68.5      │      5       │    8.52      │     45       │
   │     BPD      │    /100      │      %       │              │   kWh/bbl    │    dias      │
   │   ▲ verde    │  ● naranja   │  ● naranja   │  ● rojo      │  ● naranja   │  ● verde     │
   │   (SUM)      │   (AVG)      │   (AVG)      │(entity_count)│   (AVG)      │   (MIN)      │
   ├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
   │ Col 0        │ Col 4        │ Col 8        │ Col 12       │ Col 16       │ Col 20       │
   └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
   Widget: aggregated_value_card (x5) + entity_count (x1)
   Alias: "Todos los Pozos" (KPIs 1,2,3,5,6) | "Pozos con Alarma" (KPI 4)
   Color functions: Salud >=80 verde, >=60 naranja, <60 rojo
                    Efic. >=75 verde, >=55 naranja, <55 rojo
                    Dias  <=0 gris, <30 rojo, <90 naranja, >=90 verde

   ┌──────────────────────────────────────────────────────────────────┬────────────────────────┐
   │  Recomendaciones de Optimizacion                        [Buscar]│ Alarmas de Optimizacion │
   │                                                                 │                         │
   │  Pozo             │ Tipo │ Estado │ Salud│ Accion Recomendada  ││ Fecha   │ Pozo  │ Tipo  │
   │  ─────────────────┼──────┼────────┼──────┼─────────────────────││─────────┼───────┼───────│ Row 7-17
   │  CA-MAC-BOS-01-005│ ESP  │subopti.│  68  │ ▲ Aumentar frecuenc.││ 09:15   │ BOS-05│ PUMP_ │ sizeX:16 (izq)
   │  CA-MAC-BOS-01-003│ SRP  │pending │  55  │ ▲ Aumentar SPM      ││ 08:42   │ BOS-03│ WELL_ │ sizeX:8  (der)
   │  CA-MAC-CNE-02-001│ ESP  │subopti.│  42  │ ▼ Reducir frecuenc. ││ 07:30   │ CNE-01│ ACCEL │ sizeY:10
   │  CA-MAC-ANA-03-002│ GL   │optimiz.│  85  │ ✔ Sin accion neces. ││ 06:55   │ ANA-04│ ANOMA │
   │  CA-MAC-BOS-01-001│ PCP  │pending │  63  │ ▲ Aumentar RPM      ││ 06:12   │ BOS-01│ ESP_F │
   │  ...              │ ...  │ ...    │  ... │ ...                 ││ ...     │ ...   │ ...   │
   │  Pagina 1 de 5    │ 15 por pagina │ Ord: Ganancia (BPD) desc  ││ Pag 1/3 │ Sev.  │ Ack   │
   │                   │               │                           ││         │       │ Clear │
   │  → Click en fila navega a estado "opt_detalle" ───────────────>││         │       │       │
   ├──────────────────────────────────────────────────────────────────┼────────────────────────┤
   │ Col 0                                                   Col 16 │ Col 16          Col 24  │
   └──────────────────────────────────────────────────────────────────┴────────────────────────┘
   Widget izq: entities_table (system.cards.entities_table)
     Alias: "Todos los Pozos"
     Columnas: entityName, lift_type, opt_status, opt_well_health_score,
               opt_recommended_action, opt_potential_gain_bpd, opt_efficiency_pct, opt_anomaly_score
     Cell style functions: Salud (color por rango), Estado (badge por valor), Anomalia (color por rango)
     Cell content function: Accion (iconos + texto por tipo de accion)
     Row style: borde rojo izquierdo si anomaly_score > 0.8
     Accion: Row click -> Navigate to "opt_detalle" (Set entity from widget: Si)

   Widget der: alarms_table (system.alarm_widgets.alarms_table)
     Alias: "Todos los Pozos"
     Filtros: WELL_SUBOPTIMAL, PUMP_DEGRADATION, ACCELERATED_DECLINE,
              ESP_FAILURE_PREDICTED, ANOMALY_DETECTED, CASING_HEADING, LIFT_METHOD_REVIEW
     Status: ACTIVE_UNACK, ACTIVE_ACK | Todas las severidades
     Columnas: Created time, Originator, Type, Severity, Status

   ┌───────────────────────────────────────────────┬──────────────────────────────────────────┐
   │  Distribucion de Salud del Campo              │  Top 5 Oportunidades de Optimizacion     │
   │                                               │                                          │
   │  ┌─────────────┐ ┌─────────────┐ ┌──────────┐│  Pozo             │ Tipo│ Ganancia│ Salud │ Row 18-24
   │  │     22       │ │     18      │ │    8     ││  ─────────────────┼─────┼─────────┼───────│ sizeX:12 (izq)
   │  │   BUENA      │ │   MEDIA     │ │   BAJA   ││  CA-MAC-BOS-01-005│ ESP │ +200 BPD│  68   │ sizeX:12 (der)
   │  │   (>80)      │ │  (60-80)    │ │  (<60)   ││  CA-MAC-CNE-02-003│ SRP │ +185 BPD│  55   │ sizeY:6
   │  │  ■ verde     │ │  ■ naranja  │ │ ■ rojo   ││  CA-MAC-ANA-03-001│ GL  │ +150 BPD│  63   │
   │  │   pozos      │ │   pozos     │ │  pozos   ││  CA-MAC-BOS-01-002│ ESP │ +120 BPD│  71   │
   │  └─────────────┘ └─────────────┘ └──────────┘│  CA-MAC-CNE-02-001│ PCP │ +95 BPD │  42   │
   │  Los conteos se actualizan automaticamente    │  Ord: Ganancia desc │ Sin paginacion     │
   │                                               │  → Click en fila -> "opt_detalle"        │
   ├───────────────────────────────────────────────┼──────────────────────────────────────────┤
   │ Col 0                                  Col 12 │ Col 12                            Col 24 │
   └───────────────────────────────────────────────┴──────────────────────────────────────────┘
   Widget izq: markdown_card (Markdown/HTML Value Card)
     Alias: "Todos los Pozos" | Key: opt_well_health_score
     Tres bloques coloreados con conteo por rango de salud
     Sin header | Padding: 0

   Widget der: entities_table
     Alias: "Todos los Pozos"
     Columnas: entityName, lift_type, opt_potential_gain_bpd, opt_recommended_action, opt_well_health_score
     Sort: opt_potential_gain_bpd descendente | Page size: 5 | Sin paginacion | Sin busqueda
     Accion: Row click -> Navigate to "opt_detalle" (Set entity from widget: Si)
```

**Nota sobre el grid:** ThingsBoard usa un grid de 24 columnas. Cada widget tiene posicion
`(col, row)` y tamano `(sizeX, sizeY)`. Las filas no tienen tamano fijo; `sizeY` determina
la altura relativa del widget.

---

## 6. PASO 4: Estado de Detalle de Optimizacion (opt_detalle)

### 6.1 Crear el Estado

1. En modo edicion, click en el icono de **"States"** (esquina superior, icono de capas/paginas).
2. Click en **"+"** para agregar un nuevo estado.
3. Configurar:

| Campo | Valor |
|-------|-------|
| State name | `opt_detalle` |
| State ID | `opt_detalle` |
| Root state | No |

4. Click en **"Add"**.
5. Seleccionar el estado `opt_detalle` para editarlo.

---

### 6.2 Header con Boton Volver

**Posicion:** Row 0, Col 0 | **Tamano:** sizeX: 24, sizeY: 2.5

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `entityName` (Entity field)
  - `lift_type` (Attribute, Server)
  - `opt_well_health_score` (Attribute, Server)

**Contenido HTML:**

```html
<div style="display: flex; align-items: center; gap: 16px; padding: 8px 16px;">
    <div id="btn-back" style="cursor: pointer; padding: 6px 16px; background: #305680; color: white; border-radius: 6px; font-weight: 500; font-size: 13px; white-space: nowrap;">
        &#8592; Volver
    </div>
    <div style="flex: 1;">
        <span style="font-size: 22px; font-weight: 700; color: #305680;">${entityName}</span>
        <span class="opt-badge" style="margin-left: 8px; background: #E3F2FD; color: #2196F3;">${lift_type}</span>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; letter-spacing: 0.5px;">Score de Salud</div>
        <div style="font-size: 32px; font-weight: 700; color: #305680;">${opt_well_health_score:0}</div>
    </div>
</div>
```

**Accion del boton "Volver":**

1. En la configuracion del widget, ir a **"Actions"**.
2. Agregar accion:

| Campo | Valor |
|-------|-------|
| Action source | `Widget header button` o `Element click` (#btn-back) |
| Name | `Volver al resumen` |
| Action type | `Navigate to default state` |

> **Nota:** En algunas versiones de ThingsBoard, para manejar click en un elemento HTML especifico, se debe usar `On HTML element click` con el selector CSS `#btn-back`. Si esta opcion no esta disponible, se puede usar un boton de la barra del widget o un widget separado para la navegacion.

---

### 6.3 KPIs de Optimizacion del Pozo (6 tarjetas)

Crear 6 tarjetas de KPI en la fila 3. Cada una ocupa **sizeX: 4, sizeY: 3**.

#### KPI 1: Produccion Actual

**Posicion:** Row 3, Col 0

1. **"Add new widget"** > `Value card` o `Simple card` del bundle `Cards`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data key: `opt_current_rate_bpd` (Attribute, Server)

**Apariencia:**

| Opcion | Valor |
|--------|-------|
| Title | `Produccion Actual` |
| Units | `BPD` |
| Decimals | `0` |
| Icon | `show_chart` |
| Icon color | `#305680` |

---

#### KPI 2: Produccion Recomendada

**Posicion:** Row 3, Col 4

**Datasource:**
- Data key: `opt_recommended_rate_bpd` (Attribute, Server)

| Opcion | Valor |
|--------|-------|
| Title | `Produccion Recomendada` |
| Units | `BPD` |
| Decimals | `0` |
| Icon | `trending_up` |
| Icon color | `#4CAF50` |

---

#### KPI 3: Ganancia Potencial

**Posicion:** Row 3, Col 8

**Datasource:**
- Data key: `opt_potential_gain_bpd` (Attribute, Server)

| Opcion | Valor |
|--------|-------|
| Title | `Ganancia Potencial` |
| Units | `BPD` |
| Decimals | `0` |
| Icon | `add_circle` |
| Icon color | `#4CAF50` |
| Value color | `#4CAF50` |

---

#### KPI 4: Eficiencia

**Posicion:** Row 3, Col 12

**Datasource:**
- Data key: `opt_efficiency_pct` (Attribute, Server)

| Opcion | Valor |
|--------|-------|
| Title | `Eficiencia del Sistema` |
| Units | `%` |
| Decimals | `1` |
| Icon | `speed` |

**Color Function:**

```javascript
var eff = value;
if (eff >= 75) return '#4CAF50';
if (eff >= 55) return '#FF9800';
return '#F44336';
```

---

#### KPI 5: Energia por Barril

**Posicion:** Row 3, Col 16

**Datasource:**
- Data key: `opt_energy_kwh_bbl` (Attribute, Server)

| Opcion | Valor |
|--------|-------|
| Title | `Energia por Barril` |
| Units | `kWh/bbl` |
| Decimals | `2` |
| Icon | `bolt` |
| Icon color | `#FF9800` |

---

#### KPI 6: Probabilidad de Falla

**Posicion:** Row 3, Col 20

**Datasource:**
- Data key: `opt_failure_probability` (Attribute, Server)

| Opcion | Valor |
|--------|-------|
| Title | `Probabilidad de Falla` |
| Units | (ninguna, se muestra como decimal 0-1) |
| Decimals | `2` |
| Icon | `report_problem` |

**Color Function:**

```javascript
var prob = value;
if (prob >= 0.7) return '#F44336';
if (prob >= 0.3) return '#FF9800';
return '#4CAF50';
```

> **Nota:** Para mostrar como porcentaje en vez de decimal, usar una funcion de valor:
> ```javascript
> return (value * 100).toFixed(1) + '%';
> ```

---

### 6.4 Tarjeta de Accion Recomendada

**Posicion:** Row 7, Col 0 | **Tamano:** sizeX: 24, sizeY: 3

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `opt_recommended_action` (Attribute, Server)
  - `opt_recommended_action_detail` (Attribute, Server)
  - `opt_decline_rate_monthly_pct` (Attribute, Server)
  - `opt_days_to_predicted_failure` (Attribute, Server)

**Contenido HTML:**

```html
<div style="display: flex; gap: 16px; padding: 8px 16px;">
    <div style="flex: 1; padding: 16px; background: #E3F2FD; border-radius: 8px; border-left: 4px solid #2196F3;">
        <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Accion Recomendada</div>
        <div style="font-size: 16px; font-weight: 600; color: #305680;">${opt_recommended_action:Sin datos}</div>
        <div style="font-size: 13px; color: #4B535B; margin-top: 4px;">${opt_recommended_action_detail:El servicio de optimizacion aun no ha analizado este pozo.}</div>
    </div>
    <div style="padding: 16px; background: #FFF3E0; border-radius: 8px; border-left: 4px solid #FF9800; min-width: 200px;">
        <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Declive Mensual</div>
        <div style="font-size: 24px; font-weight: 700; color: #FF9800;">${opt_decline_rate_monthly_pct:0}%</div>
    </div>
    <div style="padding: 16px; background: #FFEBEE; border-radius: 8px; border-left: 4px solid #F44336; min-width: 200px;">
        <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Dias para Falla</div>
        <div style="font-size: 24px; font-weight: 700; color: #F44336;">${opt_days_to_predicted_failure:--}</div>
    </div>
</div>
```

> **Nota sobre placeholders:** La sintaxis `${atributo:valor_default}` muestra el valor por defecto si el atributo esta vacio. En algunas versiones de ThingsBoard, la sintaxis puede variar. Si no funciona con `:`, usar condicionales en la funcion de contenido del widget.

---

### 6.5 Grafico de Produccion vs Recomendado

**Posicion:** Row 11, Col 0 | **Tamano:** sizeX: 12, sizeY: 8

1. **"Add new widget"** > Buscar `Time series chart` en el bundle `Charts`.
   - Widget: **`system.time_series_chart`** o equivalente.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data key 1: `flow_rate_bpd` (tipo: **Timeseries**)
  - Label: `Produccion Real`
  - Color: `#305680`
  - Line type: Solid
  - Line width: 2

**Configuracion del grafico:**

| Opcion | Valor |
|--------|-------|
| Title | `Produccion vs Recomendado` |
| Y-axis label | `BPD` |
| Show legend | Si |
| Timewindow | Ultimos 7 dias (o configurable) |

**Linea de referencia para tasa recomendada:**

> Actualmente `opt_recommended_rate_bpd` es un atributo estatico (no timeseries). Para mostrarlo como una linea horizontal de referencia:

1. En la configuracion avanzada del grafico (si soporta "thresholds" o "reference lines"):
   - Agregar threshold:
     - **Source:** Entity alias: `Pozo Seleccionado`
     - **Key:** `opt_recommended_rate_bpd` (Attribute, Server)
     - **Color:** `#4CAF50`
     - **Line style:** Dashed
     - **Label:** `Tasa Recomendada`

2. Si el widget no soporta thresholds basados en atributos, agregar una nota debajo del grafico:
   - Usar un widget `Markdown/HTML Value Card` pequeno debajo con el texto:
   ```html
   <div style="padding: 4px 16px; font-size: 12px; color: #9FA6B4;">
       Tasa recomendada: <b style="color: #4CAF50;">${opt_recommended_rate_bpd} BPD</b>
       &nbsp;|&nbsp;
       Tasa actual calculada: <b style="color: #305680;">${opt_current_rate_bpd} BPD</b>
   </div>
   ```

> **Evolucion futura:** Cuando el servicio de optimizacion comience a generar `opt_recommended_rate_bpd` como timeseries (ademas de atributo), se podra agregar como segunda serie en el grafico para ver la evolucion de la recomendacion en el tiempo.

---

### 6.6 Placeholder de Curvas Nodales (IPR/VLP)

**Posicion:** Row 11, Col 12 | **Tamano:** sizeX: 12, sizeY: 8

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `opt_nodal_ipr_curve` (Attribute, Server)
  - `opt_nodal_vlp_curve` (Attribute, Server)

**Contenido HTML:**

```html
<div style="padding: 16px; text-align: center;">
    <h3 style="color: #305680; margin: 0 0 8px 0; font-weight: 600;">Analisis Nodal (IPR/VLP)</h3>
    <div style="padding: 40px; background: #F5F7FA; border-radius: 8px; color: #9FA6B4;">
        <div style="font-size: 48px; margin-bottom: 8px;">&#128202;</div>
        <div style="font-size: 14px; font-weight: 500;">Los datos de curvas nodales estaran disponibles cuando el servicio de optimizacion este activo.</div>
        <div style="margin-top: 12px; font-size: 12px; color: #B0B7C3;">
            Atributos: <code>opt_nodal_ipr_curve</code>, <code>opt_nodal_vlp_curve</code>
        </div>
        <div style="margin-top: 8px; font-size: 11px; color: #B0B7C3;">
            Formato: JSON array [[caudal_bpd, presion_psi], ...]
        </div>
    </div>
</div>
```

> **Cuando los datos esten disponibles:** Este widget se puede reemplazar por un Custom Widget que parsee el JSON de `opt_nodal_ipr_curve` y `opt_nodal_vlp_curve` y renderice un grafico IPR/VLP usando ECharts. Ver seccion 8 (Tips de Implementacion Avanzada) para el codigo.

---

### 6.7 Placeholder de Pronostico DCA

**Posicion:** Row 20, Col 0 | **Tamano:** sizeX: 12, sizeY: 6

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `opt_dca_forecast` (Attribute, Server)
  - `opt_decline_rate_monthly_pct` (Attribute, Server)
  - `opt_eur_mstb` (Attribute, Server)

**Contenido HTML:**

```html
<div style="padding: 16px;">
    <h3 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Pronostico de Declinacion (DCA)</h3>
    <div style="display: flex; gap: 12px; margin-bottom: 12px;">
        <div style="flex: 1; padding: 12px; background: #F5F7FA; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">Declive Mensual</div>
            <div style="font-size: 20px; font-weight: 700; color: #FF9800;">${opt_decline_rate_monthly_pct:0}%</div>
        </div>
        <div style="flex: 1; padding: 12px; background: #F5F7FA; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">EUR Estimado</div>
            <div style="font-size: 20px; font-weight: 700; color: #305680;">${opt_eur_mstb:0} MSTB</div>
        </div>
    </div>
    <div style="padding: 30px; background: #F5F7FA; border-radius: 8px; color: #9FA6B4; text-align: center;">
        <div style="font-size: 40px; margin-bottom: 8px;">&#128200;</div>
        <div style="font-size: 13px;">El grafico de pronostico DCA estara disponible cuando el servicio de optimizacion genere datos en <code>opt_dca_forecast</code>.</div>
    </div>
</div>
```

---

### 6.8 Informacion de Pozos Similares y Cluster

**Posicion:** Row 20, Col 12 | **Tamano:** sizeX: 12, sizeY: 6

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. Configurar:

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `opt_cluster_id` (Attribute, Server)
  - `opt_similar_wells` (Attribute, Server)
  - `opt_anomaly_score` (Attribute, Server)
  - `opt_anomaly_type` (Attribute, Server)
  - `opt_eur_mstb` (Attribute, Server)

**Contenido HTML:**

```html
<div style="padding: 16px;">
    <h3 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Pozos Similares (Cluster)</h3>
    <div style="font-size: 13px; color: #4B535B; margin-bottom: 12px;">
        <span style="color: #9FA6B4;">Cluster ID:</span> <b>${opt_cluster_id:--}</b>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style="color: #9FA6B4;">Score de Anomalia:</span> <b>${opt_anomaly_score:0}</b>
    </div>
    <div style="font-size: 13px; color: #4B535B; margin-bottom: 12px;">
        <span style="color: #9FA6B4;">Tipo de Anomalia:</span> <b>${opt_anomaly_type:Ninguna detectada}</b>
    </div>
    <div style="padding: 12px; background: #F5F7FA; border-radius: 8px; margin-bottom: 12px;">
        <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; margin-bottom: 4px;">Pozos Similares</div>
        <div style="font-size: 14px; font-weight: 500; color: #305680;">${opt_similar_wells:Sin datos de clustering disponibles}</div>
        <div style="font-size: 11px; color: #B0B7C3; margin-top: 4px;">Formato: JSON array con nombres de pozos en el mismo cluster.</div>
    </div>
    <div style="padding: 12px; background: #E3F2FD; border-radius: 8px;">
        <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; margin-bottom: 4px;">EUR Estimado</div>
        <div style="font-size: 24px; font-weight: 700; color: #305680;">${opt_eur_mstb:0} <span style="font-size: 14px; font-weight: 400;">MSTB</span></div>
    </div>
</div>
```

---

### 6.9 Parametros de Optimizacion Especificos por Tipo de Levantamiento

**Posicion:** Row 27, Col 0 | **Tamano:** sizeX: 24, sizeY: 4

Esta seccion muestra recomendaciones especificas segun el tipo de levantamiento del pozo. Se usan **condiciones de visibilidad** para mostrar solo los widgets relevantes.

> **Concepto clave:** En ThingsBoard, se puede configurar la visibilidad de un widget basada en el valor de un atributo. Asi, si el pozo es ESP, solo se muestra la tarjeta de ESP; si es SRP, solo la de SRP.

#### Widget ESP (solo visible si lift_type == "ESP")

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. **Posicion:** Row 27, Col 0 | **sizeX:** 24, **sizeY:** 4.

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `opt_recommended_frequency_hz` (Attribute, Server)
  - `opt_current_operating_point_bpd` (Attribute, Server)
  - `frequency_hz` (Timeseries, ultimo valor)
  - `lift_type` (Attribute, Server)

**Contenido HTML:**

```html
<div style="padding: 12px 16px;">
    <h3 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Optimizacion ESP</h3>
    <div style="display: flex; gap: 16px;">
        <div style="flex: 1; padding: 16px; background: #F5F7FA; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">Frecuencia Actual</div>
            <div style="font-size: 28px; font-weight: 700; color: #305680;">${frequency_hz:--} <span style="font-size: 14px; font-weight: 400;">Hz</span></div>
        </div>
        <div style="flex: 0 0 60px; display: flex; align-items: center; justify-content: center;">
            <div style="font-size: 24px; color: #4CAF50;">&#10140;</div>
        </div>
        <div style="flex: 1; padding: 16px; background: #E8F5E9; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #4CAF50; text-transform: uppercase;">Frecuencia Recomendada</div>
            <div style="font-size: 28px; font-weight: 700; color: #4CAF50;">${opt_recommended_frequency_hz:--} <span style="font-size: 14px; font-weight: 400;">Hz</span></div>
        </div>
        <div style="flex: 1; padding: 16px; background: #F5F7FA; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">Punto Operacion Actual</div>
            <div style="font-size: 28px; font-weight: 700; color: #305680;">${opt_current_operating_point_bpd:--} <span style="font-size: 14px; font-weight: 400;">BPD</span></div>
        </div>
    </div>
</div>
```

**Condicion de visibilidad:**

1. En la configuracion del widget, buscar la seccion **"Visibility"** o **"Widget visibility"**.
2. Activar **"Enable visibility condition"**.
3. Configurar:
   - **Entity alias:** `Pozo Seleccionado`
   - **Key:** `lift_type`
   - **Key type:** Attribute (Server)
   - **Condition:** `Equal`
   - **Value:** `ESP`

> **Nota:** En algunas versiones de ThingsBoard, la condicion de visibilidad esta en "Advanced" > "Widget visibility condition". Si el campo `lift_type` usa mayusculas ("ESP"), asegurarse de poner exactamente el mismo valor.

---

#### Widget SRP (solo visible si lift_type == "SRP")

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. **Posicion:** Row 27, Col 0 | **sizeX:** 24, **sizeY:** 4.

**Datasource:**
- Data keys: `opt_recommended_spm`, `spm`, `lift_type`

**Contenido HTML:**

```html
<div style="padding: 12px 16px;">
    <h3 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Optimizacion SRP (Bombeo Mecanico)</h3>
    <div style="display: flex; gap: 16px;">
        <div style="flex: 1; padding: 16px; background: #F5F7FA; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">SPM Actual</div>
            <div style="font-size: 28px; font-weight: 700; color: #305680;">${spm:--} <span style="font-size: 14px; font-weight: 400;">SPM</span></div>
        </div>
        <div style="flex: 0 0 60px; display: flex; align-items: center; justify-content: center;">
            <div style="font-size: 24px; color: #4CAF50;">&#10140;</div>
        </div>
        <div style="flex: 1; padding: 16px; background: #E8F5E9; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #4CAF50; text-transform: uppercase;">SPM Recomendado</div>
            <div style="font-size: 28px; font-weight: 700; color: #4CAF50;">${opt_recommended_spm:--} <span style="font-size: 14px; font-weight: 400;">SPM</span></div>
        </div>
    </div>
</div>
```

**Condicion de visibilidad:** `lift_type` == `SRP`

---

#### Widget Gas Lift (solo visible si lift_type == "gas_lift")

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. **Posicion:** Row 27, Col 0 | **sizeX:** 24, **sizeY:** 4.

**Datasource:**
- Data keys: `opt_recommended_injection_rate_mcfd`, `lift_type`

**Contenido HTML:**

```html
<div style="padding: 12px 16px;">
    <h3 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Optimizacion Gas Lift</h3>
    <div style="display: flex; gap: 16px;">
        <div style="flex: 1; padding: 16px; background: #E8F5E9; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #4CAF50; text-transform: uppercase;">Tasa de Inyeccion Recomendada</div>
            <div style="font-size: 28px; font-weight: 700; color: #4CAF50;">${opt_recommended_injection_rate_mcfd:--} <span style="font-size: 14px; font-weight: 400;">MCFD</span></div>
        </div>
        <div style="flex: 1; padding: 16px; background: #F5F7FA; border-radius: 8px;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase; margin-bottom: 4px;">Nota</div>
            <div style="font-size: 13px; color: #4B535B;">La curva GLPC estara disponible en el atributo <code>opt_glpc_curve</code> cuando el servicio de optimizacion este activo. Permitira visualizar la relacion entre tasa de inyeccion de gas y produccion de liquido.</div>
        </div>
    </div>
</div>
```

**Condicion de visibilidad:** `lift_type` == `gas_lift`

---

#### Widget PCP (solo visible si lift_type == "PCP")

1. **"Add new widget"** > `Markdown/HTML Value Card`.
2. **Posicion:** Row 27, Col 0 | **sizeX:** 24, **sizeY:** 4.

**Datasource:**
- Data keys: `opt_recommended_speed_rpm`, `speed_rpm`, `lift_type`

**Contenido HTML:**

```html
<div style="padding: 12px 16px;">
    <h3 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Optimizacion PCP (Cavidad Progresiva)</h3>
    <div style="display: flex; gap: 16px;">
        <div style="flex: 1; padding: 16px; background: #F5F7FA; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">RPM Actual</div>
            <div style="font-size: 28px; font-weight: 700; color: #305680;">${speed_rpm:--} <span style="font-size: 14px; font-weight: 400;">RPM</span></div>
        </div>
        <div style="flex: 0 0 60px; display: flex; align-items: center; justify-content: center;">
            <div style="font-size: 24px; color: #4CAF50;">&#10140;</div>
        </div>
        <div style="flex: 1; padding: 16px; background: #E8F5E9; border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #4CAF50; text-transform: uppercase;">RPM Recomendada</div>
            <div style="font-size: 28px; font-weight: 700; color: #4CAF50;">${opt_recommended_speed_rpm:--} <span style="font-size: 14px; font-weight: 400;">RPM</span></div>
        </div>
    </div>
</div>
```

**Condicion de visibilidad:** `lift_type` == `PCP`

---

### Resumen Visual del Estado de Detalle

```
  Col 0         Col 4         Col 8         Col 12        Col 16        Col 20      Col 24
   |              |             |              |             |             |            |
   v              v             v              v             v             v            v

   ╔══════════════════════════════════════════════════════════════════════════════════════╗
   ║ ┌──────────┐                                                    Score de Salud     ║
   ║ │<- Volver │  CA-MAC-BOS-01-005  ┌─────┐                            68             ║ Row 0-2.5
   ║ └──────────┘                     │ ESP │                        (32px, bold)        ║ sizeX:24
   ║  #btn-back                       └─────┘                                           ║ sizeY:2.5
   ╚══════════════════════════════════════════════════════════════════════════════════════╝
   Widget: markdown_card | Alias: "Pozo Seleccionado"
   Keys: entityName, lift_type, opt_well_health_score
   Accion: #btn-back click -> Navigate to default state (volver al resumen)

   ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
   │  show_chart  │ trending_up  │  add_circle  │    speed     │     bolt     │report_problem│
   │              │              │              │              │              │              │
   │  Produccion  │  Produccion  │   Ganancia   │  Eficiencia  │  Energia por │ Probabilidad │ Row 3-6
   │   Actual     │ Recomendada  │  Potencial   │ del Sistema  │    Barril    │  de Falla    │ sizeX:4
   │              │              │              │              │              │              │ sizeY:3
   │     850      │    1,050     │    +200      │    72.0      │    8.52      │    0.12      │
   │     BPD      │     BPD      │     BPD      │      %       │   kWh/bbl    │  (prob 0-1)  │
   │  ● azul      │  ● verde     │  ● verde     │  ● naranja   │  ● naranja   │  ● verde     │
   ├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
   │ Col 0        │ Col 4        │ Col 8        │ Col 12       │ Col 16       │ Col 20       │
   └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
   Widget: value_card (x6) | Alias: "Pozo Seleccionado"
   Keys: opt_current_rate_bpd, opt_recommended_rate_bpd, opt_potential_gain_bpd,
         opt_efficiency_pct, opt_energy_kwh_bbl, opt_failure_probability
   Color functions: Eficiencia >=75 verde, >=55 naranja, <55 rojo
                    Prob. Falla >=0.7 rojo, >=0.3 naranja, <0.3 verde

   ╔══════════════════════════════════════════════════════════════════════════════════════╗
   ║  ┌─────────────────────────────────────────────────────┐ ┌──────────┐ ┌──────────┐ ║
   ║  │ ACCION RECOMENDADA                                  │ │ DECLIVE  │ │ DIAS PARA│ ║
   ║  │ ▌increase_frequency                                 │ │ MENSUAL  │ │   FALLA  │ ║ Row 7-10
   ║  │ ▌Incrementar frecuencia VSD de 58 Hz a 65 Hz para  │ │          │ │          │ ║ sizeX:24
   ║  │ ▌aumentar caudal manteniendo eficiencia optima.     │ │  2.1%    │ │   120    │ ║ sizeY:3
   ║  │ ▌(borde izquierdo azul, fondo #E3F2FD)             │ │ (naranja)│ │  (rojo)  │ ║
   ║  └─────────────────────────────────────────────────────┘ └──────────┘ └──────────┘ ║
   ╚══════════════════════════════════════════════════════════════════════════════════════╝
   Widget: markdown_card | Alias: "Pozo Seleccionado"
   Keys: opt_recommended_action, opt_recommended_action_detail,
         opt_decline_rate_monthly_pct, opt_days_to_predicted_failure
   Layout: flex row - accion (flex:1), declive (min-width:200), dias falla (min-width:200)

   ┌───────────────────────────────────────────────┬──────────────────────────────────────────┐
   │  Produccion vs Recomendado                    │  Analisis Nodal (IPR/VLP)                │
   │                                               │                                          │
   │  BPD                                          │        ┌─────────────────────────────┐   │
   │  1200 ┤                                       │        │                             │   │
   │  1100 ┤          - - - - - - - - -            │        │   Los datos de curvas       │   │ Row 11-19
   │  1050 ┤ ·····Tasa Recomendada (verde, dashed) │        │   nodales estaran           │   │ sizeX:12 (izq)
   │  1000 ┤     ╱╲                                │        │   disponibles cuando el     │   │ sizeX:12 (der)
   │   900 ┤───╱──╲──╱──╲                          │        │   servicio de optimizacion  │   │ sizeY:8
   │   850 ┤──╱────╲╱────╲── Produccion Real       │        │   este activo.              │   │
   │   800 ┤─╱──────────────── (#305680, solida)   │        │                             │   │
   │   700 ┤                                       │        │   Atributos:                │   │
   │       └──┬──┬──┬──┬──┬──┬──┬─── dias          │        │   opt_nodal_ipr_curve       │   │
   │       Lun Ma Mi Ju Vi Sa Do                   │        │   opt_nodal_vlp_curve       │   │
   │  Timewindow: Ultimos 7 dias                   │        │   Formato: JSON array       │   │
   │  Leyenda: ── Real  - - Recomendada            │        └─────────────────────────────┘   │
   ├───────────────────────────────────────────────┼──────────────────────────────────────────┤
   │ Col 0                                  Col 12 │ Col 12                            Col 24 │
   └───────────────────────────────────────────────┴──────────────────────────────────────────┘
   Widget izq: time_series_chart (system.time_series_chart)
     Alias: "Pozo Seleccionado"
     Serie 1: flow_rate_bpd (Timeseries) - color #305680, solida, width 2
     Threshold: opt_recommended_rate_bpd (Attribute) - color #4CAF50, dashed
     Title: "Produccion vs Recomendado" | Y-axis: BPD | Show legend: Si

   Widget der: markdown_card (Placeholder)
     Alias: "Pozo Seleccionado"
     Keys: opt_nodal_ipr_curve, opt_nodal_vlp_curve
     Contenido: Placeholder con icono e instrucciones
     Futuro: Custom Widget con ECharts para grafico IPR/VLP

   ┌───────────────────────────────────────────────┬──────────────────────────────────────────┐
   │  Pronostico de Declinacion (DCA)              │  Pozos Similares (Cluster)               │
   │                                               │                                          │
   │  ┌─────────────────┐  ┌─────────────────┐    │  Cluster ID: 3  |  Anomalia: 0.15        │
   │  │ DECLIVE MENSUAL │  │  EUR ESTIMADO   │    │  Tipo Anomalia: Ninguna detectada         │ Row 20-26
   │  │     2.1%        │  │   450 MSTB      │    │                                          │ sizeX:12 (izq)
   │  │   (naranja)     │  │   (azul)        │    │  ┌────────────────────────────────────┐  │ sizeX:12 (der)
   │  └─────────────────┘  └─────────────────┘    │  │ POZOS SIMILARES                    │  │ sizeY:6
   │                                               │  │ Sin datos de clustering disponibles│  │
   │  ┌─────────────────────────────────────────┐  │  └────────────────────────────────────┘  │
   │  │  El grafico de pronostico DCA estara    │  │                                          │
   │  │  disponible cuando el servicio genere   │  │  ┌────────────────────────────────────┐  │
   │  │  datos en opt_dca_forecast.             │  │  │ EUR ESTIMADO                       │  │
   │  │  Formato: JSON array                    │  │  │         450 MSTB                   │  │
   │  └─────────────────────────────────────────┘  │  └────────────────────────────────────┘  │
   ├───────────────────────────────────────────────┼──────────────────────────────────────────┤
   │ Col 0                                  Col 12 │ Col 12                            Col 24 │
   └───────────────────────────────────────────────┴──────────────────────────────────────────┘
   Widget izq: markdown_card (Placeholder DCA)
     Alias: "Pozo Seleccionado"
     Keys: opt_dca_forecast, opt_decline_rate_monthly_pct, opt_eur_mstb
     KPI boxes arriba + placeholder de grafico abajo
     Futuro: Custom Widget con ECharts para curva DCA

   Widget der: markdown_card (Cluster info)
     Alias: "Pozo Seleccionado"
     Keys: opt_cluster_id, opt_similar_wells, opt_anomaly_score, opt_anomaly_type, opt_eur_mstb
     Info de cluster, anomalia y pozos similares (JSON array)

   ╔══════════════════════════════════════════════════════════════════════════════════════╗
   ║                                                                                    ║
   ║  *** SOLO UNO DE ESTOS 4 WIDGETS ES VISIBLE A LA VEZ ***                          ║
   ║  *** Controlado por condicion de visibilidad: lift_type == "XXX" ***               ║ Row 27-31
   ║                                                                                    ║ sizeX:24
   ║ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ ║ sizeY:4
   ║  SI lift_type == "ESP":                                                            ║
   ║  ┌────────────────────────────────────────────────────────────────────────────────┐ ║
   ║  │  Optimizacion ESP                                                              │ ║
   ║  │                                                                                │ ║
   ║  │  ┌──────────────────┐         ┌──────────────────┐   ┌──────────────────┐      │ ║
   ║  │  │ Frecuencia Actual│  ────>  │ Frec. Recomendada│   │ Punto Operacion  │      │ ║
   ║  │  │      58 Hz       │ (verde) │      65 Hz       │   │    850 BPD       │      │ ║
   ║  │  │  (fondo gris)    │         │  (fondo verde)   │   │  (fondo gris)    │      │ ║
   ║  │  └──────────────────┘         └──────────────────┘   └──────────────────┘      │ ║
   ║  └────────────────────────────────────────────────────────────────────────────────┘ ║
   ║  Visibility: lift_type == "ESP"                                                    ║
   ║  Keys: frequency_hz (TS), opt_recommended_frequency_hz, opt_current_operating_point║
   ║                                                                                    ║
   ║ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ ║
   ║  SI lift_type == "SRP":                                                            ║
   ║  ┌────────────────────────────────────────────────────────────────────────────────┐ ║
   ║  │  Optimizacion SRP (Bombeo Mecanico)                                            │ ║
   ║  │                                                                                │ ║
   ║  │  ┌──────────────────┐         ┌──────────────────┐                             │ ║
   ║  │  │   SPM Actual     │  ────>  │  SPM Recomendado │                             │ ║
   ║  │  │     8.5 SPM      │ (verde) │    10.2 SPM      │                             │ ║
   ║  │  │  (fondo gris)    │         │  (fondo verde)   │                             │ ║
   ║  │  └──────────────────┘         └──────────────────┘                             │ ║
   ║  └────────────────────────────────────────────────────────────────────────────────┘ ║
   ║  Visibility: lift_type == "SRP"                                                    ║
   ║  Keys: spm (TS), opt_recommended_spm                                               ║
   ║                                                                                    ║
   ║ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ ║
   ║  SI lift_type == "gas_lift":                                                       ║
   ║  ┌────────────────────────────────────────────────────────────────────────────────┐ ║
   ║  │  Optimizacion Gas Lift                                                         │ ║
   ║  │                                                                                │ ║
   ║  │  ┌──────────────────────────────┐   ┌──────────────────────────────────────┐   │ ║
   ║  │  │ Tasa Inyeccion Recomendada   │   │ Nota: Curva GLPC disponible en       │   │ ║
   ║  │  │         450 MCFD             │   │ opt_glpc_curve cuando el servicio    │   │ ║
   ║  │  │  (fondo verde)               │   │ este activo.                         │   │ ║
   ║  │  └──────────────────────────────┘   └──────────────────────────────────────┘   │ ║
   ║  └────────────────────────────────────────────────────────────────────────────────┘ ║
   ║  Visibility: lift_type == "gas_lift"                                               ║
   ║  Keys: opt_recommended_injection_rate_mcfd                                         ║
   ║                                                                                    ║
   ║ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ ║
   ║  SI lift_type == "PCP":                                                            ║
   ║  ┌────────────────────────────────────────────────────────────────────────────────┐ ║
   ║  │  Optimizacion PCP (Cavidad Progresiva)                                         │ ║
   ║  │                                                                                │ ║
   ║  │  ┌──────────────────┐         ┌──────────────────┐                             │ ║
   ║  │  │   RPM Actual     │  ────>  │  RPM Recomendada │                             │ ║
   ║  │  │    180 RPM       │ (verde) │    210 RPM       │                             │ ║
   ║  │  │  (fondo gris)    │         │  (fondo verde)   │                             │ ║
   ║  │  └──────────────────┘         └──────────────────┘                             │ ║
   ║  └────────────────────────────────────────────────────────────────────────────────┘ ║
   ║  Visibility: lift_type == "PCP"                                                    ║
   ║  Keys: speed_rpm (TS), opt_recommended_speed_rpm                                   ║
   ║                                                                                    ║
   ╚══════════════════════════════════════════════════════════════════════════════════════╝
   4 widgets apilados en la misma posicion (Row 27, Col 0, sizeX:24, sizeY:4)
   Tipo: markdown_card (Markdown/HTML Value Card) x4
   Alias: "Pozo Seleccionado" (todos)
   Visibilidad condicional: solo 1 visible segun lift_type del pozo seleccionado
   Config: Entity alias "Pozo Seleccionado", Key "lift_type", Condition "Equal", Value "XXX"
```

**Nota sobre visibilidad condicional:** Los 4 widgets de optimizacion por tipo de
levantamiento ocupan la misma posicion en el grid. ThingsBoard muestra solo el que
cumple la condicion de visibilidad (`lift_type` del pozo seleccionado). Si ninguno
cumple, no se muestra ninguno.

---

## 7. PASO 5: Preparacion para el Servicio de Optimizacion

### Que sucede cuando el servicio se active

Cuando el servicio de optimizacion comience a funcionar:

1. **Los atributos `opt_*` se poblaran automaticamente.** El servicio escribe resultados como `SERVER_SCOPE` attributes en cada asset de pozo via la API REST de ThingsBoard:
   ```
   POST /api/plugins/telemetry/ASSET/{assetId}/attributes/SERVER_SCOPE
   Content-Type: application/json
   X-Authorization: Bearer {token}

   {
       "opt_status": "suboptimal",
       "opt_current_rate_bpd": 850,
       "opt_recommended_rate_bpd": 1050,
       "opt_potential_gain_bpd": 200,
       ...
   }
   ```

2. **Las alarmas apareceran en la tabla de alarmas.** El servicio crea alarmas via:
   ```
   POST /api/alarm
   Content-Type: application/json
   X-Authorization: Bearer {token}

   {
       "originator": {"entityType": "ASSET", "id": "{wellAssetId}"},
       "type": "WELL_SUBOPTIMAL",
       "severity": "WARNING",
       "status": "ACTIVE_UNACK",
       "details": {"message": "Pozo opera 23% debajo del potencial"}
   }
   ```

3. **Los JSON de curvas (IPR, VLP, DCA, GLPC)** se pueden renderizar usando Custom Widgets con ECharts. Ver seccion 8.

4. **El dashboard "cobrara vida" sin necesidad de modificaciones.** Todos los widgets ya estan conectados a los atributos correctos.

### Checklist de Verificacion Post-Activacion

Una vez que el servicio este activo, verificar:

- [ ] Los KPIs del estado principal muestran valores numericos (no cero).
- [ ] La tabla de recomendaciones muestra acciones en la columna "Accion Recomendada".
- [ ] Los scores de salud muestran colores (verde/naranja/rojo).
- [ ] La tabla de alarmas muestra alarmas de tipo `WELL_SUBOPTIMAL`, `PUMP_DEGRADATION`, etc.
- [ ] Al hacer click en una fila, se navega al estado `opt_detalle` con los datos del pozo.
- [ ] Los widgets especificos por tipo de levantamiento se muestran/ocultan correctamente.
- [ ] Los valores de `opt_recommended_frequency_hz`, `opt_recommended_spm`, etc. son coherentes con el tipo de pozo.

### Posibles Ajustes Necesarios

| Situacion | Accion |
|-----------|--------|
| Los nombres de atributos no coinciden exactamente | Verificar en ThingsBoard: ir al asset del pozo > Attributes > Server attributes. Ajustar los data keys en los widgets. |
| Los valores de `lift_type` usan formato diferente (ej: "esp" vs "ESP") | Ajustar las condiciones de visibilidad en los widgets del PASO 4 seccion 6.9. |
| El servicio publica atributos adicionales no contemplados | Agregar nuevas columnas a la tabla o nuevos widgets segun sea necesario. |
| Se desean curvas IPR/VLP en vez de placeholder | Implementar Custom Widget con ECharts (ver seccion 8). |

---

## 8. Tips de Implementacion Avanzada

### 8.1 Renderizar Curvas Nodales (IPR/VLP) con ECharts

Cuando los atributos `opt_nodal_ipr_curve` y `opt_nodal_vlp_curve` esten poblados con datos JSON, se puede crear un **Custom Widget** para renderizarlos.

**Formato esperado de los datos:**

```json
{
    "opt_nodal_ipr_curve": [[0, 2850], [200, 2700], [400, 2500], [600, 2200], [800, 1800], [1000, 1200], [1200, 0]],
    "opt_nodal_vlp_curve": [[0, 500], [200, 700], [400, 950], [600, 1250], [800, 1600], [1000, 2100], [1200, 2700]]
}
```

Cada elemento del array es `[caudal_bpd, presion_pwf_psi]`.

**Codigo JavaScript para Custom Widget (usando ECharts):**

```javascript
// En el onDataUpdated o onInit del Custom Widget:

var iprData = [];
var vlpData = [];

try {
    var iprRaw = self.ctx.data[0].data[0][1]; // opt_nodal_ipr_curve
    var vlpRaw = self.ctx.data[1].data[0][1]; // opt_nodal_vlp_curve

    if (typeof iprRaw === 'string') iprData = JSON.parse(iprRaw);
    if (typeof vlpRaw === 'string') vlpData = JSON.parse(vlpRaw);
} catch(e) {
    console.log('Datos de curvas nodales no disponibles');
}

if (iprData.length > 0 && vlpData.length > 0) {
    var chart = echarts.init(self.ctx.$container[0]);
    var option = {
        title: {
            text: 'Analisis Nodal (IPR / VLP)',
            left: 'center',
            textStyle: { color: '#305680', fontSize: 14, fontWeight: 600 }
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                return 'Caudal: ' + params[0].data[0] + ' BPD<br/>'
                    + params.map(function(p) {
                        return p.seriesName + ': ' + p.data[1] + ' PSI';
                    }).join('<br/>');
            }
        },
        legend: {
            data: ['IPR', 'VLP'],
            bottom: 0,
            textStyle: { color: '#4B535B' }
        },
        xAxis: {
            type: 'value',
            name: 'Caudal (BPD)',
            nameLocation: 'center',
            nameGap: 30,
            axisLabel: { color: '#9FA6B4' }
        },
        yAxis: {
            type: 'value',
            name: 'Pwf (PSI)',
            nameLocation: 'center',
            nameGap: 45,
            axisLabel: { color: '#9FA6B4' }
        },
        series: [
            {
                name: 'IPR',
                type: 'line',
                smooth: true,
                data: iprData,
                lineStyle: { color: '#305680', width: 2 },
                itemStyle: { color: '#305680' }
            },
            {
                name: 'VLP',
                type: 'line',
                smooth: true,
                data: vlpData,
                lineStyle: { color: '#F44336', width: 2 },
                itemStyle: { color: '#F44336' }
            }
        ],
        grid: { left: 60, right: 20, top: 40, bottom: 50 }
    };
    chart.setOption(option);
}
```

> **Como crear un Custom Widget en ThingsBoard:**
> 1. Ir a **Widget Library** > **"+"** > **"Create new widget type"**.
> 2. Seleccionar **"Static widget"**.
> 3. Pegar el codigo JavaScript en la seccion correspondiente.
> 4. En el dashboard, agregar el widget custom y configurar los datasources.

---

### 8.2 Color Functions para Scores de Salud

Funcion reutilizable para cualquier widget que muestre scores de 0 a 100:

```javascript
// Para usar en colorFunction de Value Card, Aggregated Value Card, etc.
var score = value;
if (score === null || score === undefined || score === 0) return '#9FA6B4';
if (score >= 80) return '#4CAF50';  // Verde - Bueno
if (score >= 60) return '#FF9800';  // Naranja - Medio
return '#F44336';                    // Rojo - Bajo
```

Variante con gradiente mas suave:

```javascript
var score = value;
if (score === null || score === undefined || score === 0) return '#9FA6B4';
if (score >= 90) return '#2E7D32';  // Verde oscuro
if (score >= 80) return '#4CAF50';  // Verde
if (score >= 70) return '#8BC34A';  // Verde claro
if (score >= 60) return '#FF9800';  // Naranja
if (score >= 50) return '#FF5722';  // Naranja-rojo
if (score >= 30) return '#F44336';  // Rojo
return '#B71C1C';                    // Rojo oscuro
```

---

### 8.3 Widget de Comparacion Actual vs Recomendado (Barras)

Para mostrar una comparacion visual simple entre el valor actual y el recomendado:

**Widget:** `Markdown/HTML Value Card`

**Datasource:**
- `flow_rate_bpd` (Timeseries, ultimo valor)
- `opt_recommended_rate_bpd` (Attribute, Server)

**Contenido HTML con calculo dinamico:**

```html
<div style="padding: 16px;">
    <h4 style="color: #305680; margin: 0 0 12px 0; font-weight: 600;">Actual vs Recomendado</h4>
    <div style="display: flex; align-items: end; gap: 24px; height: 80px; padding: 0 20px;">
        <div style="flex: 1; text-align: center;">
            <div style="background: linear-gradient(180deg, #305680 0%, #4A7AAF 100%); height: 60px; border-radius: 6px 6px 0 0; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-weight: 700; font-size: 14px;">${flow_rate_bpd:0}</span>
            </div>
            <div style="font-size: 11px; color: #9FA6B4; margin-top: 6px; font-weight: 500;">Actual (BPD)</div>
        </div>
        <div style="flex: 1; text-align: center;">
            <div style="background: linear-gradient(180deg, #4CAF50 0%, #66BB6A 100%); height: 75px; border-radius: 6px 6px 0 0; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-weight: 700; font-size: 14px;">${opt_recommended_rate_bpd:0}</span>
            </div>
            <div style="font-size: 11px; color: #9FA6B4; margin-top: 6px; font-weight: 500;">Recomendado (BPD)</div>
        </div>
    </div>
</div>
```

> **Nota:** Las alturas de las barras son fijas en este ejemplo. Para hacerlas proporcionales al valor real, se necesita un Custom Widget con JavaScript que calcule la altura relativa.

---

### 8.4 Colores de Severidad de Alarmas

Referencia de colores para usar consistentemente en widgets relacionados con alarmas:

| Severidad | Color | Hex | Uso |
|-----------|-------|-----|-----|
| CRITICAL | Rojo | `#F44336` | Fallas predichas, anomalias severas |
| MAJOR | Naranja | `#FF9800` | Degradacion de bomba, baja eficiencia |
| MINOR | Amarillo | `#FFC107` | Advertencias menores |
| WARNING | Azul | `#2196F3` | Informativas de optimizacion |
| INDETERMINATE | Gris | `#9FA6B4` | Estado indefinido |

---

### 8.5 Renderizar Pronostico DCA

Cuando `opt_dca_forecast` este poblado, el formato sera:

```json
[["2025-03", 830], ["2025-04", 815], ["2025-05", 798], ["2025-06", 781]]
```

**Codigo JavaScript para Custom Widget (ECharts):**

```javascript
var dcaData = [];

try {
    var raw = self.ctx.data[0].data[0][1]; // opt_dca_forecast
    if (typeof raw === 'string') dcaData = JSON.parse(raw);
} catch(e) {
    console.log('Datos DCA no disponibles');
}

if (dcaData.length > 0) {
    var chart = echarts.init(self.ctx.$container[0]);
    var option = {
        title: {
            text: 'Pronostico de Produccion (DCA)',
            left: 'center',
            textStyle: { color: '#305680', fontSize: 14, fontWeight: 600 }
        },
        tooltip: { trigger: 'axis' },
        xAxis: {
            type: 'category',
            data: dcaData.map(function(d) { return d[0]; }),
            axisLabel: { color: '#9FA6B4', rotate: 45 }
        },
        yAxis: {
            type: 'value',
            name: 'Produccion (BPD)',
            axisLabel: { color: '#9FA6B4' }
        },
        series: [{
            name: 'Pronostico',
            type: 'line',
            data: dcaData.map(function(d) { return d[1]; }),
            smooth: true,
            lineStyle: { color: '#FF9800', width: 2 },
            itemStyle: { color: '#FF9800' },
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [
                        { offset: 0, color: 'rgba(255, 152, 0, 0.3)' },
                        { offset: 1, color: 'rgba(255, 152, 0, 0.05)' }
                    ]
                }
            }
        }],
        grid: { left: 60, right: 20, top: 40, bottom: 60 }
    };
    chart.setOption(option);
}
```

---

### 8.6 Renderizar Curva GLPC (Gas Lift Performance Curve)

Formato esperado de `opt_glpc_curve`:

```json
[[0, 0], [200, 350], [400, 580], [600, 720], [800, 800], [1000, 830], [1200, 840]]
```

Cada elemento: `[tasa_inyeccion_gas_mcfd, produccion_liquido_bpd]`.

El mismo patron de Custom Widget con ECharts se aplica, cambiando los ejes:
- Eje X: Tasa de Inyeccion de Gas (MCFD)
- Eje Y: Produccion de Liquido (BPD)

---

### 8.7 Distribucion de Salud con Conteo Dinamico

Para implementar el conteo dinamico de pozos por categoria de salud cuando los datos esten disponibles, se puede crear un Custom Widget con esta logica:

```javascript
// onDataUpdated
var high = 0, medium = 0, low = 0;

self.ctx.data.forEach(function(datasource) {
    datasource.data.forEach(function(point) {
        var score = Number(point[1]);
        if (isNaN(score) || score === 0) return;
        if (score >= 80) high++;
        else if (score >= 60) medium++;
        else low++;
    });
});

var html = '<div style="display: flex; gap: 12px; height: 100%; padding: 16px;">';
html += '<div style="flex: 1; text-align: center; padding: 16px; background: #E8F5E9; border-radius: 8px;">';
html += '<div style="font-size: 36px; font-weight: 700; color: #4CAF50;">' + high + '</div>';
html += '<div style="font-size: 12px; color: #4CAF50; font-weight: 600;">BUENA (>80)</div></div>';
html += '<div style="flex: 1; text-align: center; padding: 16px; background: #FFF3E0; border-radius: 8px;">';
html += '<div style="font-size: 36px; font-weight: 700; color: #FF9800;">' + medium + '</div>';
html += '<div style="font-size: 12px; color: #FF9800; font-weight: 600;">MEDIA (60-80)</div></div>';
html += '<div style="flex: 1; text-align: center; padding: 16px; background: #FFEBEE; border-radius: 8px;">';
html += '<div style="font-size: 36px; font-weight: 700; color: #F44336;">' + low + '</div>';
html += '<div style="font-size: 12px; color: #F44336; font-weight: 600;">BAJA (<60)</div></div>';
html += '</div>';

self.ctx.$container.html(html);
```

---

## 9. Referencia Rapida de Atributos

### Todos los Atributos opt_* del Servicio de Optimizacion

```
GENERALES:
  opt_status                          str     "optimized"|"suboptimal"|"pending"|"error"|"not_analyzed"
  opt_current_rate_bpd                float   Tasa actual (BPD)
  opt_recommended_rate_bpd            float   Tasa recomendada (BPD)
  opt_potential_gain_bpd              float   Ganancia potencial (BPD)
  opt_recommended_action              str     Codigo de accion
  opt_recommended_action_detail       str     Descripcion de la accion
  opt_efficiency_pct                  float   Eficiencia del sistema (%)
  opt_energy_kwh_bbl                  float   Consumo energetico (kWh/bbl)
  opt_well_health_score               float   Score de salud (0-100)
  opt_decline_rate_monthly_pct        float   Declive mensual (%)
  opt_eur_mstb                        float   EUR estimado (MSTB)
  opt_days_to_predicted_failure       float   Dias para falla predicha
  opt_failure_probability             float   Probabilidad de falla (0-1)
  opt_cluster_id                      str     ID de cluster
  opt_similar_wells                   str     JSON array de pozos similares
  opt_anomaly_score                   float   Score de anomalia (0-1)
  opt_anomaly_type                    str     Tipo de anomalia

CURVAS (JSON):
  opt_nodal_ipr_curve                 str     JSON [[q, pwf], ...]
  opt_nodal_vlp_curve                 str     JSON [[q, pwf], ...]
  opt_dca_forecast                    str     JSON [["YYYY-MM", rate], ...]
  opt_glpc_curve                      str     JSON [[qgl, qo], ...] (solo Gas Lift)

ESPECIFICOS POR TIPO:
  opt_recommended_frequency_hz        float   ESP - Frecuencia recomendada
  opt_current_operating_point_bpd     float   ESP - Punto operacion actual
  opt_recommended_spm                 float   SRP - SPM recomendado
  opt_recommended_injection_rate_mcfd float   Gas Lift - Inyeccion recomendada
  opt_recommended_speed_rpm           float   PCP - RPM recomendada
```

### Tipos de Alarma de Optimizacion

```
WELL_SUBOPTIMAL       WARNING    Pozo >20% debajo del potencial
PUMP_DEGRADATION      MAJOR      Eficiencia bomba <55%
ACCELERATED_DECLINE   WARNING    Declive >5%/mes
ESP_FAILURE_PREDICTED CRITICAL   Probabilidad falla >70%
ANOMALY_DETECTED      WARNING    Score anomalia >0.8
CASING_HEADING        WARNING    Cabeceo de casing detectado
LIFT_METHOD_REVIEW    INFO       Candidato a cambio levantamiento
```

### Paleta de Colores del Dashboard

```
Primario:        #305680   (Azul oscuro, titulos y valores principales)
Texto:           #4B535B   (Gris oscuro, texto general)
Subtitulo:       #9FA6B4   (Gris claro, subtitulos y labels)
Fondo claro:     #F5F7FA   (Gris muy claro, fondos de tarjetas)
Fondo blanco:    #FFFFFF   (Blanco, fondo de widgets)

Bueno/Alto:      #4CAF50   (Verde, scores altos, ganancias positivas)
Medio:           #FF9800   (Naranja, scores medios, advertencias)
Bajo/Critico:    #F44336   (Rojo, scores bajos, fallas)
Informativo:     #2196F3   (Azul, informacion general)
Inactivo:        #9FA6B4   (Gris, datos no disponibles)

Fondos estado:
  Bueno:         #E8F5E9   (Verde palido)
  Medio:         #FFF3E0   (Naranja palido)
  Bajo:          #FFEBEE   (Rojo palido)
  Info:          #E3F2FD   (Azul palido)
```

---

## Notas Finales

### Orden de Construccion Recomendado

1. Crear el dashboard y aplicar CSS (seccion 3).
2. Configurar todos los Entity Aliases (seccion 4).
3. Construir el estado principal con todos los widgets (seccion 5).
4. Crear el estado `opt_detalle` con todos los widgets (seccion 6).
5. Probar la navegacion entre estados (click en tabla > detalle > volver).
6. Guardar el dashboard.

### Consideraciones de Rendimiento

- La tabla de recomendaciones carga datos de los 63 pozos. Si el rendimiento es lento, considerar usar paginacion del lado del servidor.
- Los widgets de tipo `Aggregated value card` con multiples entidades pueden ser mas lentos. Considerar cachear los calculos en un timer del servicio de optimizacion.
- Los Custom Widgets con ECharts deben usar `chart.dispose()` en el `onDestroy` para liberar memoria.

### Compatibilidad

Esta guia fue escrita para **ThingsBoard PE v4.3**. Los nombres exactos de los widgets y sus opciones de configuracion pueden variar ligeramente entre versiones. Si un widget especifico no se encuentra:

- Buscar por nombre parcial en la biblioteca de widgets.
- Consultar la documentacion oficial de ThingsBoard para la version instalada.
- Los widgets del bundle `Cards` y `Charts` estan disponibles en todas las ediciones PE.
