# Guia Paso a Paso: Dashboard "KPIs Generales y Lista de Pozos"

## ThingsBoard PE v4.3 - Atilax Simulador de Pozos

**Objetivo:** Crear un dashboard enfocado en metricas operativas generales del campo petrolero, con una tabla filtrable de todos los pozos y navegacion drill-down hacia la vista de detalle individual de cada pozo.

**Datos del sistema:**
- 63 pozos totales: 18 ESP, 20 SRP, 16 PCP, 9 Gas Lift
- 3 campos: Campo Boscan (24 pozos), Campo Cerro Negro (27 pozos), Campo Anaco (12 pozos)
- 7 macollas distribuidas entre los campos

**Acceso a ThingsBoard:**
- URL: `http://144.126.150.120:8080`
- Usuario: `well@atilax.io`
- Contrasena: `10203040`

---

## Indice

1. [Paso 1: Crear Dashboard y Configuracion General](#paso-1-crear-dashboard-y-configuracion-general)
2. [Paso 2: Crear Entity Aliases](#paso-2-crear-entity-aliases)
3. [Paso 3: Estado Principal - Panel de KPIs](#paso-3-estado-principal---panel-de-kpis)
4. [Paso 4: Estado de Detalle del Pozo](#paso-4-estado-de-detalle-del-pozo-pozo_detalle)
5. [Paso 5: Configurar Navegacion entre Estados](#paso-5-configurar-navegacion-entre-estados)
6. [Tips de Diseno y Referencia Rapida](#tips-de-diseno-y-referencia-rapida)

---

## Paso 1: Crear Dashboard y Configuracion General

### 1.1 Crear el Dashboard

1. Ingresar a ThingsBoard en `http://144.126.150.120:8080` con las credenciales indicadas.
2. Ir al menu lateral izquierdo y seleccionar **Dashboards**.
3. Hacer clic en el boton **"+"** (esquina inferior derecha) y seleccionar **"Create new dashboard"**.
4. En el formulario:
   - **Title:** `Atilax - KPIs y Produccion`
   - **Description:** `Dashboard de KPIs generales, produccion por tipo de levantamiento y lista detallada de pozos con drill-down`
5. Hacer clic en **"Add"** para crear el dashboard.
6. Se abrira el dashboard vacio. Hacer clic en el icono de **lapiz** (editar) en la esquina inferior derecha para entrar en modo edicion.

### 1.2 Configurar Ajustes del Dashboard

1. En modo edicion, hacer clic en el icono de **engranaje** (Settings) en la barra superior derecha.
2. Configurar los siguientes parametros:

   - **State controller:** Seleccionar `entity` del dropdown.
   - **Show entity selector:** Activar (toggle ON).
   - **Show dashboard timewindow:** Activar (toggle ON).
   - **Toolbar always open:** Activar (toggle ON).

3. Hacer clic en **"Apply"** o **"Save"** para guardar los ajustes.

### 1.3 Agregar CSS Personalizado del Dashboard

1. Dentro de Settings del dashboard, buscar el campo **"Dashboard CSS"**.
2. Pegar el siguiente CSS completo:

```css
.tb-widget-container > .tb-widget {
    border-radius: 8px;
    box-shadow: 0px 2px 8px rgba(222, 223, 224, 0.25);
}

.tb-dashboard-page .tb-widget-container > .tb-widget {
    color: #4B535B !important;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .tb-markdown-view {
    overflow: hidden !important;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-mdc-table .mat-mdc-header-cell {
    color: rgba(0, 0, 0, 0.38) !important;
    font-weight: 500;
    font-size: 12px;
    line-height: 16px;
    letter-spacing: 0.25px;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-mdc-table .mat-mdc-cell {
    color: #4B535B;
    border-bottom-color: transparent;
    font-size: 14px;
    line-height: 20px;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-table .mat-row:hover:not(.tb-current-entity),
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-table .mat-row:hover:not(.tb-current-entity) .mat-cell.mat-table-sticky {
    background-color: #F9F9FB !important;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-mdc-table .mat-mdc-cell button.mat-mdc-icon-button .mat-icon,
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-widget-actions .mat-icon {
    color: #00000061 !important;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-paginator,
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-paginator button.mat-icon-button,
.tb-dashboard-page .tb-widget-container > .tb-widget .tb-table-widget .mat-paginator .mat-select-value {
    color: #9FA6B4 !important;
}
```

3. Hacer clic en **"Apply"** para guardar.

> **Nota:** Este CSS mejora la apariencia de las tablas, agrega bordes redondeados a los widgets y unifica la paleta de colores del dashboard.

---

## Paso 2: Crear Entity Aliases

Los Entity Aliases son fundamentales para conectar los widgets con los datos correctos. Vamos a crear 7 aliases que el dashboard utilizara.

### 2.1 Abrir el Editor de Entity Aliases

1. En modo edicion del dashboard, hacer clic en el icono de **"Entity aliases"** en la barra superior (icono que parece un enlace de cadena).
2. Se abrira el dialogo de Entity Aliases.

### 2.2 Alias: "Todos los Pozos"

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Todos los Pozos`
   - **Filter type:** `Asset type`
   - **Asset type:** Escribir `well` y seleccionar del dropdown.
   - **Resolve as multiple entities:** Activar (toggle ON).
3. Hacer clic en **"Add"**.

### 2.3 Alias: "Pozos ESP"

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Pozos ESP`
   - **Filter type:** `Asset type`
   - **Asset type:** `well`
   - **Resolve as multiple entities:** Activar (toggle ON).
3. Hacer clic en **"Add key filter"** (debajo de la configuracion del alias):
   - **Key:** `lift_type`
   - **Key type:** `Attribute`
   - **Value type:** `String`
   - **Operation:** `EQUAL`
   - **Value:** `esp`
4. Hacer clic en **"Add"**.

### 2.4 Alias: "Pozos SRP"

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Pozos SRP`
   - **Filter type:** `Asset type`
   - **Asset type:** `well`
   - **Resolve as multiple entities:** Activar (toggle ON).
3. Agregar key filter:
   - **Key:** `lift_type`
   - **Key type:** `Attribute`
   - **Operation:** `EQUAL`
   - **Value:** `srp`
4. Hacer clic en **"Add"**.

### 2.5 Alias: "Pozos PCP"

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Pozos PCP`
   - **Filter type:** `Asset type`
   - **Asset type:** `well`
   - **Resolve as multiple entities:** Activar (toggle ON).
3. Agregar key filter:
   - **Key:** `lift_type`
   - **Key type:** `Attribute`
   - **Operation:** `EQUAL`
   - **Value:** `pcp`
4. Hacer clic en **"Add"**.

### 2.6 Alias: "Pozos Gas Lift"

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Pozos Gas Lift`
   - **Filter type:** `Asset type`
   - **Asset type:** `well`
   - **Resolve as multiple entities:** Activar (toggle ON).
3. Agregar key filter:
   - **Key:** `lift_type`
   - **Key type:** `Attribute`
   - **Operation:** `EQUAL`
   - **Value:** `gaslift`
4. Hacer clic en **"Add"**.

### 2.7 Alias: "Usuario Actual"

Este alias se usa para almacenar preferencias de filtro del usuario actual.

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Usuario Actual`
   - **Filter type:** `Single entity`
   - **Type:** `Current User`
3. Hacer clic en **"Add"**.

### 2.8 Alias: "Pozo Seleccionado"

Este alias se usa en el estado de detalle para mostrar datos de un pozo individual seleccionado desde la tabla.

1. Hacer clic en **"Add alias"**.
2. Configurar:
   - **Alias name:** `Pozo Seleccionado`
   - **Filter type:** `Entity from dashboard state`
3. Hacer clic en **"Add"**.

4. Finalmente, hacer clic en **"Save"** en el dialogo de Entity Aliases para guardar todos los aliases creados.

---

## Paso 3: Estado Principal - Panel de KPIs

El estado principal (`default`) es lo que el usuario ve al abrir el dashboard. Contiene KPIs resumidos, graficos de produccion y la tabla completa de pozos.

**Layout:** Grid de 24 columnas (configuracion por defecto de ThingsBoard).

**Diagrama visual del estado principal (default):**

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║              DASHBOARD: KPIs y Produccion — Estado Principal (default)                  ║
║              Grid: 24 columnas | Widgets: 7 | Rows totales: ~31                         ║
╠══════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                          ║
║  ROW 0-1  (sizeY: 2)                                                                    ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  ATILAX — KPIs y Produccion         │ 63 Pozos │ 3 Campos │ 7 Macollas         │    ║
║  │  Monitoreo en tiempo real del campo petrolero simulado                          │    ║
║  └──────────────────────────────────────────────────────────────────────────────────┘    ║
║   ^--- col:0  sizeX:24  sizeY:2                                                         ║
║   Widget: system.cards.markdown_card  (Alias: Todos los Pozos o sin datasource)          ║
║                                                                                          ║
║  ROW 3-6  (sizeY: 4, 4 tarjetas KPI)                                                    ║
║  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                ║
║  │  Produccion   │ │  Produccion   │ │  Produccion   │ │  Produccion   │                ║
║  │     ESP       │ │     SRP       │ │     PCP       │ │   Gas Lift    │                ║
║  │  18 pozos     │ │  20 pozos     │ │  16 pozos     │ │   9 pozos     │                ║
║  │               │ │               │ │               │ │               │                ║
║  │  ▓▓▓ 4,250   │ │  ▓▓▓ 3,800   │ │  ▓▓▓ 2,100   │ │  ▓▓▓ 1,350   │                ║
║  │   BPD  ~~~   │ │   BPD  ~~~   │ │   BPD  ~~~   │ │   BPD  ~~~   │                ║
║  │  #4CAF50     │ │  #2196F3     │ │  #FF9800     │ │  #9C27B0     │                ║
║  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘                ║
║   col:0 sizeX:6     col:6 sizeX:6    col:12 sizeX:6    col:18 sizeX:6                   ║
║   Widget: system.cards.aggregated_value_card  (Aliases: Pozos ESP/SRP/PCP/Gas Lift)      ║
║                                                                                          ║
║  ROW 8-15  (sizeY: 8, grafico + resumen)                                                ║
║  ┌──────────────────────────────────────────┐ ┌────────────────────────┐                ║
║  │  Produccion por Tipo de Levantamiento    │ │  Resumen por Campo     │                ║
║  │                                          │ │                        │                ║
║  │  BPD                                     │ │  ┌──────────────────┐  │                ║
║  │  12k ┤                                   │ │  │ # Campo Boscan   │  │                ║
║  │  10k ┤    ╱‾‾‾‾╲        ───Total         │ │  │   Lago           │  │                ║
║  │   8k ┤   ╱      ╲       ---ESP           │ │  │   24 pozos       │  │                ║
║  │   6k ┤──╱        ╲──    ---SRP           │ │  │   3 macollas     │  │                ║
║  │   4k ┤              ──  ---PCP           │ │  └──────────────────┘  │                ║
║  │   2k ┤                  ---GL            │ │  ┌──────────────────┐  │                ║
║  │    0 ┼──┬──┬──┬──┬──┬──                  │ │  │ # Cerro Negro    │  │                ║
║  │       E  F  M  A  M  J                   │ │  │   Faja           │  │                ║
║  │  [ESP] [SRP] [PCP] [GL] [Total]          │ │  │   27 pozos       │  │                ║
║  └──────────────────────────────────────────┘ │  │   2 macollas     │  │                ║
║   col:0 sizeX:16  sizeY:8                     │  └──────────────────┘  │                ║
║   Widget: system.time_series_chart             │  ┌──────────────────┐  │                ║
║   Alias: Todos los Pozos + por tipo            │  │ # Campo Anaco    │  │                ║
║   Key: flow_rate_bpd (SUM)                     │  │   Oriente        │  │                ║
║                                                │  │   12 pozos       │  │                ║
║                                                │  │   2 macollas     │  │                ║
║                                                │  └──────────────────┘  │                ║
║                                                └────────────────────────┘                ║
║                                                 col:16 sizeX:8  sizeY:8                  ║
║                                                 Widget: system.cards.markdown_card        ║
║                                                 (Sin datasource - contenido estatico)     ║
║                                                                                          ║
║  ROW 17-18  (sizeY: 2, barra de filtros)                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  Filtros:  [ESP: ON] [SRP: ON] [PCP: ON] [GL: ON]  │  [Boscan: ON]             │    ║
║  │            [Cerro Negro: ON] [Anaco: ON]                                        │    ║
║  └──────────────────────────────────────────────────────────────────────────────────┘    ║
║   col:0 sizeX:24  sizeY:2                                                               ║
║   Widget: system.input_widgets.update_multiple_attributes                                ║
║   Alias: Usuario Actual  |  Keys: show_esp, show_srp, show_pcp, show_gaslift,           ║
║   show_campo_boscan, show_campo_cerronegro, show_campo_anaco (Server attributes)         ║
║                                                                                          ║
║  ROW 19-30  (sizeY: 12, tabla completa)                                                  ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐    ║
║  │  Lista de Pozos                                              [Buscar...]        │    ║
║  ├──────────┬───────┬───────────┬──────────┬──────────┬──────┬──────┬───────┬──────┤    ║
║  │  Pozo    │ Tipo  │ Campo     │ Macolla  │ Prod BPD │ Ptbg │ Amp  │Estado │Salud │    ║
║  ├──────────┼───────┼───────────┼──────────┼──────────┼──────┼──────┼───────┼──────┤    ║
║  │ BOS-E01  │ [ESP] │ Boscan    │ Mac-B1   │   542.3  │ 1250 │ 32.1 │  OK  │  87  │    ║
║  │ BOS-S01  │ [SRP] │ Boscan    │ Mac-B1   │   285.7  │  980 │ 18.4 │  OK  │  92  │    ║
║  │ CN-P01   │ [PCP] │ C. Negro  │ Mac-CN1  │   198.2  │  870 │ 22.7 │  OK  │  78  │    ║
║  │ ANA-G01  │ [GL]  │ Anaco     │ Mac-A1   │   312.5  │ 1100 │ 15.3 │  OK  │  85  │    ║
║  │ BOS-E02  │ [ESP] │ Boscan    │ Mac-B2   │   478.9  │ 1180 │ 29.8 │ WARN │  65  │    ║
║  │   ...    │  ...  │   ...     │   ...    │    ...   │  ... │  ... │  ... │  ... │    ║
║  ├──────────┴───────┴───────────┴──────────┴──────────┴──────┴──────┴───────┴──────┤    ║
║  │  Mostrando 1-15 de 63 pozos                         [<] [1] [2] [3] [4] [5] [>]│    ║
║  └──────────────────────────────────────────────────────────────────────────────────┘    ║
║   col:0 sizeX:24  sizeY:12                                                              ║
║   Widget: system.cards.entities_table                                                    ║
║   Alias: Todos los Pozos  |  Accion Row Click -> navegar a estado "pozo_detalle"         ║
║   Sort: -flow_rate_bpd (desc)  |  Page size: 15  |  Busqueda habilitada                 ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝

RESUMEN DE POSICIONES - Estado default:
 Widget                          | col | row | sizeX | sizeY | Alias
 --------------------------------|-----|-----|-------|-------|---------------------------
 Titulo y Resumen (HTML)         |  0  |  0  |  24   |   2   | (sin datasource / estatico)
 KPI ESP                         |  0  |  3  |   6   |   4   | Pozos ESP
 KPI SRP                         |  6  |  3  |   6   |   4   | Pozos SRP
 KPI PCP                         | 12  |  3  |   6   |   4   | Pozos PCP
 KPI Gas Lift                    | 18  |  3  |   6   |   4   | Pozos Gas Lift
 Grafico Produccion por Tipo     |  0  |  8  |  16   |   8   | Todos + ESP/SRP/PCP/GL
 Resumen por Campo (HTML)        | 16  |  8  |   8   |   8   | (sin datasource / estatico)
 Filtros (Toggle switches)       |  0  | 17  |  24   |   2   | Usuario Actual
 Tabla Completa de Pozos         |  0  | 19  |  24   |  12   | Todos los Pozos
```

### 3.1 Widget: Titulo y Resumen (Row 0)

**Tipo de widget:** `system.cards.markdown_card` (HTML/Markdown Card)

**Posicion y tamano:**
- col: 0, row: 0
- sizeX: 24, sizeY: 2

**Pasos:**
1. Hacer clic en **"Add new widget"** en el dashboard.
2. En el buscador de widgets, buscar `Markdown/HTML value card` dentro del bundle **Cards**.
3. Seleccionar el widget **"HTML/Markdown Card"** (typeFullFqn: `system.cards.markdown_card`).

**Configuracion del Datasource:**
- No se requiere datasource para este widget (es contenido estatico).
- Si el widget pide un datasource obligatorio, seleccionar el alias `Todos los Pozos` con cualquier clave.

**Contenido HTML (pegar en el campo "Markdown/HTML pattern"):**

```html
<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 16px;">
    <div>
        <h2 style="margin: 0; color: #305680; font-size: 22px; font-weight: 700;">Panel de Produccion</h2>
        <span style="color: #9FA6B4; font-size: 13px;">Resumen operativo de los campos petroleros Atilax</span>
    </div>
    <div style="display: flex; gap: 12px;">
        <div style="text-align: center; padding: 8px 16px; background: #E8F5E9; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: 700; color: #4CAF50;">63</div>
            <div style="font-size: 11px; color: #66BB6A;">Total Pozos</div>
        </div>
        <div style="text-align: center; padding: 8px 16px; background: #E3F2FD; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: 700; color: #2196F3;">3</div>
            <div style="font-size: 11px; color: #42A5F5;">Campos</div>
        </div>
        <div style="text-align: center; padding: 8px 16px; background: #FFF3E0; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: 700; color: #FF9800;">7</div>
            <div style="font-size: 11px; color: #FFA726;">Macollas</div>
        </div>
    </div>
</div>
```

**Ajustes del widget:**
- Pestaña **Appearance:**
  - Background color: `#FFFFFF`
  - Padding: `0px`
- Pestaña **Widget card:**
  - Show widget title: NO (desactivar)
  - Enable drop shadow: NO (ya lo maneja el CSS global)

5. Hacer clic en **"Add"** para colocar el widget en el dashboard.
6. Redimensionar arrastrando las esquinas hasta que ocupe todo el ancho (24 columnas) y altura de 2 unidades.

---

### 3.2 Widgets: KPI Cards por Tipo de Levantamiento (Row 3)

Vamos a crear 4 tarjetas de KPI, una por cada tipo de levantamiento. Cada tarjeta muestra la produccion total sumada de ese tipo con un mini-grafico de tendencia.

**Tipo de widget:** `system.cards.aggregated_value_card`

**Posicion:** Row 3 (debajo del titulo). Cada tarjeta ocupa sizeX: 6, sizeY: 4.

#### 3.2.1 Tarjeta: Produccion ESP

1. Hacer clic en **"Add new widget"**.
2. Buscar `Aggregated value card` en el bundle **Cards**.
3. Seleccionar **"Aggregated value card"** (typeFullFqn: `system.cards.aggregated_value_card`).

**Datasource:**
- Entity alias: `Pozos ESP`
- Hacer clic en **"+ Add"** para agregar data key:
  - Key: `flow_rate_bpd`
  - Type: `Timeseries`
  - Aggregation: `SUM`
  - Label: `Produccion`

> **Importante:** Seleccionar **"Latest telemetry"** como tipo de fuente de datos (no "Timeseries"). Esto asegura que SUM sume solo el ultimo valor de cada pozo. Con el modo Timeseries + timewindow, SUM sumaria todos los puntos del rango temporal y mostraria valores de millones en lugar del valor real esperado de ~20,945 BPD (18 pozos ESP).

**Configuracion del widget (pestaña Appearance):**

- **Title:** `Produccion ESP`
- **Subtitle:** `18 pozos ESP`
- **Units:** `BPD`
- **Show chart:** Activar (toggle ON)
- **Chart type:** `line`
- **Chart color:** `#4CAF50`

**Configuracion JSON avanzada** (en la pestaña Advanced, campo "Widget settings"):

```json
{
    "autoScale": true,
    "showTitle": true,
    "showSubtitle": true,
    "showChart": true,
    "chartType": "line",
    "chartColor": "#4CAF50",
    "valueFont": {
        "size": 36,
        "sizeUnit": "px",
        "weight": "700",
        "family": "Roboto",
        "style": "normal"
    },
    "titleFont": {
        "size": 14,
        "sizeUnit": "px",
        "weight": "500"
    },
    "subtitleFont": {
        "size": 12,
        "sizeUnit": "px",
        "weight": "400"
    }
}
```

**Posicion:** col: 0, row: 3, sizeX: 6, sizeY: 4.

4. Hacer clic en **"Add"**.

#### 3.2.2 Tarjeta: Produccion SRP

Repetir el mismo proceso del punto 3.2.1 con estas diferencias:

- **Entity alias:** `Pozos SRP`
- **Title:** `Produccion SRP`
- **Subtitle:** `20 pozos SRP`
- **Chart color:** `#2196F3`
- **Posicion:** col: 6, row: 3, sizeX: 6, sizeY: 4

> **Importante:** Seleccionar **"Latest telemetry"** como tipo de fuente de datos (no "Timeseries"). Esto asegura que SUM sume solo el ultimo valor de cada pozo. Con el modo Timeseries + timewindow, SUM sumaria todos los puntos del rango temporal y mostraria valores de millones en lugar del valor real esperado de ~35,253 BPD (20 pozos SRP).

En el JSON de configuracion, cambiar:
```json
"chartColor": "#2196F3"
```

#### 3.2.3 Tarjeta: Produccion PCP

Repetir con:

- **Entity alias:** `Pozos PCP`
- **Title:** `Produccion PCP`
- **Subtitle:** `16 pozos PCP`
- **Chart color:** `#FF9800`
- **Posicion:** col: 12, row: 3, sizeX: 6, sizeY: 4

> **Importante:** Seleccionar **"Latest telemetry"** como tipo de fuente de datos (no "Timeseries"). Esto asegura que SUM sume solo el ultimo valor de cada pozo. Con el modo Timeseries + timewindow, SUM sumaria todos los puntos del rango temporal y mostraria valores de millones en lugar del valor real esperado de ~25,366 BPD (16 pozos PCP).

En el JSON:
```json
"chartColor": "#FF9800"
```

#### 3.2.4 Tarjeta: Produccion Gas Lift

Repetir con:

- **Entity alias:** `Pozos Gas Lift`
- **Title:** `Produccion Gas Lift`
- **Subtitle:** `9 pozos Gas Lift`
- **Chart color:** `#9C27B0`
- **Posicion:** col: 18, row: 3, sizeX: 6, sizeY: 4

> **Importante:** Seleccionar **"Latest telemetry"** como tipo de fuente de datos (no "Timeseries"). Esto asegura que SUM sume solo el ultimo valor de cada pozo. Con el modo Timeseries + timewindow, SUM sumaria todos los puntos del rango temporal y mostraria valores de millones en lugar del valor real esperado de ~9,178 BPD (9 pozos Gas Lift).

En el JSON:
```json
"chartColor": "#9C27B0"
```

---

### 3.3 Widget: Grafico de Produccion Total (Row 8, izquierda)

**Tipo de widget:** `system.time_series_chart` (Time Series Chart)

**Posicion y tamano:**
- col: 0, row: 8
- sizeX: 16, sizeY: 8

**Pasos:**
1. Hacer clic en **"Add new widget"**.
2. Buscar `Time series chart` en el bundle **Charts**.
3. Seleccionar **"Time series chart"** (typeFullFqn: `system.time_series_chart`).

**Datasources (5 en total):**

Agregar cada datasource haciendo clic en **"+ Add datasource"**:

| # | Entity Alias | Data Key | Aggregation | Label | Color |
|---|---|---|---|---|---|
| 1 | `Todos los Pozos` | `flow_rate_bpd` (timeseries) | SUM | `Produccion Total` | `#305680` |
| 2 | `Pozos ESP` | `flow_rate_bpd` (timeseries) | SUM | `ESP` | `#4CAF50` |
| 3 | `Pozos SRP` | `flow_rate_bpd` (timeseries) | SUM | `SRP` | `#2196F3` |
| 4 | `Pozos PCP` | `flow_rate_bpd` (timeseries) | SUM | `PCP` | `#FF9800` |
| 5 | `Pozos Gas Lift` | `flow_rate_bpd` (timeseries) | SUM | `Gas Lift` | `#9C27B0` |

**Para configurar cada data key:**
1. Seleccionar el alias correspondiente.
2. Hacer clic en **"+ Add"** en data keys.
3. Escribir `flow_rate_bpd` y seleccionar del autocompletado.
4. En la configuracion de la key:
   - **Label:** Escribir el nombre correspondiente (ej. "Produccion Total")
   - **Color:** Seleccionar el color indicado
   - **Aggregation:** Seleccionar `SUM`

**Configuracion del Chart (pestaña Appearance):**

Titulo del widget: `Produccion por Tipo de Levantamiento`

Configuracion avanzada:

```json
{
    "showLegend": true,
    "legendConfig": {
        "position": "bottom",
        "direction": "row"
    },
    "yAxes": {
        "default": {
            "label": "Produccion (BPD)",
            "position": "left"
        }
    },
    "tooltipBackgroundColor": "rgba(0, 0, 0, 0.76)",
    "tooltipBackgroundBlur": 4,
    "animation": {
        "enabled": true
    }
}
```

**Configuracion visual recomendada:**
- En la pestaña **"Series"**, para la serie "Produccion Total":
  - Line width: `3`
  - Fill: `0.1` (relleno sutil)
- Para las demas series (ESP, SRP, PCP, Gas Lift):
  - Line width: `2`
  - Fill: `0` (sin relleno)

4. Hacer clic en **"Add"** para colocar el widget.

---

### 3.4 Widget: Resumen por Campo (Row 8, derecha)

**Tipo de widget:** `system.cards.markdown_card`

**Posicion y tamano:**
- col: 16, row: 8
- sizeX: 8, sizeY: 8

**Pasos:**
1. Agregar un nuevo widget de tipo **"HTML/Markdown Card"** (`system.cards.markdown_card`).

**Datasource:** No requiere datasource (contenido estatico).

**Contenido HTML:**

```html
<div style="padding: 12px;">
    <h3 style="color: #305680; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">Resumen por Campo</h3>

    <div style="margin-bottom: 16px; padding: 12px; background: #F5F7FA; border-radius: 8px; border-left: 4px solid #4CAF50;">
        <div style="font-weight: 600; font-size: 14px; color: #4B535B;">Campo Boscan</div>
        <div style="color: #9FA6B4; font-size: 12px; margin-top: 4px;">Lago de Maracaibo</div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
            <span style="font-size: 12px; color: #4B535B;"><b>24</b> pozos</span>
            <span style="font-size: 12px; color: #4B535B;"><b>3</b> macollas</span>
            <span style="font-size: 12px; color: #9FA6B4;">SRP, ESP, GL, PCP</span>
        </div>
    </div>

    <div style="margin-bottom: 16px; padding: 12px; background: #F5F7FA; border-radius: 8px; border-left: 4px solid #2196F3;">
        <div style="font-weight: 600; font-size: 14px; color: #4B535B;">Campo Cerro Negro</div>
        <div style="color: #9FA6B4; font-size: 12px; margin-top: 4px;">Faja del Orinoco</div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
            <span style="font-size: 12px; color: #4B535B;"><b>27</b> pozos</span>
            <span style="font-size: 12px; color: #4B535B;"><b>2</b> macollas</span>
            <span style="font-size: 12px; color: #9FA6B4;">PCP, ESP, SRP</span>
        </div>
    </div>

    <div style="padding: 12px; background: #F5F7FA; border-radius: 8px; border-left: 4px solid #FF9800;">
        <div style="font-weight: 600; font-size: 14px; color: #4B535B;">Campo Anaco</div>
        <div style="color: #9FA6B4; font-size: 12px; margin-top: 4px;">Oriente</div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
            <span style="font-size: 12px; color: #4B535B;"><b>12</b> pozos</span>
            <span style="font-size: 12px; color: #4B535B;"><b>2</b> macollas</span>
            <span style="font-size: 12px; color: #9FA6B4;">GL, ESP, SRP</span>
        </div>
    </div>
</div>
```

**Ajustes del widget:**
- Widget title: `Resumen por Campo` (o desactivar y dejar el titulo dentro del HTML)
- Background: `#FFFFFF`

2. Hacer clic en **"Add"** y posicionar en col: 16, row: 8.

---

### 3.5 Widget: Filtros para la Tabla (Row 17)

Este widget permite al usuario activar/desactivar la visibilidad de pozos por tipo de levantamiento y por campo en la tabla inferior.

**Tipo de widget:** `system.input_widgets.update_multiple_attributes`

**Posicion y tamano:**
- col: 0, row: 17
- sizeX: 24, sizeY: 2

**Pasos:**
1. Agregar un nuevo widget. Buscar `Update multiple attributes` en el bundle **Input widgets**.
2. Seleccionar **"Update multiple attributes"** (typeFullFqn: `system.input_widgets.update_multiple_attributes`).

**Datasource:**
- Entity alias: `Usuario Actual`
- Data keys (todas de tipo **Attribute**, ambito **Server**):

> **Nota:** Estos atributos se guardan como `SERVER_SCOPE` en la entidad del usuario actual. Los valores NO son booleanos (`true`/`false`), sino strings que representan el tipo de levantamiento o campo (ej. `"esp"`, `"srp"`, `"campo_boscan"`). Cuando el toggle esta ON, el atributo contiene el string del tipo; cuando esta OFF, contiene `"unset"`. Esto es necesario porque el patron de Entity Filter usa la operacion CONTAINS para comparar el atributo `wellFilter` del pozo contra estos valores del usuario. Si se usaran booleanos (`true`/`false`), el filtro no funcionaria.

**Configuracion de cada Data Key:**

Para cada key, hacer clic en el icono del lapiz (editar) en la data key y configurar segun las tablas siguientes. Cada key requiere funciones **Get value** y **Set value** en la seccion Advanced para convertir entre el string almacenado y el toggle visual (boolean).

**Data Key 1: show_esp**

| Campo | Valor |
|---|---|
| Key | `show_esp` |
| Type | Attribute (Server scope) |
| Label | `ESP` |
| Data key value type | booleanSwitch |

Funciones avanzadas (Advanced):
- **Get value function body**:
  ```javascript
  return !value || value === 'esp';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'esp' : 'unset';
  ```

**Data Key 2: show_srp**

| Campo | Valor |
|---|---|
| Key | `show_srp` |
| Type | Attribute (Server scope) |
| Label | `SRP` |
| Data key value type | booleanSwitch |

- **Get value function body**:
  ```javascript
  return !value || value === 'srp';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'srp' : 'unset';
  ```

**Data Key 3: show_pcp**

| Campo | Valor |
|---|---|
| Key | `show_pcp` |
| Type | Attribute (Server scope) |
| Label | `PCP` |
| Data key value type | booleanSwitch |

- **Get value function body**:
  ```javascript
  return !value || value === 'pcp';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'pcp' : 'unset';
  ```

**Data Key 4: show_gaslift**

| Campo | Valor |
|---|---|
| Key | `show_gaslift` |
| Type | Attribute (Server scope) |
| Label | `Gas Lift` |
| Data key value type | booleanSwitch |

- **Get value function body**:
  ```javascript
  return !value || value === 'gaslift';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'gaslift' : 'unset';
  ```

**Data Key 5: show_campo_boscan**

| Campo | Valor |
|---|---|
| Key | `show_campo_boscan` |
| Type | Attribute (Server scope) |
| Label | `Boscan` |
| Data key value type | booleanSwitch |

- **Get value function body**:
  ```javascript
  return !value || value === 'campo_boscan';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'campo_boscan' : 'unset';
  ```

**Data Key 6: show_campo_cerronegro**

| Campo | Valor |
|---|---|
| Key | `show_campo_cerronegro` |
| Type | Attribute (Server scope) |
| Label | `Cerro Negro` |
| Data key value type | booleanSwitch |

- **Get value function body**:
  ```javascript
  return !value || value === 'campo_cerronegro';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'campo_cerronegro' : 'unset';
  ```

**Data Key 7: show_campo_anaco**

| Campo | Valor |
|---|---|
| Key | `show_campo_anaco` |
| Type | Attribute (Server scope) |
| Label | `Anaco` |
| Data key value type | booleanSwitch |

- **Get value function body**:
  ```javascript
  return !value || value === 'campo_anaco';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'campo_anaco' : 'unset';
  ```

**Configuracion avanzada del widget:**

En la pestaña **Appearance**, configurar:
- **Layout:** `Row` (para que los toggles se muestren horizontalmente)
- **Show group title:** Activar, titulo: `Filtros`

3. Hacer clic en **"Add"** y posicionar.

> **Importante:** Este widget de filtro funciona guardando atributos de tipo string en la entidad del usuario (SERVER_SCOPE). Para que la tabla de abajo responda a estos filtros, se debe configurar un **Entity Filter** en el dashboard que compare el atributo `wellFilter` de cada pozo contra los valores almacenados en los atributos del usuario, usando la operacion **CONTAINS** con **Dynamic value** desde **Current user**. Este es el mismo patron descrito en la Guia 01 (Campo Petrolero), seccion 3 "Filtros". El filtro se aplica al alias "Todos los Pozos" y cualquier widget que use ese alias se actualizara automaticamente cuando el usuario cambie los toggles. **No** usar Data post-processing function para esto, ya que el Entity Filter es mas eficiente y funciona de forma nativa con ThingsBoard.

---

### 3.6 Widget: Tabla Completa de Pozos (Row 19)

Esta es la tabla principal del dashboard. Muestra todos los pozos con sus principales metricas y permite drill-down al hacer clic en una fila.

**Tipo de widget:** `system.cards.entities_table` (Entities Table)

**Posicion y tamano:**
- col: 0, row: 19
- sizeX: 24, sizeY: 12

**Pasos:**
1. Agregar un nuevo widget. Buscar `Entities table` en el bundle **Cards**.
2. Seleccionar **"Entities table"** (typeFullFqn: `system.cards.entities_table`).

**Datasource:**
- Entity alias: `Todos los Pozos`

**Columnas (Data Keys):**

Agregar las siguientes data keys en este orden:

| # | Key | Type | Label | Sortable | Decimals | Notas |
|---|---|---|---|---|---|---|
| 1 | `entityName` | Entity field | `Pozo` | SI | - | Nombre del asset |
| 2 | `lift_type` | Attribute | `Tipo` | SI | - | esp, srp, pcp, gaslift |
| 3 | `field_name` | Attribute | `Campo` | SI | - | Nombre del campo |
| 4 | `macolla_name` | Attribute | `Macolla` | NO | - | Nombre de la macolla |
| 5 | `flow_rate_bpd` | Timeseries | `Produccion (BPD)` | SI | 1 | Caudal de produccion |
| 6 | `tubing_pressure_psi` | Timeseries | `Presion Tubing (PSI)` | SI | 1 | Presion en tuberia |
| 7 | `motor_current_a` | Timeseries | `Corriente (A)` | SI | 2 | Corriente del motor |
| 8 | `motor_power_kw` | Timeseries | `Potencia (kW)` | SI | 2 | Potencia del motor |
| 9 | `status` | Attribute | `Estado` | SI | - | producing, shut-in, etc. |
| 10 | `opt_well_health_score` | Attribute | `Salud` | SI | 0 | Score de salud (0-100) |

**Para agregar cada columna:**
1. Hacer clic en **"+ Add"** en la seccion de data keys.
2. Para keys tipo **Entity field**: seleccionar `entityName` del dropdown de entity fields.
3. Para keys tipo **Attribute**: escribir el nombre de la key y seleccionar `Attribute [Server]`.
4. Para keys tipo **Timeseries**: escribir el nombre y seleccionar `Timeseries`.
5. En la configuracion de cada key, establecer el **Label** como se indica en la tabla.

**Configuracion General del Widget (pestaña Appearance):**

```json
{
    "entitiesTitle": "Lista de Pozos",
    "enableSearch": true,
    "enableStickyHeader": true,
    "displayPagination": true,
    "defaultPageSize": 15,
    "enableSelection": false,
    "defaultSortOrder": "-flow_rate_bpd",
    "enableStickyAction": true
}
```

Esto se configura manualmente:
- **Title:** `Lista de Pozos`
- **Enable search:** Activar
- **Enable sticky header:** Activar
- **Display pagination:** Activar
- **Default page size:** `15`
- **Enable selection:** Desactivar
- **Default sort order:** `-flow_rate_bpd` (produccion descendente; el signo `-` indica orden descendente)

#### 3.6.1 Cell Style Function para la Columna "Estado"

1. En la lista de data keys, hacer clic en el icono de **lapiz** (editar) de la key `status`.
2. Buscar la seccion **"Cell style function"** (en la pestaña de tabla o en configuracion avanzada de la columna).
3. Activar "Use cell style function" y pegar:

```javascript
if (value === 'producing') {
    return {
        color: '#4CAF50',
        fontWeight: '600'
    };
} else if (value === 'shut-in') {
    return {
        color: '#F44336',
        fontWeight: '600'
    };
} else {
    return {
        color: '#FF9800',
        fontWeight: '600'
    };
}
```

#### 3.6.2 Cell Content Function para la Columna "Estado" (Badges)

Para mostrar badges con colores en lugar de texto plano:

1. En la misma configuracion de la key `status`, buscar **"Cell content function"**.
2. Activar "Use cell content function" y pegar:

```javascript
if (value === 'producing') {
    return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:#E8F5E9;color:#4CAF50;font-size:12px;font-weight:600;">Produciendo</div>';
} else if (value === 'shut-in') {
    return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:#FFEBEE;color:#F44336;font-size:12px;font-weight:600;">Cerrado</div>';
}
return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:#FFF3E0;color:#FF9800;font-size:12px;font-weight:600;">' + value + '</div>';
```

#### 3.6.3 Cell Style Function para la Columna "Produccion (BPD)"

1. Editar la key `flow_rate_bpd`.
2. Activar "Use cell style function" y pegar:

```javascript
var numVal = Number(value);
if (numVal > 500) {
    return {
        color: '#4CAF50',
        fontWeight: '600'
    };
} else if (numVal > 200) {
    return {
        color: '#FF9800'
    };
} else {
    return {
        color: '#F44336'
    };
}
```

#### 3.6.4 Cell Content Function para la Columna "Tipo" (Badges por tipo)

1. Editar la key `lift_type`.
2. Activar "Use cell content function" y pegar:

```javascript
var colors = {
    'esp': { bg: '#E8F5E9', text: '#4CAF50', label: 'ESP' },
    'srp': { bg: '#E3F2FD', text: '#2196F3', label: 'SRP' },
    'pcp': { bg: '#FFF3E0', text: '#FF9800', label: 'PCP' },
    'gaslift': { bg: '#F3E5F5', text: '#9C27B0', label: 'Gas Lift' }
};
var c = colors[value] || { bg: '#F5F5F5', text: '#757575', label: value };
return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:' + c.bg + ';color:' + c.text + ';font-size:12px;font-weight:600;">' + c.label + '</div>';
```

#### 3.6.5 Configurar Accion: Row Click para Drill-Down

Esta es la funcionalidad mas importante: al hacer clic en una fila de la tabla, se navega al estado de detalle de ese pozo.

1. En la configuracion del widget, ir a la pestaña **"Actions"**.
2. Hacer clic en **"Add action"** (boton "+").
3. Configurar:
   - **Action source:** `Row click` (o `On row click`)
   - **Name:** `Ver detalle del pozo`
   - **Icon:** `open_in_new` (o `visibility`)
   - **Type:** `Navigate to new dashboard state`
   - **Target dashboard state:** `pozo_detalle`
   - **Set entity from widget:** Activar (toggle ON). Esto pasa la entidad de la fila clickeada al estado de destino.

4. Hacer clic en **"Save"** para guardar la accion.

5. Hacer clic en **"Add"** para agregar el widget al dashboard.

---

## Paso 4: Estado de Detalle del Pozo (pozo_detalle)

Este estado muestra la informacion detallada de un pozo individual. Se accede desde la tabla principal al hacer clic en una fila.

### 4.1 Crear el Estado

1. En modo edicion del dashboard, hacer clic en el icono de **"Manage dashboard states"** en la barra superior (icono de capas o rectangulos superpuestos).
2. Hacer clic en **"+"** para agregar un nuevo estado.
3. Configurar:
   - **Name:** `Detalle del Pozo`
   - **Id:** `pozo_detalle`
   - **Root:** NO (dejar desactivado; solo el estado `default` es root)
4. Hacer clic en **"Add"**.
5. Seleccionar el estado `pozo_detalle` para editarlo (hacer clic en el tab o seleccionarlo del dropdown de estados).

### 4.2 Widget: Boton Volver + Header del Pozo (Row 0)

**Tipo de widget:** `system.cards.markdown_card`

**Posicion y tamano:**
- col: 0, row: 0
- sizeX: 24, sizeY: 2

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `entityName` (Entity field)
  - `lift_type` (Attribute)
  - `field_name` (Attribute)
  - `macolla_name` (Attribute)
  - `well_code_pdvsa` (Attribute)

**Contenido HTML:**

```html
<div style="display: flex; align-items: center; gap: 16px; padding: 8px 16px;">
    <div id="btn-back" onclick="window.history.back()"
         style="cursor: pointer; padding: 6px 16px; background: #305680; color: white; border-radius: 6px; font-weight: 500; font-size: 13px; white-space: nowrap; user-select: none;">
        &larr; Volver a Lista
    </div>
    <div style="flex: 1;">
        <span style="font-size: 22px; font-weight: 700; color: #305680;">${entityName}</span>
        <span style="margin-left: 12px; padding: 4px 12px; border-radius: 12px; background: #E8F5E9; color: #4CAF50; font-size: 12px; font-weight: 600;">${lift_type}</span>
    </div>
    <div style="display: flex; gap: 16px; font-size: 13px;">
        <div><span style="color: #9FA6B4;">Campo:</span> <b>${field_name}</b></div>
        <div><span style="color: #9FA6B4;">Macolla:</span> <b>${macolla_name}</b></div>
        <div><span style="color: #9FA6B4;">Codigo PDVSA:</span> <b>${well_code_pdvsa}</b></div>
    </div>
</div>
```

> **Nota sobre el boton "Volver":** El atributo `onclick="window.history.back()"` funciona para navegacion basica. Alternativamente, se puede configurar una **accion del widget** para una navegacion mas robusta:

**Configurar accion del boton Volver (metodo alternativo):**
1. En la configuracion del widget, ir a pestaña **"Actions"**.
2. Agregar accion:
   - **Action source:** `Widget header button` o `On HTML element click`
   - **Name:** `Volver`
   - **Type:** `Navigate to new dashboard state`
   - **Target dashboard state:** `default`
3. Si se usa "On HTML element click", el ID del elemento HTML es `btn-back`.

**Ajustes:**
- Show widget title: NO
- Background: `#FFFFFF`

---

### 4.3 Widgets: KPI Cards del Pozo (Row 3)

Crear 6 tarjetas de KPI para el pozo seleccionado. Cada una muestra un valor clave con mini-grafico.

**Tipo de widget:** `system.cards.aggregated_value_card`

**Posicion:** Row 3. Cada tarjeta sizeX: 4, sizeY: 3. Se colocan secuencialmente: col 0, 4, 8, 12, 16, 20.

**Datasource comun:** Entity alias `Pozo Seleccionado`

| # | col | Data Key | Label | Units | Color |
|---|---|---|---|---|---|
| 1 | 0 | `flow_rate_bpd` | `Produccion` | `BPD` | `#305680` |
| 2 | 4 | `tubing_pressure_psi` | `Presion Tubing` | `PSI` | `#4CAF50` |
| 3 | 8 | `casing_pressure_psi` | `Presion Casing` | `PSI` | `#2196F3` |
| 4 | 12 | `motor_current_a` | `Corriente Motor` | `A` | `#FF9800` |
| 5 | 16 | `motor_power_kw` | `Potencia Motor` | `kW` | `#9C27B0` |
| 6 | 20 | Variable segun tipo (ver abajo) | Variable | Variable | `#607D8B` |

**Tarjeta 6 - Variable por tipo de levantamiento:**

La sexta tarjeta muestra un parametro especifico del tipo de levantamiento:
- **ESP:** `motor_temperature_f` (Label: "Temp. Motor", Units: "F")
- **SRP:** `pump_fillage_pct` (Label: "Llenado Bomba", Units: "%")
- **PCP:** `speed_rpm` (Label: "Velocidad", Units: "RPM")
- **Gas Lift:** `gl_injection_rate_mscfd` (Label: "Inyeccion Gas", Units: "MSCFD")

**Opcion A - Crear 4 widgets con condiciones de visibilidad:**

Se crean 4 widgets en la misma posicion (col: 20, row: 3) y se usa **Widget visibility condition** para mostrar solo el correcto:

Para cada widget, en la pestaña **"Advanced"** buscar **"Widget visibility"** y activar **"Use widget visibility condition"**. Pegar la funcion correspondiente:

**Para ESP:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'esp';
```

**Para SRP:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'srp';
```

**Para PCP:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'pcp';
```

**Para Gas Lift:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'gaslift';
```

**Opcion B - Un solo widget generico:**

Si no se desean crear 4 widgets, se puede crear un solo widget con el data key `motor_temperature_f` y simplemente dejarlo vacio para los tipos que no lo emitan.

---

### 4.4 Widget: Grafico de Produccion del Pozo (Row 7, izquierda)

**Tipo de widget:** `system.time_series_chart`

**Posicion y tamano:**
- col: 0, row: 7
- sizeX: 12, sizeY: 8

**Datasource:**
- Entity alias: `Pozo Seleccionado`
- Data keys:
  - `flow_rate_bpd` (timeseries, color: `#305680`, label: "Produccion BPD")
  - `water_cut_pct` (timeseries, color: `#42A5F5`, label: "Corte de Agua %")

**Configuracion del Chart:**

- **Title:** `Historico de Produccion`
- **Show legend:** SI, posicion: bottom

Configurar dos ejes Y:
- **Eje izquierdo:** Label "Produccion (BPD)" - para `flow_rate_bpd`
- **Eje derecho:** Label "Corte de Agua (%)" - para `water_cut_pct`

Para configurar doble eje Y:
1. En la configuracion de la serie `water_cut_pct`, buscar **"Y axis"** y seleccionar un eje secundario a la derecha.
2. O en la seccion de ejes del chart, agregar un segundo eje Y con posicion "right".

---

### 4.5 Widget: Grafico Especifico por Tipo (Row 7, derecha)

**Tipo de widget:** `system.time_series_chart`

**Posicion y tamano:**
- col: 12, row: 7
- sizeX: 12, sizeY: 8

Se crean **4 versiones** de este widget (una por tipo de levantamiento) en la misma posicion, usando **widget visibility conditions** para mostrar solo el correcto.

#### Grafico ESP (visibilidad: `lift_type === 'esp'`)

**Datasource:** Entity alias `Pozo Seleccionado`

| Data Key | Label | Color |
|---|---|---|
| `motor_temperature_f` | Temp. Motor (F) | `#F44336` |
| `motor_current_a` | Corriente (A) | `#FF9800` |
| `vibration_ips` | Vibracion (IPS) | `#9C27B0` |
| `vsd_frequency_hz` | Frecuencia VSD (Hz) | `#4CAF50` |

**Title:** `Parametros ESP`

**Widget visibility condition:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'esp';
```

#### Grafico SRP (visibilidad: `lift_type === 'srp'`)

| Data Key | Label | Color |
|---|---|---|
| `polished_rod_load_max_lb` | Carga Max (lb) | `#F44336` |
| `spm` | SPM | `#2196F3` |
| `pump_fillage_pct` | Llenado (%) | `#4CAF50` |
| `fluid_level_ft` | Nivel Fluido (ft) | `#FF9800` |

**Title:** `Parametros SRP`

**Widget visibility condition:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'srp';
```

#### Grafico PCP (visibilidad: `lift_type === 'pcp'`)

| Data Key | Label | Color |
|---|---|---|
| `drive_rpm` | RPM | `#2196F3` |
| `drive_torque_ftlb` | Torque (ft-lb) | `#F44336` |
| `motor_current_a` | Corriente (A) | `#FF9800` |
| `sand_pct` | Arena (%) | `#795548` |

**Title:** `Parametros PCP`

**Widget visibility condition:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'pcp';
```

#### Grafico Gas Lift (visibilidad: `lift_type === 'gaslift'`)

| Data Key | Label | Color |
|---|---|---|
| `gl_injection_rate_mscfd` | Inyeccion (MSCFD) | `#9C27B0` |
| `gl_injection_pressure_psi` | Presion Iny. (PSI) | `#F44336` |
| `thp_psi` | THP (PSI) | `#4CAF50` |
| `chp_psi` | CHP (PSI) | `#2196F3` |

**Title:** `Parametros Gas Lift`

**Widget visibility condition:**
```javascript
return entity && entity.attributes && entity.attributes.lift_type === 'gaslift';
```

---

### 4.6 Widget: Datos Tecnicos de Completacion (Row 16, izquierda)

**Tipo de widget:** `system.cards.entities_table`

**Posicion y tamano:**
- col: 0, row: 16
- sizeX: 12, sizeY: 8

**Datasource:**
- Entity alias: `Pozo Seleccionado`

**Columnas (Data Keys):**

| Key | Type | Label |
|---|---|---|
| `total_depth_md_ft` | Attribute | Profundidad MD (ft) |
| `total_depth_tvd_ft` | Attribute | Profundidad TVD (ft) |
| `pump_depth_ft` | Attribute | Prof. Bomba (ft) |
| `perforations_top_ft` | Attribute | Perf. Tope (ft) |
| `perforations_bottom_ft` | Attribute | Perf. Base (ft) |
| `casing_od_in` | Attribute | Casing OD (in) |
| `casing_id_in` | Attribute | Casing ID (in) |
| `tubing_od_in` | Attribute | Tubing OD (in) |
| `tubing_id_in` | Attribute | Tubing ID (in) |
| `completion_type` | Attribute | Tipo Completacion |

**Configuracion:**
- **Title:** `Datos de Completacion`
- **Display pagination:** NO (son pocos datos)
- **Enable search:** NO

---

### 4.7 Widget: Datos de Reservorio (Row 16, derecha)

**Tipo de widget:** `system.cards.entities_table`

**Posicion y tamano:**
- col: 12, row: 16
- sizeX: 12, sizeY: 8

**Datasource:**
- Entity alias: `Pozo Seleccionado`

**Columnas (Data Keys):**

| Key | Type | Label |
|---|---|---|
| `reservoir_pressure_psi` | Attribute | Presion Reservorio (PSI) |
| `reservoir_temperature_f` | Attribute | Temp. Reservorio (F) |
| `bubble_point_psi` | Attribute | Punto Burbuja (PSI) |
| `api_gravity` | Attribute | Gravedad API |
| `gor_scf_stb` | Attribute | GOR (SCF/STB) |
| `water_cut_initial_pct` | Attribute | Corte Agua Inicial (%) |
| `oil_viscosity_cp` | Attribute | Viscosidad (cp) |
| `productivity_index_bpd_psi` | Attribute | Indice Productividad (BPD/PSI) |
| `ipr_model` | Attribute | Modelo IPR |
| `drive_mechanism` | Attribute | Mecanismo de Empuje |

**Configuracion:**
- **Title:** `Datos de Reservorio`
- **Display pagination:** NO
- **Enable search:** NO

---

## Paso 5: Configurar Navegacion entre Estados

### 5.1 Verificar Navegacion de Tabla a Detalle

La navegacion principal ya fue configurada en el Paso 3.6.5 (accion Row Click en la tabla). Verificar que funciona:

1. Salir del modo edicion (clic en el icono de check/guardar).
2. En la tabla de pozos, hacer clic en cualquier fila.
3. El dashboard debe navegar al estado `pozo_detalle` mostrando los datos del pozo seleccionado.
4. La URL del navegador cambiara a algo como: `...?state=pozo_detalle&entityId=<uuid>&entityType=ASSET`

### 5.2 Verificar Boton Volver

1. Estando en el estado `pozo_detalle`, hacer clic en el boton "Volver a Lista".
2. El dashboard debe regresar al estado `default` con la tabla completa.

### 5.3 Navegacion por URL

ThingsBoard permite navegar directamente a un pozo via URL. La estructura es:

```
http://144.126.150.120:8080/dashboard/<dashboard-id>?state=pozo_detalle&entityId=<entity-uuid>&entityType=ASSET
```

Esto es util para compartir enlaces directos a un pozo especifico.

### 5.4 Configuracion del Entity State Controller

El Entity State Controller (configurado en Paso 1.2) permite que la barra superior del dashboard muestre un selector de entidad. Esto permite al usuario:

1. Navegar entre pozos usando el dropdown de la barra superior.
2. Buscar pozos por nombre en el selector.
3. La URL se actualiza automaticamente con el entityId seleccionado.

---

## Tips de Diseno y Referencia Rapida

### Paleta de Colores del Sistema

| Elemento | Color | Hex |
|---|---|---|
| Color primario (titulos, acciones) | Azul oscuro | `#305680` |
| ESP | Verde | `#4CAF50` |
| SRP | Azul | `#2196F3` |
| PCP | Naranja | `#FF9800` |
| Gas Lift | Purpura | `#9C27B0` |
| Texto principal | Gris oscuro | `#4B535B` |
| Texto secundario | Gris claro | `#9FA6B4` |
| Fondo tarjetas info | Gris muy claro | `#F5F7FA` |
| Exito / Produciendo | Verde | `#4CAF50` |
| Advertencia | Naranja | `#FF9800` |
| Error / Cerrado | Rojo | `#F44336` |

### Referencia de TypeFullFqn de Widgets

Siempre usar el nombre completo `typeFullFqn` al buscar widgets:

| Widget | typeFullFqn |
|---|---|
| HTML/Markdown Card | `system.cards.markdown_card` |
| Aggregated Value Card | `system.cards.aggregated_value_card` |
| Entities Table | `system.cards.entities_table` |
| Time Series Chart | `system.time_series_chart` |
| Update Multiple Attributes | `system.input_widgets.update_multiple_attributes` |

### Widget Visibility Condition - Sintaxis

Para que un widget solo sea visible cuando el pozo es de un tipo especifico:

```javascript
// En configuracion del widget -> Advanced -> Widget visibility condition
return entity && entity.attributes && entity.attributes.lift_type === 'esp';
```

Reemplazar `'esp'` con `'srp'`, `'pcp'`, o `'gaslift'` segun corresponda.

### Cell Content Function - Badge de Estado

Funcion completa para crear badges de colores en columnas de tabla:

```javascript
// Columna "status" -> Cell content function
if (value === 'producing') {
    return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:#E8F5E9;color:#4CAF50;font-size:12px;font-weight:600;">Produciendo</div>';
} else if (value === 'shut-in') {
    return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:#FFEBEE;color:#F44336;font-size:12px;font-weight:600;">Cerrado</div>';
}
return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:#FFF3E0;color:#FF9800;font-size:12px;font-weight:600;">' + value + '</div>';
```

### Cell Style Function - Colores por Rango de Produccion

```javascript
// Columna "flow_rate_bpd" -> Cell style function
var numVal = Number(value);
if (numVal > 500) {
    return { color: '#4CAF50', fontWeight: '600' };
} else if (numVal > 200) {
    return { color: '#FF9800' };
} else {
    return { color: '#F44336' };
}
```

### Cell Content Function - Badge de Tipo de Levantamiento

```javascript
// Columna "lift_type" -> Cell content function
var colors = {
    'esp': { bg: '#E8F5E9', text: '#4CAF50', label: 'ESP' },
    'srp': { bg: '#E3F2FD', text: '#2196F3', label: 'SRP' },
    'pcp': { bg: '#FFF3E0', text: '#FF9800', label: 'PCP' },
    'gaslift': { bg: '#F3E5F5', text: '#9C27B0', label: 'Gas Lift' }
};
var c = colors[value] || { bg: '#F5F5F5', text: '#757575', label: value };
return '<div style="display:inline-block;padding:2px 8px;border-radius:12px;background:' + c.bg + ';color:' + c.text + ';font-size:12px;font-weight:600;">' + c.label + '</div>';
```

### Claves de Telemetria por Tipo de Levantamiento

**Comunes a todos los tipos:**

| Clave | Descripcion | Unidad |
|---|---|---|
| `flow_rate_bpd` | Caudal de produccion | BPD |
| `water_cut_pct` | Corte de agua | % |
| `tubing_pressure_psi` | Presion en cabezal tubing | PSI |
| `casing_pressure_psi` | Presion en cabezal casing | PSI |

**Especificas de ESP:**

| Clave | Descripcion | Unidad |
|---|---|---|
| `motor_temperature_f` | Temperatura del motor | F |
| `motor_current_a` | Corriente del motor | A |
| `motor_voltage_v` | Voltaje del motor | V |
| `motor_power_kw` | Potencia del motor | kW |
| `vsd_frequency_hz` | Frecuencia del VSD | Hz |
| `vibration_ips` | Vibracion (max X/Y) | IPS |
| `vibration_x_ips` | Vibracion eje X | IPS |
| `vibration_y_ips` | Vibracion eje Y | IPS |
| `intake_pressure_psi` | Presion de succion | PSI |
| `discharge_pressure_psi` | Presion de descarga | PSI |
| `pump_efficiency_pct` | Eficiencia de la bomba | % |
| `insulation_mohm` | Resistencia de aislamiento | MOhm |

**Especificas de SRP:**

| Clave | Descripcion | Unidad |
|---|---|---|
| `motor_current_a` | Corriente del motor | A |
| `motor_power_kw` | Potencia del motor | kW |
| `spm` | Golpes por minuto | SPM |
| `polished_rod_load_max_lb` | Carga max varilla pulida | lb |
| `polished_rod_load_min_lb` | Carga min varilla pulida | lb |
| `load_lb` | Carga (alias de max) | lb |
| `fluid_level_ft` | Nivel de fluido | ft |
| `pump_fillage_pct` | Porcentaje de llenado | % |
| `pump_efficiency_pct` | Eficiencia de la bomba | % |
| `stroke_counter` | Contador de golpes | - |

**Especificas de PCP:**

| Clave | Descripcion | Unidad |
|---|---|---|
| `motor_current_a` | Corriente del motor | A |
| `motor_power_kw` | Potencia del motor | kW |
| `drive_rpm` | RPM del drive | RPM |
| `speed_rpm` | RPM (alias) | RPM |
| `drive_torque_ftlb` | Torque del drive | ft-lb |
| `motor_torque_ftlb` | Torque (alias) | ft-lb |
| `intake_pressure_psi` | Presion de succion | PSI |
| `sand_pct` | Porcentaje de arena | % |
| `pump_efficiency_pct` | Eficiencia de la bomba | % |

**Especificas de Gas Lift:**

| Clave | Descripcion | Unidad |
|---|---|---|
| `gl_injection_rate_mscfd` | Tasa de inyeccion de gas | MSCFD |
| `gl_injection_pressure_psi` | Presion de inyeccion | PSI |
| `thp_psi` | Presion cabezal tubing | PSI |
| `chp_psi` | Presion cabezal casing | PSI |
| `tht_f` | Temperatura cabezal | F |
| `gor_scf_stb` | Relacion gas-aceite (total) | SCF/STB |
| `choke_size_64ths` | Tamano del choke | 64avos |

> **Nota sobre Gas Lift:** Este tipo no genera las claves alias `tubing_pressure_psi` ni `casing_pressure_psi`. Usa directamente `thp_psi` y `chp_psi`. Tener esto en cuenta al configurar columnas de tabla que combinen todos los tipos.

### Atributos Estaticos (Server Attributes)

**Comunes a todos los pozos:**

| Atributo | Descripcion |
|---|---|
| `well_name` | Nombre del pozo |
| `well_code_pdvsa` | Codigo PDVSA del pozo |
| `field_name` | Nombre del campo |
| `macolla_name` | Nombre de la macolla |
| `lift_type` | Tipo de levantamiento (esp, srp, pcp, gaslift) |
| `status` | Estado (producing, shut-in) |
| `total_depth_md_ft` | Profundidad total MD |
| `total_depth_tvd_ft` | Profundidad total TVD |
| `pump_depth_ft` | Profundidad de la bomba |
| `casing_od_in` / `casing_id_in` | Diametros del casing |
| `tubing_od_in` / `tubing_id_in` | Diametros del tubing |
| `perforations_top_ft` / `perforations_bottom_ft` | Intervalo perforado |
| `completion_type` | Tipo de completacion |
| `reservoir_pressure_psi` | Presion inicial del reservorio |
| `reservoir_temperature_f` | Temperatura del reservorio |
| `bubble_point_psi` | Punto de burbuja |
| `api_gravity` | Gravedad API del crudo |
| `productivity_index_bpd_psi` | Indice de productividad |
| `ipr_model` | Modelo IPR (vogel o darcy) |
| `drive_mechanism` | Mecanismo de empuje |
| `opt_well_health_score` | Score de salud del pozo (0-100) |

### Resolucion de Problemas Comunes

**1. La tabla no muestra datos:**
- Verificar que el alias `Todos los Pozos` esta configurado correctamente con Asset type = `well`.
- Verificar que "Resolve as multiple entities" esta activado.
- Verificar que los pozos existen como Assets en ThingsBoard (ir a Entities -> Assets y buscar).

**2. Los graficos muestran "No data":**
- Verificar el rango de tiempo del dashboard (timewindow). Si los datos son historicos, ampliar el rango.
- Verificar que las claves de telemetria existen. Ir a un Asset individual -> Latest telemetry y verificar los nombres de las claves.

**3. Las condiciones de visibilidad no funcionan:**
- Asegurarse de que `lift_type` esta como **Server Attribute** en la entidad.
- La funcion debe retornar `true` o `false`.
- Verificar que se accede correctamente: `entity.attributes.lift_type`.

**4. El drill-down no navega al detalle:**
- Verificar que la accion "Row click" esta configurada con "Set entity from widget" activado.
- Verificar que el estado `pozo_detalle` existe con id exacto `pozo_detalle`.
- Verificar que el alias `Pozo Seleccionado` usa "Entity from dashboard state".

**5. El boton "Volver" no funciona:**
- Si se usa `window.history.back()`, asegurarse de que la navegacion no fue directa por URL.
- Es preferible configurar una accion del widget con "Navigate to new dashboard state" -> `default`.

**6. Gas Lift no muestra presion tubing/casing en la tabla:**
- El modelo Gas Lift usa `thp_psi` y `chp_psi` directamente sin crear los alias `tubing_pressure_psi` / `casing_pressure_psi`.
- Solucion: Agregar ambas claves (`tubing_pressure_psi` y `thp_psi`) como columnas, o modificar la regla de ThingsBoard para crear los alias.

---

### Diagrama Visual: Estado de Detalle (pozo_detalle)

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║              DASHBOARD: KPIs y Produccion — Estado Detalle (pozo_detalle)                ║
║              Grid: 24 columnas | Widgets: 10+ | Rows totales: ~24                        ║
║              Acceso: Click en fila de tabla del estado default                            ║
╠══════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                          ║
║  ROW 0-1  (sizeY: 2, header con boton volver)                                           ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐    ║
║  │ [<- Volver a Lista]  BOS-E01  [ESP]  │  Campo: Boscan  │  Macolla: Mac-B1      │    ║
║  │                                       │  Codigo PDVSA: BOS-E-001               │    ║
║  └──────────────────────────────────────────────────────────────────────────────────┘    ║
║   col:0 sizeX:24  sizeY:2                                                               ║
║   Widget: system.cards.markdown_card                                                     ║
║   Alias: Pozo Seleccionado                                                               ║
║   Keys: entityName, lift_type, field_name, macolla_name, well_code_pdvsa                 ║
║                                                                                          ║
║  ROW 3-5  (sizeY: 3, 6 tarjetas KPI individuales)                                       ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         ║
║  │Produccion│ │ Presion  │ │ Presion  │ │Corriente │ │ Potencia │ │ Variable │         ║
║  │          │ │  Tubing  │ │  Casing  │ │  Motor   │ │  Motor   │ │ x Tipo   │         ║
║  │  542.3   │ │  1,250   │ │    380   │ │   32.1   │ │   18.7   │ │  185.4   │         ║
║  │   BPD    │ │   PSI    │ │   PSI    │ │    A     │ │    kW    │ │   F/RPM  │         ║
║  │  ~~~     │ │  ~~~     │ │  ~~~     │ │  ~~~     │ │  ~~~     │ │  ~~~     │         ║
║  │ #305680  │ │ #4CAF50  │ │ #2196F3  │ │ #FF9800  │ │ #9C27B0  │ │ #607D8B  │         ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         ║
║   col:0        col:4        col:8        col:12       col:16       col:20               ║
║   sizeX:4      sizeX:4      sizeX:4      sizeX:4      sizeX:4      sizeX:4              ║
║   Widget: system.cards.aggregated_value_card  (Alias: Pozo Seleccionado)                 ║
║   Nota: Tarjeta 6 es variable por tipo (ESP: Temp Motor, SRP: Llenado,                  ║
║         PCP: Velocidad RPM, GL: Inyeccion Gas). Usa widget visibility conditions.        ║
║                                                                                          ║
║  ROW 7-14  (sizeY: 8, graficos lado a lado)                                             ║
║  ┌──────────────────────────────────┐ ┌──────────────────────────────────┐               ║
║  │  Produccion y Corte de Agua     │ │  Parametros ESP/SRP/PCP/GL      │               ║
║  │                                  │ │  (segun lift_type del pozo)     │               ║
║  │  BPD         % Agua              │ │                                  │               ║
║  │  800┤╲               ┌──  20%    │ │  F/A                             │               ║
║  │  600┤ ╲    ╱‾╲      ╱    15%    │ │  200┤                    ──Temp  │               ║
║  │  400┤  ╲──╱   ╲    ╱     10%    │ │  150┤  ─╱‾╲──           --Amp   │               ║
║  │  200┤          ╲──╱       5%    │ │  100┤ ╱    ╲────╲──     --Vib   │               ║
║  │    0┼──┬──┬──┬──┬──       0%    │ │   50┤╱                   --VSD   │               ║
║  │      E  F  M  A  M              │ │    0┼──┬──┬──┬──┬──              │               ║
║  │  [Produccion BPD] [Corte Agua]  │ │  [Temp] [Corriente] [Vib] [VSD] │               ║
║  └──────────────────────────────────┘ └──────────────────────────────────┘               ║
║   col:0 sizeX:12  sizeY:8             col:12 sizeX:12  sizeY:8                          ║
║   Widget: system.time_series_chart     Widget: system.time_series_chart                  ║
║   Alias: Pozo Seleccionado             Alias: Pozo Seleccionado                          ║
║   Keys: flow_rate_bpd, water_cut_pct   Keys: Varian segun lift_type                     ║
║                                         ESP: motor_temperature_f, motor_current_a,       ║
║                                              vibration_ips, vsd_frequency_hz             ║
║                                         SRP: polished_rod_load_max_lb, spm,              ║
║                                              pump_fillage_pct, fluid_level_ft            ║
║                                         PCP: drive_rpm, drive_torque_ftlb,               ║
║                                              motor_current_a, sand_pct                   ║
║                                         GL:  gl_injection_rate_mscfd,                    ║
║                                              gl_injection_pressure_psi, thp, chp         ║
║                                         (4 widgets superpuestos con visibility cond.)    ║
║                                                                                          ║
║  ROW 16-23  (sizeY: 8, tablas de datos tecnicos)                                        ║
║  ┌──────────────────────────────────┐ ┌──────────────────────────────────┐               ║
║  │  Datos de Completacion           │ │  Datos de Reservorio             │               ║
║  ├────────────────────┬─────────────┤ ├────────────────────┬─────────────┤               ║
║  │  Parametro         │    Valor    │ │  Parametro         │    Valor    │               ║
║  ├────────────────────┼─────────────┤ ├────────────────────┼─────────────┤               ║
║  │  Profundidad MD    │  8,500 ft   │ │  Presion Reserv.   │  2,850 PSI  │               ║
║  │  Profundidad TVD   │  7,200 ft   │ │  Temp. Reserv.     │    185 F    │               ║
║  │  Prof. Bomba       │  6,800 ft   │ │  Punto Burbuja     │  1,200 PSI  │               ║
║  │  Perf. Tope        │  7,000 ft   │ │  Gravedad API      │    22.5     │               ║
║  │  Perf. Base        │  7,150 ft   │ │  GOR               │  350 SCF/STB│               ║
║  │  Casing OD         │  7.000 in   │ │  Corte Agua Ini.   │    15.0 %   │               ║
║  │  Casing ID         │  6.366 in   │ │  Viscosidad        │   8.5 cp    │               ║
║  │  Tubing OD         │  2.875 in   │ │  Indice Product.   │ 1.2 BPD/PSI │               ║
║  │  Tubing ID         │  2.441 in   │ │  Modelo IPR        │   Vogel     │               ║
║  │  Tipo Completacion │  Simple     │ │  Mec. de Empuje    │ Gas en sol. │               ║
║  └────────────────────┴─────────────┘ └────────────────────┴─────────────┘               ║
║   col:0 sizeX:12  sizeY:8             col:12 sizeX:12  sizeY:8                          ║
║   Widget: system.cards.entities_table  Widget: system.cards.entities_table                ║
║   Alias: Pozo Seleccionado             Alias: Pozo Seleccionado                          ║
║   10 atributos de completacion         10 atributos de reservorio                        ║
║   Sin paginacion | Sin busqueda        Sin paginacion | Sin busqueda                     ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝

RESUMEN DE POSICIONES - Estado pozo_detalle:
 Widget                          | col | row | sizeX | sizeY | Alias
 --------------------------------|-----|-----|-------|-------|---------------------------
 Header + Boton Volver (HTML)    |  0  |  0  |  24   |   2   | Pozo Seleccionado
 KPI: Produccion                 |  0  |  3  |   4   |   3   | Pozo Seleccionado
 KPI: Presion Tubing             |  4  |  3  |   4   |   3   | Pozo Seleccionado
 KPI: Presion Casing             |  8  |  3  |   4   |   3   | Pozo Seleccionado
 KPI: Corriente Motor            | 12  |  3  |   4   |   3   | Pozo Seleccionado
 KPI: Potencia Motor             | 16  |  3  |   4   |   3   | Pozo Seleccionado
 KPI: Variable x Tipo (x4)      | 20  |  3  |   4   |   3   | Pozo Seleccionado
 Grafico Produccion + Agua       |  0  |  7  |  12   |   8   | Pozo Seleccionado
 Grafico Parametros x Tipo (x4)  | 12  |  7  |  12   |   8   | Pozo Seleccionado
 Tabla Datos Completacion        |  0  | 16  |  12   |   8   | Pozo Seleccionado
 Tabla Datos Reservorio          | 12  | 16  |  12   |   8   | Pozo Seleccionado
```

---

## Resumen del Dashboard

Al completar esta guia, el dashboard **"Atilax - KPIs y Produccion"** contendra:

**Estado Principal (default):**
1. Banner con titulo y contadores de pozos/campos/macollas
2. 4 tarjetas KPI con produccion sumada por tipo de levantamiento (ESP, SRP, PCP, Gas Lift)
3. Grafico de series de tiempo con produccion total y desglose por tipo
4. Panel de resumen por campo (Boscan, Cerro Negro, Anaco)
5. Barra de filtros con toggles por tipo y por campo
6. Tabla completa de 63 pozos con badges de color, ordenamiento y busqueda

**Estado Detalle (pozo_detalle):**
1. Header con nombre del pozo, tipo, campo, macolla y codigo PDVSA
2. 6 tarjetas KPI con metricas principales del pozo individual
3. Grafico de produccion historica con corte de agua
4. Grafico especifico del tipo de levantamiento (parametros ESP/SRP/PCP/Gas Lift)
5. Tabla de datos de completacion
6. Tabla de datos de reservorio

**Navegacion:**
- Click en fila de tabla -> Detalle del pozo
- Boton "Volver" -> Lista completa
- Entity selector en barra superior -> Navegacion directa

---

*Guia creada para el proyecto Atilax Simulador de Pozos - ThingsBoard PE v4.3*
