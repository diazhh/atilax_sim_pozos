# Guia Paso a Paso: Dashboard "Campo Petrolero" en ThingsBoard PE v4.3

## Descripcion General

Este documento describe como crear manualmente un dashboard de tipo **Mapa de Campo Petrolero** en ThingsBoard Professional Edition v4.3. El dashboard presenta:

- Un **mapa interactivo** (OpenStreetMap) con los pozos geolocalizados y marcadores de color segun tipo de levantamiento.
- **Filtros dinamicos** (toggle switches) para mostrar/ocultar pozos por tipo: ESP, SRP, PCP, Gas Lift.
- **KPIs agregados** en la parte superior (total pozos, produccion total, presion promedio, corriente promedio).
- **Tabla lateral** con lista de pozos y datos clave.
- **Vista de detalle** (drill-down) al hacer clic en un pozo, con graficos especificos segun el tipo de levantamiento.

El patron de diseno esta inspirado en las plantillas oficiales de ThingsBoard **Mine Site Monitoring** (`3e6b43b0-0547-11f1-8dfb-fb2fc7314bd7`) y **Fuel Level Monitoring** (`53591540-0547-11f1-8dfb-fb2fc7314bd7`).

---

## Indice

1. [Prerequisito: Agregar Coordenadas GPS](#prerequisito-agregar-coordenadas-gps)
2. [Paso 1: Crear el Dashboard y Configurar Settings](#paso-1-crear-el-dashboard-y-configurar-settings)
3. [Paso 2: Crear Entity Aliases](#paso-2-crear-entity-aliases)
4. [Paso 3: Crear Filtros Dinamicos](#paso-3-crear-filtros-dinamicos)
5. [Paso 4: Estado Principal - Vista General](#paso-4-estado-principal---vista-general)
6. [Paso 5: Estado de Detalle - Vista del Pozo](#paso-5-estado-de-detalle---vista-del-pozo)
7. [Paso 6: Navegacion entre Estados](#paso-6-navegacion-entre-estados)
8. [Tips y Mejores Practicas](#tips-y-mejores-practicas)

---

## Prerequisito: Agregar Coordenadas GPS

> **CRITICO**: Actualmente no existen atributos de ubicacion (`latitude`, `longitude`) en ninguna entidad de tipo `well`. Sin estos atributos el widget de mapa no podra posicionar los marcadores. Es **obligatorio** agregar estos atributos antes de continuar.

### Que se necesita

Cada pozo (entidad tipo `ASSET`, subtipo `well`) debe tener dos atributos de ambito **SERVER_SCOPE**:

| Atributo    | Tipo   | Ejemplo     | Descripcion                     |
|-------------|--------|-------------|---------------------------------|
| `latitude`  | number | 9.9123      | Latitud decimal (Norte positivo)|
| `longitude` | number | -71.8045    | Longitud decimal (Oeste negativo)|

### Coordenadas base por campo

| Campo       | Region               | Latitud Base | Longitud Base |
|-------------|----------------------|--------------|---------------|
| Boscan      | Lago de Maracaibo    | 9.90         | -71.80        |
| Cerro Negro | Faja del Orinoco     | 8.50         | -63.50        |
| Anaco       | Oriente              | 9.40         | -64.50        |

### Script Python para agregar coordenadas via API

Ejecutar este script una sola vez. Asigna coordenadas base segun el campo del pozo, con un desplazamiento aleatorio para que los pozos no se superpongan en el mapa.

```python
import requests
import random

# ── Configuracion ──────────────────────────────────────────────
TB_URL   = "http://144.126.150.120:8080"
USERNAME = "well@atilax.io"
PASSWORD = "10203040"

# ── Login ──────────────────────────────────────────────────────
r = requests.post(
    f"{TB_URL}/api/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)
r.raise_for_status()
token = r.json()["token"]
headers = {"X-Authorization": f"Bearer {token}"}

# ── Coordenadas base por campo ─────────────────────────────────
COORDS = {
    "Boscan":     (9.90,  -71.80),
    "Cerro Negro": (8.50, -63.50),
    "Anaco":      (9.40,  -64.50),
}

# ── Obtener todos los pozos ────────────────────────────────────
resp = requests.get(
    f"{TB_URL}/api/tenant/assets?pageSize=100&page=0&type=well",
    headers=headers
)
resp.raise_for_status()
wells = resp.json()["data"]
print(f"Pozos encontrados: {len(wells)}")

# ── Asignar coordenadas ───────────────────────────────────────
for w in wells:
    wid = w["id"]["id"]
    wname = w["name"]

    # Leer atributos actuales para determinar el campo
    attrs_resp = requests.get(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE",
        headers=headers
    )
    attrs_resp.raise_for_status()
    attrs = attrs_resp.json()

    field_name = ""
    for a in attrs:
        if a["key"] == "field_name":
            field_name = a["value"]
            break

    # Determinar coordenadas base
    base_lat, base_lon = COORDS.get("Anaco")  # default
    for key, (blat, blon) in COORDS.items():
        if key.lower() in field_name.lower():
            base_lat, base_lon = blat, blon
            break

    # Agregar desplazamiento aleatorio (aprox 0-5 km en cada direccion)
    lat = base_lat + random.uniform(-0.05, 0.05)
    lon = base_lon + random.uniform(-0.05, 0.05)

    # Escribir atributos
    post_resp = requests.post(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/attributes/SERVER_SCOPE",
        headers=headers,
        json={"latitude": round(lat, 6), "longitude": round(lon, 6)}
    )
    post_resp.raise_for_status()
    print(f"  [OK] {wname}: lat={lat:.6f}, lon={lon:.6f} (campo: {field_name})")

print("\nCoordenas asignadas exitosamente a todos los pozos.")
```

### Agregar atributo `wellFilter` (necesario para el paso 3)

Ademas de las coordenadas, cada pozo necesita un atributo `wellFilter` que contenga su tipo de levantamiento en minusculas. Este atributo es usado por el sistema de filtros del dashboard.

```python
# ── Continuacion del script anterior ──────────────────────────
# (usar el mismo token y headers)

for w in wells:
    wid = w["id"]["id"]
    wname = w["name"]

    # Leer lift_type del pozo
    attrs_resp = requests.get(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE",
        headers=headers
    )
    attrs = attrs_resp.json()

    lift_type = ""
    for a in attrs:
        if a["key"] == "lift_type":
            lift_type = a["value"]
            break

    # Mapear a valor de filtro
    filter_map = {
        "ESP": "esp",
        "SRP": "srp",
        "PCP": "pcp",
        "Gas Lift": "gaslift",
        "GasLift": "gaslift",
    }
    well_filter = filter_map.get(lift_type, lift_type.lower().replace(" ", ""))

    requests.post(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/attributes/SERVER_SCOPE",
        headers=headers,
        json={"wellFilter": well_filter}
    )
    print(f"  [OK] {wname}: wellFilter = {well_filter}")

print("\nAtributo wellFilter asignado a todos los pozos.")
```

### Verificacion

Para verificar que los atributos se asignaron correctamente, ir a **Entities > Assets**, seleccionar cualquier pozo, pestaña **Attributes**, ambito **Server attributes**. Deben aparecer `latitude`, `longitude` y `wellFilter`.

---

## Paso 1: Crear el Dashboard y Configurar Settings

### 1.1 Crear el dashboard

1. En el menu lateral izquierdo, ir a **Dashboards**.
2. Hacer clic en el boton **"+"** (esquina inferior derecha).
3. Seleccionar **"Create new dashboard"**.
4. Rellenar:
   - **Title**: `Atilax - Mapa de Campo`
   - **Description** (opcional): `Dashboard principal de campo petrolero con mapa interactivo y vista de detalle por pozo`
5. Hacer clic en **"Add"**.

### 1.2 Abrir el dashboard en modo edicion

1. Hacer clic en el dashboard recien creado para abrirlo.
2. Hacer clic en el **icono de lapiz** (esquina inferior derecha) para entrar en modo edicion.

### 1.3 Configurar Settings generales

1. Hacer clic en el **icono de engranaje** (gear) en la barra de herramientas superior derecha.
2. En el panel de **Dashboard settings** que se abre, configurar:

| Campo                          | Valor                          |
|--------------------------------|--------------------------------|
| Dashboard title                | `Atilax - Mapa de Campo`      |
| State controller               | `Entity`                       |
| Show entity selector           | **Activado (ON)**              |
| Show dashboard timewindow      | **Activado (ON)**              |
| Toolbar always open            | **Activado (ON)**              |

3. **NO cerrar todavia** -- hay que agregar el CSS personalizado.

### 1.4 Agregar CSS personalizado

En el mismo panel de Settings, buscar el campo **"Dashboard CSS"** (puede estar en una seccion expandible llamada "Advanced" o directamente visible). Pegar el siguiente bloque CSS completo:

```css
.tb-widget-container > .tb-widget {
    border-radius: 8px;
    box-shadow: 0px 2px 8px rgba(222, 223, 224, 0.25);
}

.tb-dashboard-page .tb-widget-container > .tb-widget {
    color: #4B535B !important;
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

.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-in,
.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-out {
    color: #4B535B;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-in {
    border-radius: 6px 6px 0 0;
    border-bottom: 1px solid transparent;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-control-zoom-out {
    border-radius: 0 0 6px 6px;
}

.tb-dashboard-page .tb-widget-container > .tb-widget .leaflet-popup a.tb-custom-action {
    font-family: 'Roboto';
    font-weight: 500;
    font-size: 14px;
    line-height: 20px;
    letter-spacing: 0.25px;
    border-bottom: none;
    color: #305680;
}

/* Estilo personalizado para tarjetas KPI */
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #305680;
}

.kpi-label {
    font-size: 12px;
    color: #9FA6B4;
    text-transform: uppercase;
}
```

4. Hacer clic en **"Save"** o **"Apply"** para guardar la configuracion.

> **Nota**: Este CSS aplica bordes redondeados a todos los widgets, mejora la tipografia de las tablas, estiliza los controles del mapa y define clases auxiliares para las tarjetas KPI.

---

## Paso 2: Crear Entity Aliases

Los Entity Aliases son la base de todo el dashboard. Definen **de donde provienen los datos** que consumen los widgets. Se configuran una sola vez y luego se reutilizan en multiples widgets.

### 2.1 Abrir el editor de Entity Aliases

1. Estando en modo edicion del dashboard, hacer clic en el icono **"Entity aliases"** en la barra de herramientas (icono con forma de etiqueta/tag, usualmente al lado del icono de filtros).
2. Se abre el panel **"Entity aliases"**.

### 2.2 Alias: "Todos los Pozos"

Este alias devuelve **todos** los pozos del tenant. Es el alias principal para el mapa y las tablas.

1. Hacer clic en **"Add alias"**.
2. Configurar:

| Campo                      | Valor                    |
|----------------------------|--------------------------|
| Alias name                 | `Todos los Pozos`        |
| Filter type                | **Asset type**           |
| Asset type                 | `well`                   |
| Resolve as multiple entities | **Activado (checked)**  |

3. Hacer clic en **"Add"**.

### 2.3 Alias: "Usuario Actual"

Este alias apunta al usuario que esta viendo el dashboard. Se usa para almacenar y leer los atributos de filtro (los toggles de tipo de pozo).

1. Hacer clic en **"Add alias"**.
2. Configurar:

| Campo                      | Valor                    |
|----------------------------|--------------------------|
| Alias name                 | `Usuario Actual`         |
| Filter type                | **Single entity**        |
| Type                       | **Current User**         |

3. Hacer clic en **"Add"**.

### 2.4 Alias: "Pozo Seleccionado"

Este alias resuelve al pozo que el usuario selecciona al hacer clic en el mapa o en la tabla. Se usa en el estado de detalle (well_detail).

1. Hacer clic en **"Add alias"**.
2. Configurar:

| Campo                      | Valor                           |
|----------------------------|---------------------------------|
| Alias name                 | `Pozo Seleccionado`             |
| Filter type                | **Entity from dashboard state** |

3. Hacer clic en **"Add"**.

> **Nota**: Este tipo de alias toma su valor del estado actual del dashboard. Cuando un widget ejecuta la accion "openDashboardState" con `setEntityId: true`, el ID de la entidad seleccionada se pasa al estado destino y este alias lo resuelve automaticamente.

### 2.5 Alias: "Pozos del Campo" (opcional)

Este alias es util si mas adelante se desea crear una vista intermedia a nivel de campo o macolla. Devuelve los pozos que estan relacionados con la entidad actualmente seleccionada (campo o macolla) mediante relacion "Contains".

1. Hacer clic en **"Add alias"**.
2. Configurar:

| Campo                      | Valor                           |
|----------------------------|---------------------------------|
| Alias name                 | `Pozos del Campo`               |
| Filter type                | **Relations query**             |
| Root entity                | **From dashboard state**        |
| Direction                  | **From**                        |
| Max relation level         | `2`                             |
| Relation type              | `Contains`                      |
| Entity types               | **ASSET**                       |
| Asset types                | `well`                          |

3. Hacer clic en **"Add"**.

### 2.6 Guardar los aliases

Hacer clic en **"Save"** en el panel de Entity Aliases. Ahora deben aparecer 4 aliases (o 3 si se omitio el opcional):

- Todos los Pozos
- Usuario Actual
- Pozo Seleccionado
- Pozos del Campo (opcional)

---

## Paso 3: Crear Filtros Dinamicos

El sistema de filtros permite al usuario mostrar u ocultar pozos en el mapa y la tabla segun el tipo de levantamiento (ESP, SRP, PCP, Gas Lift) usando toggle switches.

### 3.1 Como funciona el patron de filtros

El mecanismo es el siguiente:

1. Cada **pozo** tiene un atributo `wellFilter` con su tipo en minusculas (`"esp"`, `"srp"`, `"pcp"`, `"gaslift"`).
2. El **usuario actual** tiene atributos booleanos/string (`show_esp`, `show_srp`, etc.) que se guardan como SERVER_SCOPE en la entidad del usuario.
3. Un **Entity Filter** en ThingsBoard compara el `wellFilter` del pozo contra los valores almacenados en los atributos del usuario.
4. Un widget de **toggle switches** permite al usuario modificar estos atributos en tiempo real.
5. Cuando un toggle cambia, el filtro se reevalua y los widgets que usan el alias filtrado se actualizan automaticamente.

### 3.2 Crear el filtro en el dashboard

1. Estando en modo edicion, hacer clic en el icono **"Filters"** en la barra de herramientas (icono con forma de embudo, al lado del icono de Entity Aliases).
2. Hacer clic en **"Add filter"**.
3. Configurar:

| Campo       | Valor                |
|-------------|----------------------|
| Filter name | `Filtro de Pozos`    |

4. En la seccion de **Key filters**, hacer clic en **"Add key filter"**.
5. Configurar el primer filtro de clave:

| Campo         | Valor                |
|---------------|----------------------|
| Key           | `wellFilter`         |
| Key type      | **Attribute**        |
| Value type    | **String**           |

6. En **Predicates**, se necesita configurar una operacion **OR** con 4 condiciones. Cada condicion usa un **Dynamic value** que lee del usuario actual.

#### Predicado 1: ESP

| Campo                        | Valor                         |
|------------------------------|-------------------------------|
| Operation                    | **CONTAINS**                  |
| Value                        | (dejar vacio)                 |
| Dynamic value                | **Activado**                  |
| Source type                  | **Current user**              |
| Source attribute             | `show_esp`                    |
| Inherit from owner/hierarchy | No                            |

#### Predicado 2: SRP

| Campo                        | Valor                         |
|------------------------------|-------------------------------|
| Operation                    | **CONTAINS**                  |
| Dynamic value                | **Activado**                  |
| Source type                  | **Current user**              |
| Source attribute             | `show_srp`                    |

#### Predicado 3: PCP

| Campo                        | Valor                         |
|------------------------------|-------------------------------|
| Operation                    | **CONTAINS**                  |
| Dynamic value                | **Activado**                  |
| Source type                  | **Current user**              |
| Source attribute             | `show_pcp`                    |

#### Predicado 4: Gas Lift

| Campo                        | Valor                         |
|------------------------------|-------------------------------|
| Operation                    | **CONTAINS**                  |
| Dynamic value                | **Activado**                  |
| Source type                  | **Current user**              |
| Source attribute             | `show_gaslift`                |

7. Asegurarse de que la **operacion logica entre predicados** sea **OR** (cualquiera de los tipos activados se muestra).

8. Hacer clic en **"Add"** y luego **"Save"**.

### 3.3 Aplicar el filtro al alias "Todos los Pozos"

1. Volver a **Entity Aliases**.
2. Editar el alias **"Todos los Pozos"**.
3. En la seccion **"Filters"**, seleccionar **"Filtro de Pozos"** del dropdown.
4. Guardar.

Ahora cualquier widget que use el alias "Todos los Pozos" respetara el filtro automaticamente.

### 3.4 Inicializar atributos del usuario

Para que los filtros funcionen desde la primera carga, el usuario necesita tener los atributos `show_esp`, `show_srp`, `show_pcp` y `show_gaslift` con valores iniciales.

Se pueden agregar manualmente:
1. Ir a **Users** en el menu lateral.
2. Seleccionar el usuario (`well@atilax.io`).
3. Ir a la pestaña **Attributes**, ambito **Server attributes**.
4. Agregar cada atributo manualmente:

| Key           | Type   | Value   |
|---------------|--------|---------|
| `show_esp`    | String | `esp`   |
| `show_srp`    | String | `srp`   |
| `show_pcp`    | String | `pcp`   |
| `show_gaslift`| String | `gaslift` |

O ejecutar via API:

```python
import requests

TB_URL   = "http://144.126.150.120:8080"
r = requests.post(f"{TB_URL}/api/auth/login",
                   json={"username": "well@atilax.io", "password": "10203040"})
token = r.json()["token"]
headers = {"X-Authorization": f"Bearer {token}"}

# Obtener ID del usuario actual
user_resp = requests.get(f"{TB_URL}/api/auth/user", headers=headers)
user_id = user_resp.json()["id"]["id"]

# Inicializar filtros (todos activos)
requests.post(
    f"{TB_URL}/api/plugins/telemetry/USER/{user_id}/attributes/SERVER_SCOPE",
    headers=headers,
    json={
        "show_esp": "esp",
        "show_srp": "srp",
        "show_pcp": "pcp",
        "show_gaslift": "gaslift"
    }
)
print("Filtros inicializados para el usuario.")
```

---

## Paso 4: Estado Principal - Vista General

Este es el estado `default` del dashboard, el que se muestra al abrirlo. Contiene la barra de filtros, los KPIs, el mapa y la tabla de pozos.

### Layout general

Se usa un **grid de 24 columnas**. A continuacion se muestra como deberia verse el estado principal al finalizar:

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                           DASHBOARD: CAMPO PETROLERO — Estado Principal                     ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────┐  ║
║  │ ☐ ESP (18)    ☐ SRP (20)    ☐ PCP (16)    ☐ Gas Lift (9)                              │  ║
║  │ [toggle ON]   [toggle ON]   [toggle ON]    [toggle ON]         ← Filtros de tipo       │  ║
║  └────────────────────────────────────────────────────────────────────────────────────────┘  ║
║   Row 0-1 | sizeX: 24 | update_multiple_attributes | Alias: Usuario Actual                  ║
║                                                                                              ║
║  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                    ║
║  │ ■ Pozos       │ │ ▲ Produccion  │ │ ◆ Presion     │ │ ★ Corriente   │                    ║
║  │  Activos      │ │  Total        │ │  Promedio     │ │  Promedio     │                    ║
║  │               │ │               │ │               │ │               │                    ║
║  │    58         │ │  32,450 BPD   │ │  185 PSI      │ │  42.3 A       │                    ║
║  │  ▴ +3 hoy    │ │  ▾ -2.1%      │ │  ▴ +5 PSI     │ │  → estable    │                    ║
║  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘                    ║
║   Row 2-4 | 4x sizeX: 6 | aggregated_value_card | Alias: Todos los Pozos                   ║
║                                                                                              ║
║  ┌────────────────────────────────────────────────┐ ┌──────────────────────────────────────┐ ║
║  │                                                │ │ Nombre       │ Tipo  │ BPD   │ Estado│ ║
║  │          MAPA OPENSTREETMAP                    │ │──────────────┼───────┼───────┼───────│ ║
║  │                                                │ │ BOS-M1-P01   │ ● ESP │ 850   │ Prod. │ ║
║  │    ● BOS-M1-P01 (ESP)                         │ │ BOS-M1-P03   │ ● SRP │ 320   │ Prod. │ ║
║  │         ● BOS-M1-P03 (SRP)                    │ │ NEG-M1-P01   │ ● PCP │ 450   │ Prod. │ ║
║  │    ◆ BOS-M2-P08 (PCP)                         │ │ ANA-M1-P02   │ ● GL  │ 580   │ Prod. │ ║
║  │              ★ ANA-M1-P02 (GL)                │ │ BOS-M2-P08   │ ● PCP │ 280   │ Shut  │ ║
║  │                                                │ │ ...          │ ...   │ ...   │ ...   │ ║
║  │    [Click en marcador → well_detail]           │ │                                      │ ║
║  │                                                │ │ [Click en fila → well_detail]        │ ║
║  │   🟢 ESP  🔵 SRP  🟠 PCP  🟣 Gas Lift        │ │ Busqueda: [___________]  Pag: 1/7   │ ║
║  └────────────────────────────────────────────────┘ └──────────────────────────────────────┘ ║
║   Row 6-17 | Mapa: sizeX: 16 | map | Tabla: sizeX: 8 | entities_table                     ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

### 4.1 Widget: Barra de Filtros

**Posicion**: fila 0, columna 0, sizeX: 24, sizeY: 1.5 (aproximadamente)

#### Agregar el widget

1. En modo edicion, hacer clic en **"Add new widget"** (icono "+").
2. Buscar el widget: **Input widgets > Update Multiple Attributes**
   - Tipo completo: `system.input_widgets.update_multiple_attributes`
3. Hacer clic para agregarlo.

#### Configurar Datasource

1. En la configuracion del widget, ir a la pestaña **"Data"** (o "Datasource").
2. Configurar:

| Campo           | Valor                |
|-----------------|----------------------|
| Type            | **Entity**           |
| Entity alias    | `Usuario Actual`     |

3. Agregar las siguientes **Data Keys** (todas de tipo **Attribute**, ambito **Server**):

**Data Key 1: show_esp**

| Campo               | Valor                    |
|----------------------|--------------------------|
| Key                  | `show_esp`               |
| Type                 | Attribute                |
| Label                | `ESP`                    |
| Data key value type  | booleanSwitch            |
| Color                | `#4CAF50` (verde)        |

En la seccion de funciones avanzadas (Advanced):
- **Get value function body**:
  ```javascript
  return !value || value === 'esp';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'esp' : 'unset';
  ```

**Data Key 2: show_srp**

| Campo               | Valor                    |
|----------------------|--------------------------|
| Key                  | `show_srp`               |
| Type                 | Attribute                |
| Label                | `SRP`                    |
| Data key value type  | booleanSwitch            |
| Color                | `#2196F3` (azul)         |

- **Get value function body**:
  ```javascript
  return !value || value === 'srp';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'srp' : 'unset';
  ```

**Data Key 3: show_pcp**

| Campo               | Valor                    |
|----------------------|--------------------------|
| Key                  | `show_pcp`               |
| Type                 | Attribute                |
| Label                | `PCP`                    |
| Data key value type  | booleanSwitch            |
| Color                | `#FF9800` (naranja)      |

- **Get value function body**:
  ```javascript
  return !value || value === 'pcp';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'pcp' : 'unset';
  ```

**Data Key 4: show_gaslift**

| Campo               | Valor                    |
|----------------------|--------------------------|
| Key                  | `show_gaslift`           |
| Type                 | Attribute                |
| Label                | `Gas Lift`               |
| Data key value type  | booleanSwitch            |
| Color                | `#9C27B0` (morado)       |

- **Get value function body**:
  ```javascript
  return !value || value === 'gaslift';
  ```
- **Set value function body**:
  ```javascript
  return value ? 'gaslift' : 'unset';
  ```

#### Configurar Settings del widget

Ir a la pestaña **"Settings"** (o "Widget settings") y configurar:

```json
{
    "showResultMessage": false,
    "showActionButtons": false,
    "showGroupTitle": false,
    "fieldsAlignment": "row",
    "rowGap": 10,
    "fieldsInRow": 4,
    "columnGap": 16
}
```

En la interfaz esto se traduce a:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Show result message    | **Desactivado (OFF)**    |
| Show action buttons    | **Desactivado (OFF)**    |
| Show group title       | **Desactivado (OFF)**    |
| Fields alignment       | **Row (horizontal)**     |
| Row gap                | `10`                     |
| Fields in row          | `4`                      |
| Column gap             | `16`                     |

#### Configurar apariencia

En la pestaña **"Appearance"**:
- Title: `Filtros por Tipo de Pozo` (o dejarlo vacio)
- Show title: depende de preferencia
- Background color: `#FFFFFF`
- Padding: `8px 16px`

4. Hacer clic en **"Save"** para guardar el widget.

### 4.2 Widgets: KPI Cards (4 tarjetas)

Las tarjetas KPI muestran metricas agregadas de todos los pozos visibles. Cada una ocupa 6 columnas de ancho.

**Posicion**: fila 2, columnas 0/6/12/18, sizeX: 6, sizeY: 3

#### KPI 1: Total Pozos Activos

1. Agregar nuevo widget.
2. Buscar: **Cards > Aggregated value card**
   - Tipo completo: `system.cards.aggregated_value_card`
3. Configurar datasource:

| Campo           | Valor                |
|-----------------|----------------------|
| Entity alias    | `Todos los Pozos`    |
| Data key        | `entityName`         |
| Key type        | **Entity field**     |
| Aggregation     | **COUNT**            |

> **NOTA IMPORTANTE**: Usamos `entityName` (Entity field) con COUNT en lugar de `flow_rate_bpd` (Timeseries) porque COUNT sobre telemetria cuenta **puntos de datos en el timewindow**, no entidades. Con 63 pozos enviando datos cada 30 segundos en un timewindow de 1 hora, COUNT sobre Timeseries devolveria miles de puntos, no 63. Al usar `entityName` (Entity field), COUNT cuenta las entidades que coinciden con el alias, devolviendo el numero correcto de pozos.

4. Settings:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Title                  | `Pozos Activos`          |
| Subtitle               | `Total con datos`        |
| Value font size        | `36`                     |
| Value color            | `#305680`                |
| Background color       | `#F5F7FA`                |
| Decimals               | `0`                      |
| Units                  | (vacio)                  |

5. Posicionar: row 2, col 0, sizeX: 6, sizeY: 3.

#### KPI 2: Produccion Total

1. Agregar widget `system.cards.aggregated_value_card`.
2. Datasource:

| Campo               | Valor                    |
|---------------------|--------------------------|
| Entity alias        | `Todos los Pozos`        |
| Data source type    | **Latest telemetry**     |
| Data key            | `flow_rate_bpd`          |
| Key type            | Timeseries               |
| Aggregation         | **SUM**                  |

> **NOTA IMPORTANTE**: Es critico seleccionar **"Latest telemetry"** como tipo de datasource. Si se usa el modo "Timeseries" con un timewindow, SUM sumara TODOS los puntos de datos del rango temporal, resultando en valores de millones en lugar de los ~90,000 BPD reales. Con "Latest telemetry", SUM agrega unicamente el valor mas reciente de cada uno de los 63 pozos, produciendo el total correcto de produccion del campo.

3. Settings:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Title                  | `Produccion Total`       |
| Units                  | `BPD`                    |
| Decimals               | `0`                      |
| Value color            | `#4CAF50`                |
| Background color       | `#F5F7FA`                |

4. Si el widget soporta **mini chart** (grafico en miniatura), activarlo para mostrar la tendencia de produccion.
5. Posicionar: row 2, col 6, sizeX: 6, sizeY: 3.

#### KPI 3: Presion Promedio Tubing

1. Agregar widget `system.cards.aggregated_value_card`.
2. Datasource:

| Campo               | Valor                    |
|---------------------|--------------------------|
| Entity alias        | `Todos los Pozos`        |
| Data source type    | **Latest telemetry**     |
| Data key            | `tubing_pressure_psi`    |
| Key type            | Timeseries               |
| Aggregation         | **AVG**                  |

> **NOTA**: Usar **"Latest telemetry"** como tipo de datasource para que AVG calcule el promedio de los valores mas recientes de cada pozo (uno por entidad). Si se usa el modo "Timeseries" con un timewindow, AVG promediaria todos los puntos de datos del rango temporal: aunque el resultado numerico puede ser similar, conceptualmente es incorrecto ya que mezcla valores historicos en lugar de mostrar el estado actual del campo.

3. Settings:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Title                  | `Presion Tubing Prom.`   |
| Units                  | `PSI`                    |
| Decimals               | `1`                      |
| Value color            | `#305680`                |
| Background color       | `#F5F7FA`                |

4. Posicionar: row 2, col 12, sizeX: 6, sizeY: 3.

#### KPI 4: Corriente Promedio Motor

1. Agregar widget `system.cards.aggregated_value_card`.
2. Datasource:

| Campo               | Valor                    |
|---------------------|--------------------------|
| Entity alias        | `Todos los Pozos`        |
| Data source type    | **Latest telemetry**     |
| Data key            | `motor_current_a`        |
| Key type            | Timeseries               |
| Aggregation         | **AVG**                  |

> **NOTA**: Usar **"Latest telemetry"** como tipo de datasource para que AVG calcule el promedio de los valores mas recientes de cada pozo (uno por entidad). Si se usa el modo "Timeseries" con un timewindow, AVG promediaria todos los puntos de datos del rango temporal: aunque el resultado numerico puede ser similar, conceptualmente es incorrecto ya que mezcla valores historicos en lugar de mostrar el estado actual del campo.

3. Settings:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Title                  | `Corriente Motor Prom.`  |
| Units                  | `A`                      |
| Decimals               | `1`                      |
| Value color            | `#305680`                |
| Background color       | `#F5F7FA`                |

4. Posicionar: row 2, col 18, sizeX: 6, sizeY: 3.

### 4.3 Widget: Mapa de Pozos

Este es el widget central del dashboard. Muestra todos los pozos en un mapa OpenStreetMap con marcadores de color segun tipo de levantamiento.

**Posicion**: fila 6, columna 0, sizeX: 16, sizeY: 12

#### Agregar el widget

1. Agregar nuevo widget.
2. Buscar: **Maps > OpenStreetMap**
   - Tipo completo: `system.map` con proveedor OpenStreetMap
3. Seleccionar **"OpenStreetMap"** como proveedor de mapa.

#### Configurar Datasource

| Campo           | Valor                |
|-----------------|----------------------|
| Entity alias    | `Todos los Pozos`    |
| Filter          | `Filtro de Pozos`    |

Data keys a agregar:

| Key                | Type        | Label             |
|--------------------|-------------|-------------------|
| `latitude`         | Attribute   | Latitud           |
| `longitude`        | Attribute   | Longitud          |
| `flow_rate_bpd`    | Timeseries  | Produccion        |
| `lift_type`        | Attribute   | Tipo              |
| `status`           | Attribute   | Estado            |

#### Configurar Map Settings

En la pestaña **"Settings"** del widget de mapa, configurar:

**Configuracion general del mapa:**

| Campo                          | Valor                |
|--------------------------------|----------------------|
| Map provider                   | `openstreet`         |
| Fit map bounds                 | **Activado (ON)**    |
| Default zoom level             | `8`                  |
| Use default center position    | **Desactivado (OFF)**|
| Latitude field key             | `latitude`           |
| Longitude field key            | `longitude`          |

**Configuracion de tooltip (informacion emergente):**

| Campo           | Valor        |
|-----------------|--------------|
| Show tooltip    | **Activado** |

En el campo **Tooltip pattern**, pegar:

```html
<div style='padding: 8px;'>
    <b style='font-size:14px; color:#305680;'>${entityName}</b>
    <br/>
    <span style='color:#9FA6B4; font-size:11px;'>Tipo:</span>
    <b>${lift_type}</b>
    <br/>
    <span style='color:#9FA6B4; font-size:11px;'>Produccion:</span>
    <b>${flow_rate_bpd} BPD</b>
    <br/>
    <span style='color:#9FA6B4; font-size:11px;'>Estado:</span>
    <b>${status}</b>
</div>
```

**Configuracion de marcadores (marker image):**

| Campo                          | Valor             |
|--------------------------------|-------------------|
| Use marker image function      | **Activado (ON)** |

En el campo **Marker image function**, pegar:

```javascript
var type = dsData[dsIndex]['lift_type'];
var colors = {
    'esp': '#4CAF50',
    'srp': '#2196F3',
    'pcp': '#FF9800',
    'gaslift': '#9C27B0'
};
var color = colors[type] || '#607D8B';
return {
    url: images[0],
    size: 34,
    color: color
};
```

> **Nota**: La funcion `images[0]` usa la imagen de marcador por defecto de ThingsBoard. El parametro `color` aplica un tinte de color. Si la funcion no produce el resultado esperado, se puede usar `markerColor` en lugar de esta funcion personalizada.

**Configuracion de etiquetas (labels):**

| Campo                          | Valor             |
|--------------------------------|-------------------|
| Use label function             | **Activado (ON)** |

En el campo **Label function**:

```javascript
return dsData[dsIndex]['entityName'];
```

| Campo           | Valor        |
|-----------------|--------------|
| Label color     | `#305680`    |
| Label font size | `11`         |

**Configuracion de zoom:**

| Campo              | Valor             |
|--------------------|-------------------|
| Scroll zoom        | **Activado**      |
| Double click zoom  | **Activado**      |
| Control buttons    | **Activado**      |

#### Configurar accion al hacer clic en marcador

Esta es la accion que permite navegar al detalle del pozo. Es **fundamental** para la funcionalidad de drill-down.

1. En la configuracion del widget, ir a la pestaña **"Actions"**.
2. Hacer clic en **"Add action"**.
3. Configurar:

| Campo                    | Valor                           |
|--------------------------|---------------------------------|
| Action source            | **Marker click** (o "On marker click") |
| Name                     | `Ver Detalle del Pozo`          |
| Icon                     | `info` (o cualquier icono)      |
| Action type              | **Navigate to new dashboard state** |
| Target dashboard state   | `well_detail`                   |
| Set entity from widget   | **Activado (checked)**          |

> **Importante**: El estado `well_detail` aun no existe. Se creara en el Paso 5. ThingsBoard permite referenciarlo antes de crearlo. Si da error, escribir el nombre manualmente en el campo.

4. Hacer clic en **"Add"** y luego **"Save"**.

### 4.4 Widget: Tabla de Pozos

La tabla complementa el mapa mostrando los datos de los pozos en formato tabular con busqueda y paginacion.

**Posicion**: fila 6, columna 16, sizeX: 8, sizeY: 12

#### Agregar el widget

1. Agregar nuevo widget.
2. Buscar: **Cards > Entities table**
   - Tipo completo: `system.cards.entities_table`

#### Configurar Datasource

| Campo           | Valor                |
|-----------------|----------------------|
| Entity alias    | `Todos los Pozos`    |
| Filter          | `Filtro de Pozos`    |

Columnas (Data keys):

| Key                | Type          | Label              |
|--------------------|---------------|--------------------|
| `entityName`       | Entity field  | `Pozo`             |
| `lift_type`        | Attribute     | `Tipo`             |
| `field_name`       | Attribute     | `Campo`            |
| `flow_rate_bpd`    | Timeseries    | `Produccion (BPD)` |
| `status`           | Attribute     | `Estado`           |

#### Configurar Settings de la tabla

| Campo                  | Valor                      |
|------------------------|----------------------------|
| Enable search          | **Activado (ON)**          |
| Enable sticky header   | **Activado (ON)**          |
| Display pagination     | **Activado (ON)**          |
| Default page size      | `10`                       |
| Enable selection       | **Desactivado (OFF)**      |
| Default sort order     | `-flow_rate_bpd` (descendente) |

> **Nota**: El signo `-` delante del nombre de la columna indica orden descendente (mayor produccion primero).

#### Configurar accion al hacer clic en fila

1. Ir a la pestaña **"Actions"** del widget.
2. Hacer clic en **"Add action"**.
3. Configurar:

| Campo                    | Valor                           |
|--------------------------|---------------------------------|
| Action source            | **Row click** (o "On row click") |
| Name                     | `Ver Detalle`                   |
| Action type              | **Navigate to new dashboard state** |
| Target dashboard state   | `well_detail`                   |
| Set entity from widget   | **Activado (checked)**          |

4. Guardar.

### 4.5 Guardar el estado principal

Hacer clic en el boton **"Save"** (icono de disco/check) en la barra inferior del dashboard para guardar todos los cambios del estado principal.

---

## Paso 5: Estado de Detalle - Vista del Pozo (well_detail)

Este estado se muestra cuando el usuario hace clic en un pozo desde el mapa o la tabla. Presenta informacion detallada del pozo individual, con graficos que varian segun el tipo de levantamiento.

### 5.1 Crear el estado well_detail

1. Estando en modo edicion, hacer clic en el icono **"Manage dashboard states"** (icono con capas/layers en la barra de herramientas).
2. Se abre el panel **"Dashboard states"**. Debe verse el estado `default` ya existente.
3. Hacer clic en **"+"** para agregar un nuevo estado.
4. Configurar:

| Campo     | Valor                           |
|-----------|---------------------------------|
| Name      | `Vista del Pozo`                |
| ID        | `well_detail`                   |
| Root      | **Desactivado (NO es root)**    |

5. Hacer clic en **"Add"** y luego **"Save"**.
6. Ahora en el selector de estados (dropdown en la barra superior del dashboard) se puede cambiar entre `default` y `well_detail`. Seleccionar **`well_detail`** para comenzar a agregar widgets a este estado.

### Layout del estado well_detail

Asi deberia verse el estado de detalle de un pozo individual:

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                           DASHBOARD: CAMPO PETROLERO — Estado well_detail                   ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║  ┌──────────┐ ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ ← Volver │ │  BOS-M1-P01  |  Tipo: ESP  |  Campo: Boscan  |  Macolla: MAC-BOS-01    │  ║
║  │ al Mapa  │ │  Estado: ● Produciendo     |  Profundidad: 8,500 ft                    │  ║
║  └──────────┘ └──────────────────────────────────────────────────────────────────────────┘  ║
║   Row 0-1 | Boton: sizeX:4 | Header: sizeX:20 | markdown_card | Alias: Pozo Seleccionado  ║
║                                                                                              ║
║  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      ║
║  │ Produccion│ │ Corte Agua│ │ Presion   │ │ Temp.     │ │ GOR       │ │ Frecuencia│      ║
║  │  850 BPD  │ │  32.5 %   │ │  185 PSI  │ │  245 °F   │ │  380 SCF  │ │  55 Hz    │      ║
║  │  ▴ mini   │ │  ▴ mini   │ │  ▴ mini   │ │  ▴ mini   │ │  ▴ mini   │ │ (solo ESP)│      ║
║  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘      ║
║   Row 2-4 | 6x sizeX: 4 | aggregated_value_card | KPI6 cambia segun lift_type             ║
║                                                                                              ║
║  ┌──────────────────────────────────────────┐ ┌──────────────────────────────────────────┐  ║
║  │ PRODUCCION HISTORICA                     │ │ PARAMETROS ESP (visible si lift_type=ESP) │  ║
║  │ ┌────────────────────────────────────┐   │ │ ┌────────────────────────────────────┐   │  ║
║  │ │  900│                              │   │ │ │  60│      ╱╲                       │   │  ║
║  │ │     │  ╱╲    ╱╲                    │   │ │ │    │     ╱  ╲   ╱╲                 │   │  ║
║  │ │  600│ ╱  ╲  ╱  ╲   ╱╲             │   │ │ │  40│    ╱    ╲ ╱  ╲                │   │  ║
║  │ │     │╱    ╲╱    ╲  ╱ ╲────         │   │ │ │    │───╱      ╲    ╲───            │   │  ║
║  │ │  300│              ╲╱              │   │ │ │  20│  ╱                             │   │  ║
║  │ │     ├──────────────────────────    │   │ │ │    ├──────────────────────────      │   │  ║
║  │ │     Ene  Feb  Mar  Abr  May  Jun   │   │ │ │    — Temp Motor  — Corriente       │   │  ║
║  │ └────────────────────────────────────┘   │ │ └────────────────────────────────────┘   │  ║
║  │  — flow_rate_bpd                         │ │  — motor_temp_f  — motor_current_a      │  ║
║  └──────────────────────────────────────────┘ └──────────────────────────────────────────┘  ║
║   Row 6-13 | Produccion: sizeX:12 | time_series_chart | Tipo: sizeX:12 + visibility cond   ║
║                                                                                              ║
║  ┌──────────────────────────────────────────┐ ┌──────────────────────────────────────────┐  ║
║  │ DATOS MECANICOS                          │ │ DATOS DEL RESERVORIO                     │  ║
║  │ ┌──────────────┬────────────────────┐    │ │ ┌──────────────────┬──────────────────┐  │  ║
║  │ │ Atributo     │ Valor              │    │ │ │ Atributo         │ Valor            │  │  ║
║  │ ├──────────────┼────────────────────┤    │ │ ├──────────────────┼──────────────────┤  │  ║
║  │ │ pump_model   │ DN1750             │    │ │ │ reservoir_pr_psi │ 2,800 psi        │  │  ║
║  │ │ num_stages   │ 180                │    │ │ │ temperature_f    │ 245 °F           │  │  ║
║  │ │ motor_hp     │ 150 HP             │    │ │ │ api_gravity      │ 10.5 °API        │  │  ║
║  │ │ cable_length │ 8,200 ft           │    │ │ │ bubble_point_psi │ 1,500 psi        │  │  ║
║  │ └──────────────┴────────────────────┘    │ │ └──────────────────┴──────────────────┘  │  ║
║  └──────────────────────────────────────────┘ └──────────────────────────────────────────┘  ║
║   Row 14-19 | sizeX: 12 cada uno | entities_table (solo atributos, no timeseries)          ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

### 5.2 Widget: Boton Volver al Mapa

**Posicion**: fila 0, columna 0, sizeX: 4, sizeY: 2

1. Agregar nuevo widget.
2. Buscar: **Cards > HTML Card** (o Markdown/HTML Card)
   - Tipo completo: `system.cards.markdown_card` o `system.basic.markdown_html_card`
3. En el contenido HTML/Markdown, pegar:

```html
<div id="btn-volver"
     style="cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 20px;
            border-radius: 6px;
            background: #305680;
            color: white;
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            font-size: 14px;
            line-height: 20px;
            letter-spacing: 0.25px;
            transition: background 0.2s ease;">
    <span style="font-size: 18px;">&#8592;</span>
    <span>Volver al Mapa</span>
</div>
```

4. No necesita datasource (se puede dejar vacio o usar cualquier alias).

#### Configurar accion del boton

1. Ir a la pestaña **"Actions"** del widget.
2. Hacer clic en **"Add action"**.
3. Configurar:

| Campo                    | Valor                            |
|--------------------------|----------------------------------|
| Action source            | **Widget header button** o **On HTML element click** |
| Name                     | `Volver al Mapa`                 |
| Action type              | **Navigate to new dashboard state** |
| Target dashboard state   | `default`                        |

> **Alternativa**: Si el widget es de tipo Markdown/HTML y soporta acciones en elementos HTML, se puede usar `headerButton` como action source o bien configurar un **custom action** con JavaScript:
> ```javascript
> const $injector = widgetContext.$scope.$injector;
> const dashboardService = $injector.get('dashboardService') || widgetContext.dashboard;
> widgetContext.dashboard.openDashboardState('default');
> ```
> En muchos casos basta con seleccionar Action source = "On HTML element click" y apuntar al elemento con id `btn-volver`.

4. Guardar.

### 5.3 Widget: Informacion del Pozo (Header)

**Posicion**: fila 0, columna 4, sizeX: 20, sizeY: 2

1. Agregar widget `system.cards.markdown_card` (o HTML Card).
2. Configurar datasource:

| Campo           | Valor                    |
|-----------------|--------------------------|
| Entity alias    | `Pozo Seleccionado`      |

Data keys:

| Key              | Type          | Label       |
|------------------|---------------|-------------|
| `entityName`     | Entity field  | Nombre      |
| `lift_type`      | Attribute     | Tipo        |
| `field_name`     | Attribute     | Campo       |
| `macolla_name`   | Attribute     | Macolla     |
| `status`         | Attribute     | Estado      |

3. En el contenido HTML, pegar:

```html
<div style="display: flex; align-items: center; padding: 8px 16px; gap: 24px;">
    <div>
        <span style="font-size: 24px; font-weight: 700; color: #305680;">
            ${entityName}
        </span>
    </div>
    <div style="display: flex; gap: 24px;">
        <div>
            <span style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">
                Tipo
            </span>
            <br/>
            <span style="font-size: 14px; font-weight: 600;">
                ${lift_type}
            </span>
        </div>
        <div>
            <span style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">
                Campo
            </span>
            <br/>
            <span style="font-size: 14px; font-weight: 600;">
                ${field_name}
            </span>
        </div>
        <div>
            <span style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">
                Macolla
            </span>
            <br/>
            <span style="font-size: 14px; font-weight: 600;">
                ${macolla_name}
            </span>
        </div>
        <div>
            <span style="font-size: 11px; color: #9FA6B4; text-transform: uppercase;">
                Estado
            </span>
            <br/>
            <span style="font-size: 14px; font-weight: 600;">
                ${status}
            </span>
        </div>
    </div>
</div>
```

4. Configurar apariencia:
   - Background color: `#FFFFFF`
   - Show title: **Desactivado**
   - Padding: `0`

5. Guardar.

### 5.4 Widgets: KPI Cards del Pozo (6 tarjetas)

**Posicion**: fila 2, cada una sizeX: 4, sizeY: 3

Todas usan el widget `system.cards.aggregated_value_card` con el alias **"Pozo Seleccionado"** y agregacion **NONE** (ultimo valor).

#### KPI 1: Produccion Actual

| Campo           | Valor                    |
|-----------------|--------------------------|
| Entity alias    | `Pozo Seleccionado`      |
| Data key        | `flow_rate_bpd`          |
| Aggregation     | NONE                     |
| Title           | `Produccion`             |
| Units           | `BPD`                    |
| Decimals        | `0`                      |
| Value color     | `#4CAF50`                |

Posicion: row 2, col 0, sizeX: 4, sizeY: 3.

#### KPI 2: Presion Tubing

| Campo           | Valor                    |
|-----------------|--------------------------|
| Data key        | `tubing_pressure_psi`    |
| Title           | `Presion Tubing`         |
| Units           | `PSI`                    |
| Decimals        | `1`                      |

Posicion: row 2, col 4, sizeX: 4, sizeY: 3.

#### KPI 3: Presion Casing

| Campo           | Valor                    |
|-----------------|--------------------------|
| Data key        | `casing_pressure_psi`    |
| Title           | `Presion Casing`         |
| Units           | `PSI`                    |
| Decimals        | `1`                      |

Posicion: row 2, col 8, sizeX: 4, sizeY: 3.

#### KPI 4: Corriente Motor

| Campo           | Valor                    |
|-----------------|--------------------------|
| Data key        | `motor_current_a`        |
| Title           | `Corriente Motor`        |
| Units           | `A`                      |
| Decimals        | `1`                      |

Posicion: row 2, col 12, sizeX: 4, sizeY: 3.

#### KPI 5: Potencia Motor

| Campo           | Valor                    |
|-----------------|--------------------------|
| Data key        | `motor_power_kw`         |
| Title           | `Potencia Motor`         |
| Units           | `kW`                     |
| Decimals        | `1`                      |

Posicion: row 2, col 16, sizeX: 4, sizeY: 3.

#### KPI 6: Variable Especifica por Tipo

La sexta tarjeta muestra una variable diferente segun el tipo de levantamiento del pozo. Para lograr esto se crean **4 widgets** en la misma posicion y se usa **Widget Visibility Conditions** para mostrar solo el que corresponda.

Posicion para los 4: row 2, col 20, sizeX: 4, sizeY: 3.

**Widget 6a - Para pozos ESP:**

| Campo              | Valor                    |
|--------------------|--------------------------|
| Data key           | `motor_temperature_f`    |
| Title              | `Temp. Motor`            |
| Units              | `F`                      |
| Decimals           | `0`                      |

Visibility condition:
```javascript
return entity.attributes.lift_type === 'ESP' || entity.attributes.lift_type === 'esp';
```

**Widget 6b - Para pozos SRP:**

| Campo              | Valor                    |
|--------------------|--------------------------|
| Data key           | `pump_fillage_pct`       |
| Title              | `Llenado Bomba`          |
| Units              | `%`                      |
| Decimals           | `1`                      |

Visibility condition:
```javascript
return entity.attributes.lift_type === 'SRP' || entity.attributes.lift_type === 'srp';
```

**Widget 6c - Para pozos PCP:**

| Campo              | Valor                    |
|--------------------|--------------------------|
| Data key           | `speed_rpm`              |
| Title              | `Velocidad`              |
| Units              | `RPM`                    |
| Decimals           | `0`                      |

Visibility condition:
```javascript
return entity.attributes.lift_type === 'PCP' || entity.attributes.lift_type === 'pcp';
```

**Widget 6d - Para pozos Gas Lift:**

| Campo              | Valor                    |
|--------------------|--------------------------|
| Data key           | `gas_injection_rate_mscfd`|
| Title              | `Iny. Gas`               |
| Units              | `MSCFD`                  |
| Decimals           | `1`                      |

Visibility condition:
```javascript
return entity.attributes.lift_type === 'Gas Lift' || entity.attributes.lift_type === 'gaslift';
```

> **Como configurar Widget Visibility Conditions**: En la configuracion del widget, buscar la seccion **"Widget visibility"** (normalmente en la pestaña "Appearance" o "Advanced"). Activar la opcion y pegar la funcion JavaScript correspondiente. La funcion recibe el objeto `entity` con sus atributos y debe retornar `true` si el widget debe mostrarse, o `false` si debe ocultarse.

### 5.5 Widget: Grafico de Produccion

**Posicion**: fila 6, columna 0, sizeX: 12, sizeY: 8

1. Agregar nuevo widget.
2. Buscar: **Charts > Time Series Chart**
   - Tipo completo: `system.time_series_chart`
3. Configurar datasource:

| Campo           | Valor                    |
|-----------------|--------------------------|
| Entity alias    | `Pozo Seleccionado`      |

Data key:

| Key                | Type        | Label         | Color     | Axis  |
|--------------------|-------------|---------------|-----------|-------|
| `flow_rate_bpd`    | Timeseries  | `Produccion`  | `#4CAF50` | Left  |

4. Configurar ejes Y:

```json
{
    "yAxes": {
        "default": {
            "label": "Produccion (BPD)",
            "position": "left",
            "units": "BPD",
            "showLabels": true,
            "showSplitLines": true,
            "min": 0
        }
    }
}
```

En la interfaz, ir a la seccion de **Y Axes** y configurar:

| Campo         | Valor                |
|---------------|----------------------|
| Label         | `Produccion (BPD)`   |
| Position      | Left                 |
| Units         | `BPD`                |
| Min value     | `0`                  |

5. Settings adicionales:

| Campo           | Valor             |
|-----------------|-------------------|
| Title           | `Produccion`      |
| Show legend     | **Activado (ON)** |
| Animation       | **Activado (ON)** |

6. Configurar timewindow: en la pestaña de timewindow del widget (o usar el timewindow del dashboard):

| Campo           | Valor             |
|-----------------|-------------------|
| Type            | Realtime          |
| Time range      | Last 1 hour       |

7. Guardar.

### 5.6 Widgets: Graficos Especificos por Tipo de Levantamiento

**Posicion**: fila 6, columna 12, sizeX: 12, sizeY: 8

Se crean **4 widgets de time series chart** en la misma posicion, cada uno con una **Widget Visibility Condition** para que solo se muestre el que corresponda al tipo de pozo seleccionado.

#### Grafico para pozos ESP

Widget: `system.time_series_chart`

Datasource: `Pozo Seleccionado`

Data keys:

| Key                    | Type        | Label            | Color     | Axis   |
|------------------------|-------------|------------------|-----------|--------|
| `motor_temperature_f`  | Timeseries  | `Temp. Motor`    | `#F44336` | Left   |
| `motor_current_a`      | Timeseries  | `Corriente`      | `#2196F3` | Right  |
| `vibration_ips`        | Timeseries  | `Vibracion`      | `#FF9800` | Right  |

Settings:

| Campo           | Valor                       |
|-----------------|-----------------------------|
| Title           | `Monitoreo ESP`             |
| Show legend     | **Activado**                |

Configurar dos ejes Y:
- **Left axis**: Label = `Temperatura (F)`, Units = `F`
- **Right axis**: Label = `Corriente (A) / Vibracion (IPS)`

Visibility condition:
```javascript
return entity.attributes.lift_type === 'ESP' || entity.attributes.lift_type === 'esp';
```

#### Grafico para pozos SRP

Widget: `system.time_series_chart`

Datasource: `Pozo Seleccionado`

Data keys:

| Key                  | Type        | Label         | Color     | Axis   |
|----------------------|-------------|---------------|-----------|--------|
| `load_lb`            | Timeseries  | `Carga`       | `#F44336` | Left   |
| `spm`                | Timeseries  | `SPM`         | `#2196F3` | Right  |
| `pump_fillage_pct`   | Timeseries  | `Llenado %`   | `#4CAF50` | Right  |

Settings:

| Campo           | Valor                       |
|-----------------|-----------------------------|
| Title           | `Monitoreo SRP`             |

Ejes Y:
- **Left axis**: Label = `Carga (lb)`, Units = `lb`
- **Right axis**: Label = `SPM / Llenado (%)`

Visibility condition:
```javascript
return entity.attributes.lift_type === 'SRP' || entity.attributes.lift_type === 'srp';
```

#### Grafico para pozos PCP

Widget: `system.time_series_chart`

Datasource: `Pozo Seleccionado`

Data keys:

| Key                    | Type        | Label         | Color     | Axis   |
|------------------------|-------------|---------------|-----------|--------|
| `speed_rpm`            | Timeseries  | `Velocidad`   | `#2196F3` | Left   |
| `motor_torque_ftlb`    | Timeseries  | `Torque`      | `#FF9800` | Right  |

Settings:

| Campo           | Valor                       |
|-----------------|-----------------------------|
| Title           | `Monitoreo PCP`             |

Ejes Y:
- **Left axis**: Label = `Velocidad (RPM)`, Units = `RPM`
- **Right axis**: Label = `Torque (ft-lb)`, Units = `ft-lb`

Visibility condition:
```javascript
return entity.attributes.lift_type === 'PCP' || entity.attributes.lift_type === 'pcp';
```

#### Grafico para pozos Gas Lift

Para pozos de Gas Lift, dado que las variables principales son menos, se puede crear un grafico combinado de produccion e inyeccion de gas, o simplemente no mostrar un grafico adicional (el grafico de produccion del lado izquierdo ya es suficiente).

Si se desea agregar un grafico complementario:

Widget: `system.time_series_chart`

Datasource: `Pozo Seleccionado`

Data keys:

| Key                          | Type        | Label          | Color     | Axis   |
|------------------------------|-------------|----------------|-----------|--------|
| `gas_injection_rate_mscfd`   | Timeseries  | `Iny. Gas`     | `#9C27B0` | Left   |
| `tubing_pressure_psi`        | Timeseries  | `Presion Tbg`  | `#607D8B` | Right  |

Settings:

| Campo           | Valor                       |
|-----------------|-----------------------------|
| Title           | `Monitoreo Gas Lift`        |

Visibility condition:
```javascript
return entity.attributes.lift_type === 'Gas Lift' || entity.attributes.lift_type === 'gaslift';
```

### 5.7 Widget: Tabla de Atributos Mecanicos

**Posicion**: fila 14, columna 0, sizeX: 12, sizeY: 6

Este widget muestra los atributos de configuracion mecanica del pozo seleccionado en formato tabular.

1. Agregar widget `system.cards.entities_table`.
2. Datasource:

| Campo           | Valor                    |
|-----------------|--------------------------|
| Entity alias    | `Pozo Seleccionado`      |

Data keys (todos de tipo **Attribute**):

| Key                      | Type      | Label                   |
|--------------------------|-----------|-------------------------|
| `entityName`             | Entity field | `Pozo`               |
| `lift_type`              | Attribute | `Tipo Levantamiento`    |
| `pump_depth_ft`          | Attribute | `Prof. Bomba (ft)`      |
| `tubing_od_in`           | Attribute | `OD Tubing (in)`        |
| `casing_id_in`           | Attribute | `ID Casing (in)`        |
| `pump_stages`            | Attribute | `Etapas Bomba`          |
| `motor_hp`               | Attribute | `HP Motor`              |
| `cable_size_awg`         | Attribute | `Cable (AWG)`           |

Settings:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Title                  | `Datos Mecanicos`        |
| Enable search          | **Desactivado**          |
| Display pagination     | **Desactivado**          |
| Enable selection       | **Desactivado**          |

> **Nota**: No todas las claves pueden existir para todos los tipos de pozo. Las celdas con datos no disponibles simplemente mostraran un valor vacio o `N/A`.

### 5.8 Widget: Datos del Reservorio

**Posicion**: fila 14, columna 12, sizeX: 12, sizeY: 6

Muestra los atributos del yacimiento y las condiciones de fondo del pozo.

1. Agregar widget `system.cards.entities_table`.
2. Datasource:

| Campo           | Valor                    |
|-----------------|--------------------------|
| Entity alias    | `Pozo Seleccionado`      |

Data keys (todos de tipo **Attribute**):

| Key                          | Type      | Label                     |
|------------------------------|-----------|---------------------------|
| `reservoir_pressure_psi`     | Attribute | `Presion Reservorio (PSI)`|
| `bubble_point_psi`           | Attribute | `Punto Burbuja (PSI)`    |
| `oil_gravity_api`            | Attribute | `Gravedad API`            |
| `water_cut_pct`              | Attribute | `Corte de Agua (%)`       |
| `gor_scf_bbl`               | Attribute | `GOR (SCF/BBL)`           |
| `productivity_index_bpd_psi` | Attribute | `Indice Productividad`    |
| `reservoir_temperature_f`    | Attribute | `Temp. Reservorio (F)`    |
| `formation_name`             | Attribute | `Formacion`               |

Settings:

| Campo                  | Valor                    |
|------------------------|--------------------------|
| Title                  | `Datos del Reservorio`   |
| Enable search          | **Desactivado**          |
| Display pagination     | **Desactivado**          |
| Enable selection       | **Desactivado**          |

### 5.9 Guardar el estado well_detail

Hacer clic en **"Save"** para guardar todos los cambios del estado de detalle.

---

## Paso 6: Navegacion entre Estados

### 6.1 Resumen de la navegacion

El dashboard tiene dos estados con la siguiente logica de navegacion:

```
┌─────────────────────────┐
│   Estado: default       │
│   (Vista General)       │
│                         │
│  [Mapa] ──clic──┐      │
│  [Tabla] ─clic──┤      │
│                  │      │
└──────────────────┼──────┘
                   │
                   v
┌─────────────────────────┐
│   Estado: well_detail   │
│   (Vista del Pozo)      │
│                         │
│  [← Volver] ──clic─────┼──> regresa a default
│                         │
└─────────────────────────┘
```

### 6.2 Acciones del estado default hacia well_detail

Estas acciones ya fueron configuradas en los pasos 4.3 y 4.4. Resumiendo:

**En el widget Mapa** (paso 4.3):
- Action source: **Marker click**
- Action type: **Navigate to new dashboard state**
- Target state: `well_detail`
- Set entity from widget: **Activado**

**En el widget Tabla** (paso 4.4):
- Action source: **Row click**
- Action type: **Navigate to new dashboard state**
- Target state: `well_detail`
- Set entity from widget: **Activado**

La opcion "Set entity from widget" es fundamental: pasa el ID del pozo seleccionado al estado destino, donde el alias "Pozo Seleccionado" (de tipo "Entity from dashboard state") lo captura y lo usa como fuente de datos para todos los widgets del estado well_detail.

### 6.3 Accion de regreso: well_detail hacia default

Esta accion ya fue configurada en el paso 5.2 (widget boton Volver). Resumiendo:

**En el widget "Volver al Mapa"** (paso 5.2):
- Action source: **On HTML element click** (o Header button)
- Action type: **Navigate to new dashboard state**
- Target state: `default`

### 6.4 Verificar la navegacion

1. Guardar el dashboard.
2. Salir del modo edicion (clic en el icono de check/save).
3. En el estado default:
   - Hacer clic en un marcador del mapa. Debe navegar al estado well_detail mostrando los datos de ese pozo.
   - Hacer clic en una fila de la tabla. Debe navegar igualmente.
4. En el estado well_detail:
   - Verificar que el nombre del pozo aparece en el header.
   - Verificar que los KPIs muestran datos.
   - Verificar que el grafico especifico por tipo se muestra (y los de otros tipos estan ocultos).
   - Hacer clic en "Volver al Mapa". Debe regresar al estado default.

### 6.5 Solucion de problemas comunes

| Problema                                    | Causa probable                                  | Solucion                                           |
|---------------------------------------------|------------------------------------------------|----------------------------------------------------|
| El mapa no muestra marcadores               | Faltan atributos latitude/longitude             | Ejecutar el script del prerequisito                |
| Marcadores en posicion incorrecta           | Coordenadas invertidas (lat/lon)                | Verificar que latitude es ~8-10 y longitude es negativa |
| Los filtros no funcionan                    | Falta atributo wellFilter en los pozos          | Ejecutar el script de wellFilter del prerequisito  |
| Al hacer clic no navega al detalle          | Falta la accion o el estado well_detail         | Verificar que existe el estado y que la accion tiene Set entity from widget activado |
| El detalle muestra "No data"                | El alias Pozo Seleccionado no resuelve          | Verificar que Set entity from widget esta activado en la accion de navegacion |
| Widget visibility no oculta widgets         | Funcion JavaScript incorrecta                   | Verificar que la comparacion usa el valor exacto del atributo lift_type |
| Grafico vacio en el detalle                 | Timewindow muy corto o no hay datos recientes   | Ampliar el rango temporal o verificar que el simulador esta enviando datos |

---

## Tips y Mejores Practicas

### Identificadores de widgets

Siempre usar el formato completo `typeFullFqn` para identificar widgets. Nunca usar la combinacion `bundleAlias` + `typeAlias` que esta deprecada.

| Widget                      | typeFullFqn correcto                                  |
|-----------------------------|-------------------------------------------------------|
| Aggregated Value Card       | `system.cards.aggregated_value_card`                  |
| Entities Table              | `system.cards.entities_table`                         |
| Time Series Chart           | `system.time_series_chart`                            |
| Mapa OpenStreetMap          | `system.map`                                          |
| Update Multiple Attributes  | `system.input_widgets.update_multiple_attributes`     |
| Markdown/HTML Card          | `system.cards.markdown_card`                          |

### Configuracion del timewindow

Para que los datos se muestren correctamente:

| Tipo de dato      | Timewindow recomendado      | Aggregation    |
|-------------------|----------------------------|----------------|
| Ultimo valor      | Realtime, Last 1 min        | NONE           |
| Tendencia 1 hora  | Realtime, Last 1 hour       | AVG o NONE     |
| Historico diario  | History, Last 24 hours      | AVG            |
| KPI agregado      | Realtime, Last 5 min        | SUM/AVG/COUNT  |

### Configuracion de Time Series Chart

Al crear un widget de Time Series Chart, es importante completar **todos** los campos obligatorios de la configuracion. Si se dejan campos vacios (especialmente en la seccion de ejes Y), el widget puede fallar y mostrar una pantalla en blanco.

Campos minimos obligatorios:
- Al menos un data key con tipo Timeseries
- Al menos un eje Y configurado (label, position, units)
- Timewindow definido (puede heredar del dashboard)

### Widget Visibility Conditions

Las condiciones de visibilidad son funciones JavaScript que se evaluan en el contexto del widget. El objeto disponible es `entity` que contiene:

```javascript
entity = {
    id: { entityType: "ASSET", id: "..." },
    name: "BOS-M1-P01",
    label: "BOS-M1-P01",
    attributes: {
        lift_type: "ESP",
        field_name: "Boscan",
        status: "producing",
        // ... otros atributos
    }
}
```

Ejemplo de condicion:
```javascript
return entity.attributes.lift_type === 'ESP' || entity.attributes.lift_type === 'esp';
```

> **Atencion**: El valor del atributo puede variar en mayusculas/minusculas segun como se haya almacenado. Es recomendable normalizar la comparacion.

### Orden de creacion recomendado

1. Prerequisito: agregar coordenadas y wellFilter (scripts Python)
2. Crear el dashboard vacio con settings y CSS
3. Crear todos los Entity Aliases
4. Crear el filtro
5. Agregar widgets del estado default (filtros, KPIs, mapa, tabla)
6. Configurar acciones del mapa y tabla
7. Crear el estado well_detail
8. Agregar widgets del estado well_detail
9. Configurar accion del boton Volver
10. Probar toda la navegacion

### Paleta de colores del dashboard

| Uso                     | Color     | Codigo   |
|-------------------------|-----------|----------|
| Texto principal         | Gris      | `#4B535B` |
| Titulos y enlaces       | Azul      | `#305680` |
| Etiquetas secundarias   | Gris claro| `#9FA6B4` |
| Fondo de tarjetas       | Blanco    | `#FFFFFF` |
| Fondo KPI               | Gris muy claro | `#F5F7FA` |
| Hover en tabla          | Gris hover| `#F9F9FB` |
| ESP (verde)             | Verde     | `#4CAF50` |
| SRP (azul)              | Azul      | `#2196F3` |
| PCP (naranja)           | Naranja   | `#FF9800` |
| Gas Lift (morado)       | Morado    | `#9C27B0` |
| Sin tipo                | Gris      | `#607D8B` |
| Alerta/Temperatura      | Rojo      | `#F44336` |

### Probar con datos reducidos

Antes de configurar el dashboard completo, se recomienda probarlo con un subconjunto de pozos (por ejemplo, solo los pozos de una macolla). Esto permite:

- Validar que las coordenadas aparecen correctamente en el mapa.
- Verificar que los filtros funcionan.
- Confirmar que la navegacion de drill-down pasa el ID correcto.
- Ajustar el layout sin tener que esperar a que se carguen 63 pozos.

Para limitar temporalmente los datos, se puede modificar el alias "Todos los Pozos" para agregar un filtro adicional por campo o macolla, y luego eliminarlo cuando todo este verificado.

---

## Resumen Final

Al completar todos los pasos de esta guia, el dashboard contara con:

1. **Vista principal** con:
   - 4 toggles de filtro por tipo de levantamiento
   - 4 tarjetas KPI con metricas agregadas
   - Mapa interactivo con marcadores coloreados por tipo
   - Tabla de pozos con busqueda y paginacion
   - Acciones de clic para drill-down

2. **Vista de detalle** con:
   - Boton de regreso al mapa
   - Header con informacion del pozo
   - 6 tarjetas KPI individuales (la ultima varia por tipo)
   - Grafico de produccion
   - Grafico especifico por tipo de levantamiento (con visibility conditions)
   - Tabla de datos mecanicos
   - Tabla de datos del reservorio

3. **Navegacion bidireccional** entre estados usando acciones de ThingsBoard.

Este dashboard proporciona una vista operacional completa de un campo petrolero, permitiendo al operador o ingeniero de produccion monitorear el estado de los pozos en tiempo real, filtrar por tipo de levantamiento, y profundizar en los detalles de cada pozo individual.
