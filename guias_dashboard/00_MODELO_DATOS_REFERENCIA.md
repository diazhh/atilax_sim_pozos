# Modelo de Datos - Referencia Completa para Dashboards ThingsBoard PE

## Sistema de Monitoreo de Campo Petrolero Atilax

**Documento de referencia** para la construccion manual de dashboards en ThingsBoard Professional Edition.
Contiene todas las entidades, claves de telemetria, atributos de servidor, relaciones y tipos de alarma
disponibles en el sistema.

> **Servidor ThingsBoard:** `http://144.126.150.120:8080`
> **Usuario:** `well@atilax.io` / **Password:** `10203040`
> **Autenticacion API:** POST `/api/auth/login` -> JWT token -> Header `X-Authorization: Bearer {token}`

---

## Tabla de Contenidos

1. [Jerarquia de Entidades](#1-jerarquia-de-entidades)
2. [Tipos de Entidad y Conteos](#2-tipos-de-entidad-y-conteos)
3. [Relaciones entre Entidades](#3-relaciones-entre-entidades)
4. [Perfiles de Dispositivo (Device Profiles)](#4-perfiles-de-dispositivo-device-profiles)
5. [Telemetria por Tipo de Levantamiento](#5-telemetria-por-tipo-de-levantamiento)
6. [Telemetria del Dispositivo RTU vs Asset del Pozo](#6-telemetria-del-dispositivo-rtu-vs-asset-del-pozo)
7. [Atributos de Servidor por Pozo](#7-atributos-de-servidor-por-pozo)
8. [Alarmas Operativas](#8-alarmas-operativas)
9. [Datos de Ubicacion (Mapas)](#9-datos-de-ubicacion-mapas)
10. [Cadenas de Reglas (Rule Chains)](#10-cadenas-de-reglas-rule-chains)
11. [Dashboards Existentes](#11-dashboards-existentes)
12. [Guia Rapida: Datasources para Widgets](#12-guia-rapida-datasources-para-widgets)
13. [Referencia de Unidades](#13-referencia-de-unidades)

---

## 1. Jerarquia de Entidades

```
Tenant (Atilax)
  |
  +-- Campo (Asset tipo "field")
  |     |
  |     +-- Macolla (Asset tipo "macolla")
  |           |
  |           +-- Pozo (Asset tipo "well")
  |           |     |
  |           |     +-- RTU (Device tipo "rtu_esp" / "rtu_srp" / "rtu_gaslift" / "rtu_pcp")
  |           |     +-- [Opcional] Downhole Gauge (Device tipo "downhole_gauge")
  |           |     +-- [Opcional] Multiphase Meter (Device tipo "multiphase_meter")
  |           |
  |           +-- Facilidad (Asset tipo "facility")
  |           |     Separadores, compresores, tanques
  |           |
  |           +-- Gateway IoT (Device tipo "iot_gateway")
```

**Flujo de datos:**
```
RTU (Device) --telemetria--> Rule Chain --propaga--> Pozo (Asset)
```

El dispositivo RTU transmite la telemetria cruda. La cadena de reglas "Propagacion Device->Asset"
filtra las metricas relevantes y las copia al asset del pozo padre.

---

## 2. Tipos de Entidad y Conteos

### Campos (Assets tipo "field") - 3 total

| Campo | Template | Region | Macollas | Pozos Totales |
|-------|----------|--------|----------|---------------|
| Campo Boscan | lago_maracaibo | Lago de Maracaibo | 3 | 24 |
| Campo Cerro Negro | faja_orinoco | Faja del Orinoco | 2 | 27 |
| Campo Anaco | oriente_liviano | Oriente | 2 | 12 |

### Macollas (Assets tipo "macolla") - 7 total

| Macolla | Campo | Pozos |
|---------|-------|-------|
| MAC-BOS-01 | Campo Boscan | 8 |
| MAC-BOS-02 | Campo Boscan | 10 |
| MAC-BOS-03 | Campo Boscan | 6 |
| MAC-NEG-01 | Campo Cerro Negro | 12 |
| MAC-NEG-02 | Campo Cerro Negro | 15 |
| MAC-ANA-01 | Campo Anaco | 5 |
| MAC-ANA-02 | Campo Anaco | 7 |

### Distribucion de Pozos por Tipo de Levantamiento - 63 total

| Tipo Levantamiento | Abreviacion | Total Pozos | Device Profile |
|--------------------|-------------|-------------|----------------|
| Bombeo Electrosumergible | ESP | 18 | rtu_esp |
| Bombeo Mecanico | SRP | 20 | rtu_srp |
| Bombeo Cavidad Progresiva | PCP | 16 | rtu_pcp |
| Levantamiento por Gas | Gas Lift | 9 | rtu_gaslift |

### Distribucion por Campo

| Campo | ESP | SRP | PCP | Gas Lift |
|-------|-----|-----|-----|----------|
| Campo Boscan | 20% | 65% | 5% | 10% |
| Campo Cerro Negro | 35% | 10% | 55% | 0% |
| Campo Anaco | 35% | 15% | 0% | 50% |

### Facilidades por Macolla (Assets tipo "facility")

Cada macolla tiene por defecto:
- 2 separadores (`SEPARATOR-{macolla}-01`, `SEPARATOR-{macolla}-02`)
- 1 compresor (`COMPRESSOR-{macolla}-01`)
- 2 tanques (`TANK-{macolla}-01`, `TANK-{macolla}-02`)

### Dispositivos Auxiliares

| Dispositivo | Profile | Condicion |
|-------------|---------|-----------|
| Gateway IoT | iot_gateway | 1 por macolla (`GW-{macolla}`) |
| Downhole Gauge | downhole_gauge | ~30% de pozos ESP (`DH-{pozo}`) |
| Multiphase Meter | multiphase_meter | ~20% de todos los pozos (`MM-{pozo}`) |

---

## 3. Relaciones entre Entidades

| Desde (from) | Tipo Relacion | Hacia (to) | Descripcion |
|--------------|---------------|-------------|-------------|
| Campo (Asset) | Contains | Macolla (Asset) | Campo contiene macollas |
| Macolla (Asset) | Contains | Pozo (Asset) | Macolla contiene pozos |
| Macolla (Asset) | Contains | Gateway (Device) | Macolla contiene su gateway |
| Macolla (Asset) | Contains | Facilidad (Asset) | Macolla contiene facilidades |
| Pozo (Asset) | Contains | RTU (Device) | Pozo contiene su RTU |
| Pozo (Asset) | Contains | Downhole Gauge (Device) | Si aplica |
| Pozo (Asset) | Contains | Multiphase Meter (Device) | Si aplica |
| Pozo (Asset) | Uses | Facilidad (Asset) | Pozo usa separador |

**Nota para dashboards:** Usar relaciones `Contains` con direccion `FROM` para navegar
de padre a hijos. Para navegar de Device a Asset padre, usar direccion `TO`.

---

## 4. Perfiles de Dispositivo (Device Profiles)

| Profile Name | Descripcion | Cantidad Estimada |
|-------------|-------------|-------------------|
| rtu_esp | RTU para pozos ESP | 18 |
| rtu_srp | RTU para pozos SRP | 20 |
| rtu_gaslift | RTU para pozos Gas Lift | 9 |
| rtu_pcp | RTU para pozos PCP | 16 |
| downhole_gauge | Sensor de presion/temperatura de fondo | ~5 |
| multiphase_meter | Medidor multifasico | ~12 |
| iot_gateway | Gateway IoT por macolla | 7 |

---

## 5. Telemetria por Tipo de Levantamiento

### 5.1 Telemetria en el ASSET del Pozo (propagada por Rule Chain)

Estas son las claves de telemetria que llegan al asset del pozo despues de pasar por la
cadena de reglas de propagacion. **Estas son las claves que deben usarse en dashboards
cuando el datasource es el asset del pozo.**

#### Claves Comunes (todos los tipos)

| Clave | Descripcion | Unidad | Rango Tipico |
|-------|-------------|--------|--------------|
| `flow_rate_bpd` | Tasa de flujo total (liquido) | BPD | 100 - 2500 |
| `tubing_pressure_psi` | Presion de tubing (cabezal) | PSI | 15 - 500 |
| `casing_pressure_psi` | Presion de casing (cabezal) | PSI | 30 - 500 |
| `motor_power_kw` | Potencia del motor | kW | 1 - 300 |
| `wellhead_temperature_f` | Temperatura del cabezal | F | 80 - 200 |
| `last_telemetry_ts` | Timestamp ultima telemetria | ms epoch | - |

#### ESP - Bombeo Electrosumergible (13 claves en asset)

| Clave | Descripcion | Unidad | Rango Tipico |
|-------|-------------|--------|--------------|
| `flow_rate_bpd` | Tasa de flujo | BPD | 200 - 2500 |
| `casing_pressure_psi` | Presion de casing | PSI | 30 - 400 |
| `tubing_pressure_psi` | Presion de tubing | PSI | 10 - 300 |
| `motor_current_a` | Corriente del motor | A | 5 - 90 |
| `motor_power_kw` | Potencia del motor | kW | 10 - 300 |
| `motor_temperature_f` | Temperatura del motor | F | 100 - 350 |
| `motor_voltage_v` | Voltaje del motor | V | 400 - 3500 |
| `frequency_hz` | Frecuencia VSD | Hz | 30 - 65 |
| `intake_pressure_psi` | Presion de intake (succion) | PSI | 50 - 2000 |
| `discharge_pressure_psi` | Presion de descarga | PSI | 100 - 5000 |
| `vibration_ips` | Vibracion (max X,Y) | IPS | 0.01 - 5.0 |
| `wellhead_temperature_f` | Temperatura cabezal | F | 80 - 200 |
| `last_telemetry_ts` | Timestamp ultimo dato | ms | - |

#### SRP - Bombeo Mecanico (9 claves en asset)

| Clave | Descripcion | Unidad | Rango Tipico |
|-------|-------------|--------|--------------|
| `flow_rate_bpd` | Tasa de flujo | BPD | 50 - 1500 |
| `casing_pressure_psi` | Presion de casing | PSI | 30 - 400 |
| `tubing_pressure_psi` | Presion de tubing | PSI | 15 - 200 |
| `motor_current_a` | Corriente del motor | A | 5 - 60 |
| `motor_power_kw` | Potencia del motor | kW | 1 - 80 |
| `spm` | Golpes por minuto | SPM | 2 - 15 |
| `load_lb` | Carga en barra pulida (max) | lb | 2000 - 36000 |
| `pump_fillage_pct` | Llenado de bomba | % | 20 - 100 |
| `last_telemetry_ts` | Timestamp ultimo dato | ms | - |

#### PCP - Bombeo de Cavidad Progresiva (8 claves en asset)

| Clave | Descripcion | Unidad | Rango Tipico |
|-------|-------------|--------|--------------|
| `flow_rate_bpd` | Tasa de flujo | BPD | 100 - 3000 |
| `casing_pressure_psi` | Presion de casing | PSI | 30 - 500 |
| `tubing_pressure_psi` | Presion de tubing | PSI | 15 - 300 |
| `motor_current_a` | Corriente del motor | A | 5 - 50 |
| `motor_power_kw` | Potencia del motor | kW | 1 - 100 |
| `speed_rpm` | Velocidad del motor/drive | RPM | 30 - 400 |
| `motor_torque_ftlb` | Torque del motor | ft-lb | 100 - 5000 |
| `last_telemetry_ts` | Timestamp ultimo dato | ms | - |

#### Gas Lift - Levantamiento por Gas (2 claves en asset)

| Clave | Descripcion | Unidad | Rango Tipico |
|-------|-------------|--------|--------------|
| `flow_rate_bpd` | Tasa de flujo | BPD | 100 - 800 |
| `last_telemetry_ts` | Timestamp ultimo dato | ms | - |

> **NOTA:** El Gas Lift tiene telemetria limitada en el asset porque las claves
> `gl_injection_rate_mscfd`, `gl_injection_pressure_psi`, `choke_size_64ths` no
> estan incluidas en el filtro de propagacion de la Rule Chain. Si se necesitan,
> se debe leer directamente del dispositivo RTU o modificar la Rule Chain.

---

### 5.2 Telemetria COMPLETA en el Dispositivo RTU

Estas son TODAS las claves que genera el simulador y que quedan almacenadas en el
dispositivo RTU. Incluyen claves adicionales que NO se propagan al asset.

#### RTU ESP (rtu_esp) - 24 claves

| Clave | Alias de | Propagada a Asset |
|-------|----------|-------------------|
| `flow_rate_bpd` | - | SI |
| `water_cut_pct` | - | NO |
| `gor_scf_stb` | - | NO |
| `thp_psi` | - | NO (usa `tubing_pressure_psi`) |
| `chp_psi` | - | NO (usa `casing_pressure_psi`) |
| `tht_f` | - | NO (usa `wellhead_temperature_f`) |
| `tubing_pressure_psi` | alias de `thp_psi` | SI |
| `casing_pressure_psi` | alias de `chp_psi` | SI |
| `wellhead_temperature_f` | alias de `tht_f` | SI |
| `intake_pressure_psi` | - | SI |
| `discharge_pressure_psi` | - | SI |
| `motor_temp_f` | - | NO (usa `motor_temperature_f`) |
| `motor_temperature_f` | alias de `motor_temp_f` | SI |
| `intake_temp_f` | - | NO |
| `motor_current_a` | - | SI |
| `motor_voltage_v` | - | SI |
| `motor_power_kw` | - | SI |
| `vsd_frequency_hz` | - | NO (usa `frequency_hz`) |
| `frequency_hz` | alias de `vsd_frequency_hz` | SI |
| `vibration_x_ips` | - | NO |
| `vibration_y_ips` | - | NO |
| `vibration_ips` | max(x,y) | SI |
| `insulation_mohm` | - | NO |
| `pump_efficiency_pct` | - | NO |

#### RTU SRP (rtu_srp) - 15 claves

| Clave | Alias de | Propagada a Asset |
|-------|----------|-------------------|
| `flow_rate_bpd` | - | SI |
| `water_cut_pct` | - | NO |
| `thp_psi` | - | NO (usa `tubing_pressure_psi`) |
| `chp_psi` | - | NO (usa `casing_pressure_psi`) |
| `tubing_pressure_psi` | alias de `thp_psi` | SI |
| `casing_pressure_psi` | alias de `chp_psi` | SI |
| `motor_current_a` | - | SI |
| `motor_power_kw` | - | SI |
| `spm` | - | SI |
| `polished_rod_load_max_lb` | - | NO |
| `polished_rod_load_min_lb` | - | NO |
| `load_lb` | alias de `polished_rod_load_max_lb` | SI |
| `fluid_level_ft` | - | NO |
| `pump_fillage_pct` | - | SI |
| `pump_efficiency_pct` | - | NO |
| `stroke_counter` | - | NO |
| `dynamo_card_surface` | JSON [[pos,load],...] | NO |

#### RTU PCP (rtu_pcp) - 14 claves

| Clave | Alias de | Propagada a Asset |
|-------|----------|-------------------|
| `flow_rate_bpd` | - | SI |
| `water_cut_pct` | - | NO |
| `thp_psi` | - | NO (usa `tubing_pressure_psi`) |
| `chp_psi` | - | NO (usa `casing_pressure_psi`) |
| `tubing_pressure_psi` | alias de `thp_psi` | SI |
| `casing_pressure_psi` | alias de `chp_psi` | SI |
| `drive_torque_ftlb` | - | NO (usa `motor_torque_ftlb`) |
| `motor_torque_ftlb` | alias de `drive_torque_ftlb` | SI |
| `drive_rpm` | - | NO (usa `speed_rpm`) |
| `speed_rpm` | alias de `drive_rpm` | SI |
| `motor_current_a` | - | SI |
| `motor_power_kw` | - | SI |
| `intake_pressure_psi` | - | NO* |
| `sand_pct` | - | NO |
| `pump_efficiency_pct` | - | NO |

> *`intake_pressure_psi` en PCP no esta incluida en las claves PCP del filtro de propagacion.

#### RTU Gas Lift (rtu_gaslift) - 9 claves

| Clave | Alias de | Propagada a Asset |
|-------|----------|-------------------|
| `flow_rate_bpd` | - | SI |
| `water_cut_pct` | - | NO |
| `gor_scf_stb` | - | NO |
| `thp_psi` | - | NO |
| `chp_psi` | - | NO |
| `tht_f` | - | NO |
| `gl_injection_rate_mscfd` | - | NO |
| `gl_injection_pressure_psi` | - | NO |
| `choke_size_64ths` | - | NO |

---

## 6. Telemetria del Dispositivo RTU vs Asset del Pozo

### Diferencia Clave

| Aspecto | Dispositivo RTU | Asset Pozo |
|---------|-----------------|------------|
| **Tipo de entidad** | DEVICE | ASSET |
| **Telemetria** | Completa (todas las claves) | Filtrada (solo propagadas) |
| **Origen dato** | Directo del simulador | Propagado via Rule Chain |
| **Uso en dashboard** | Detalle tecnico avanzado | Vista operativa principal |
| **Ejemplo ESP** | 24 claves | 13 claves |
| **Ejemplo SRP** | 15+ claves | 9 claves |

### Cuando usar cada uno

- **Asset del Pozo:** Para la mayoria de dashboards operativos. Metricas normalizadas
  con nombres estandar (`tubing_pressure_psi` en vez de `thp_psi`).
- **Device RTU:** Cuando se necesiten datos no propagados como `water_cut_pct`,
  `pump_efficiency_pct`, `insulation_mohm`, `dynamo_card_surface`, etc.

### Como acceder a datos del RTU desde un dashboard del Pozo

En un widget de ThingsBoard cuyo datasource es el asset del pozo:
1. Usar **Entity from relations** con tipo `Contains` y direccion `FROM`
2. Filtrar por entity type `DEVICE` y device type `rtu_*`
3. Seleccionar las claves de telemetria del dispositivo

---

## 7. Atributos de Servidor por Pozo

Cada asset de pozo tiene entre 40 y 55 atributos de servidor dependiendo del tipo
de levantamiento. Se organizan en las siguientes categorias:

### 7.1 Identificacion

| Atributo | Tipo | Ejemplo | Descripcion |
|----------|------|---------|-------------|
| `well_name` | str | "CA-MAC-ANA-01-003" | Nombre del pozo |
| `well_code_pdvsa` | str | "PDVSA-CAM-CA-MAC..." | Codigo PDVSA |
| `field_name` | str | "Campo Anaco" | Campo al que pertenece |
| `macolla_name` | str | "MAC-ANA-01" | Macolla a la que pertenece |
| `lift_type` | str | "ESP" / "SRP" / "PCP" / "gas_lift" | Tipo de levantamiento |
| `lifting_type` | str | "ESP" | Alias de lift_type (para Rule Chain) |
| `status` | str | "producing" / "shut_in" / "workover" | Estado operativo |
| `install_date` | str | "" | Fecha de instalacion (vacio por defecto) |

### 7.2 Reservorio

| Atributo | Tipo | Unidad | Descripcion |
|----------|------|--------|-------------|
| `reservoir_pressure_psi` | float | PSI | Presion inicial del reservorio |
| `reservoir_temperature_f` | float | F | Temperatura del reservorio |
| `bubble_point_psi` | float | PSI | Presion de burbuja |
| `api_gravity` | float | API | Gravedad API del crudo |
| `gor_scf_stb` | float | SCF/STB | Relacion gas-petroleo |
| `water_cut_initial_pct` | float | % | Corte de agua inicial |
| `oil_viscosity_cp` | float | cP | Viscosidad del crudo (Beggs-Robinson) |
| `bo_factor` | float | - | Factor volumetrico del petroleo (Standing) |
| `productivity_index_bpd_psi` | float | BPD/PSI | Indice de productividad |
| `ipr_model` | str | - | Modelo IPR: "vogel" o "darcy" |
| `ipr_qmax_bpd` | float | BPD | Caudal maximo absoluto |
| `drive_mechanism` | str | - | "solution_gas", "water_drive", "gas_cap" |

### Rangos de Reservorio por Campo

| Parametro | Campo Boscan | Campo Cerro Negro | Campo Anaco |
|-----------|-------------|-------------------|-------------|
| Presion (PSI) | 2200 - 3000 | 800 - 1500 | 2500 - 4000 |
| Temperatura (F) | 160 - 200 | 120 - 160 | 200 - 280 |
| API | 10 - 15 | 6 - 10 | 28 - 36 |
| Viscosidad (cP) | 500 - 5000 | 2000 - 12000 | 1 - 10 |
| Corte de agua | 0.20 - 0.75 | 0.10 - 0.50 | 0.30 - 0.85 |
| GOR (SCF/STB) | 80 - 200 | 50 - 120 | 400 - 1500 |
| Produccion (BPD) | 200 - 1500 | 300 - 2500 | 100 - 800 |

### 7.3 Mecanico (Geometria del Pozo)

| Atributo | Tipo | Unidad | Descripcion |
|----------|------|--------|-------------|
| `total_depth_md_ft` | float | ft | Profundidad total medida |
| `total_depth_tvd_ft` | float | ft | Profundidad total vertical verdadera |
| `pump_depth_ft` | float | ft | Profundidad de la bomba |
| `perforations_top_ft` | float | ft | Tope de perforaciones |
| `perforations_bottom_ft` | float | ft | Base de perforaciones |
| `casing_od_in` | float | in | Diametro externo del casing |
| `casing_id_in` | float | in | Diametro interno del casing |
| `tubing_od_in` | float | in | Diametro externo del tubing |
| `tubing_id_in` | float | in | Diametro interno del tubing |
| `completion_type` | str | - | Tipo de completacion ("vertical") |

### 7.4 Atributos Especificos por Tipo de Levantamiento

#### ESP

| Atributo | Tipo | Unidad | Descripcion |
|----------|------|--------|-------------|
| `esp_pump_stages` | int | - | Numero de etapas de la bomba (100-280) |
| `esp_design_rate_bpd` | float | BPD | Tasa de diseno |
| `esp_design_head_ft` | float | ft | Cabeza de diseno |
| `esp_bep_rate_bpd` | float | BPD | Tasa en punto de mejor eficiencia |
| `esp_efficiency_at_bep` | float | - | Eficiencia en BEP (0-1) |
| `esp_motor_hp` | float | HP | Potencia del motor (60-300) |
| `esp_motor_voltage_v` | float | V | Voltaje nominal (1000-3500) |
| `esp_motor_amperage_a` | float | A | Corriente nominal (20-90) |
| `esp_vsd_installed` | bool | - | VSD instalado (true/false) |
| `esp_vsd_nominal_hz` | float | Hz | Frecuencia nominal VSD |

#### SRP

| Atributo | Tipo | Unidad | Descripcion |
|----------|------|--------|-------------|
| `srp_unit_type` | str | - | Tipo de unidad ("conventional") |
| `srp_beam_load_capacity_lb` | float | lb | Capacidad de carga del balancin |
| `srp_stroke_length_in` | float | in | Longitud de carrera (100-168) |
| `srp_max_spm` | float | SPM | SPM maximo |
| `srp_prime_mover_hp` | float | HP | Potencia del motor (30-75) |
| `srp_pump_bore_in` | float | in | Diametro de la bomba (1.5-2.5) |
| `srp_rod_material` | str | - | Material de las varillas ("grade_D") |

#### PCP

| Atributo | Tipo | Unidad | Descripcion |
|----------|------|--------|-------------|
| `pcp_pump_geometry` | str | - | Geometria de la bomba ("2-3 lobe") |
| `pcp_pump_stages` | int | - | Etapas del estator (2-5) |
| `pcp_max_rate_bpd` | float | BPD | Tasa maxima |
| `pcp_max_differential_psi` | float | PSI | Diferencial maximo |
| `pcp_elastomer_type` | str | - | Tipo de elastomero ("NBR") |
| `pcp_drive_type` | str | - | Tipo de drive ("surface_drive") |
| `pcp_max_rpm` | float | RPM | Velocidad maxima |
| `pcp_max_torque_ftlb` | float | ft-lb | Torque maximo (2000-5000) |
| `pcp_motor_hp` | float | HP | Potencia del motor (20-100) |

#### Gas Lift

| Atributo | Tipo | Unidad | Descripcion |
|----------|------|--------|-------------|
| `gl_num_mandrels` | int | - | Numero de mandriles (4-7) |
| `gl_operating_valve_depth_ft` | float | ft | Profundidad de valvula operativa |
| `gl_valve_port_size_64ths` | int | 1/64" | Tamano del puerto de la valvula |
| `gl_optimal_injection_mscfd` | float | MSCFD | Tasa de inyeccion optima |
| `gl_max_injection_mscfd` | float | MSCFD | Tasa de inyeccion maxima |
| `gl_injection_pressure_psi` | float | PSI | Presion de inyeccion |

### 7.5 Optimizacion (`opt_*`) - Actualmente vacios/cero

Estos atributos son llenados por el servicio de optimizacion (aun no activo).
Todos estan inicializados con valores por defecto (0, "").

| Atributo | Tipo | Descripcion |
|----------|------|-------------|
| `opt_status` | str | Estado de optimizacion |
| `opt_last_run` | str | Ultima ejecucion |
| `opt_current_operating_point_bpd` | float | Punto de operacion actual |
| `opt_recommended_rate_bpd` | float | Tasa recomendada |
| `opt_potential_gain_bpd` | float | Ganancia potencial |
| `opt_potential_gain_percent` | float | Ganancia potencial (%) |
| `opt_recommended_action` | str | Accion recomendada |
| `opt_efficiency_percent` | float | Eficiencia optimizada |
| `opt_specific_energy_kwh_bbl` | float | Energia especifica |
| `opt_well_health_score` | float | Score de salud del pozo (0-100) |
| `opt_decline_rate_monthly_percent` | float | Tasa de declive mensual |
| `opt_cluster_id` | str | ID de cluster |
| `opt_similar_wells` | str | Pozos similares (JSON) |

> **NOTA:** Cuando el servicio de optimizacion se active, estos atributos se
> actualizaran periodicamente con recomendaciones basadas en modelos analiticos.

---

## 8. Alarmas Operativas

La cadena de reglas "Atilax - Alarmas Operativas" genera las siguientes alarmas:

### Tipos de Alarma Configurados

| Tipo de Alarma | Severidad | Condicion de Creacion | Condicion de Limpieza |
|----------------|-----------|----------------------|----------------------|
| `HIGH_TEMPERATURE` | MAJOR | `motor_temperature_f > umbral` (def: 250 F) | `motor_temperature_f <= umbral * 0.95` |
| `LOW_INTAKE_PRESSURE` | MAJOR | `intake_pressure_psi < umbral` (def: 100 PSI) | `intake_pressure_psi >= umbral * 1.05` |
| `HIGH_VIBRATION` | CRITICAL | `vibration_ips > umbral` (def: 5 IPS) | `vibration_ips <= umbral * 0.8` |
| `PUMP_OFF_DETECTED` | CRITICAL | `frequency_hz == 0` o `motor_current_a < 0.5` | `frequency_hz > 5` y `motor_current_a > 1` |
| `LOW_EFFICIENCY` | MINOR | `pump_efficiency_pct < umbral` (def: 50%) | `pump_efficiency_pct >= umbral * 1.1` |
| `HIGH_MOTOR_CURRENT` | MAJOR | `motor_current_a > umbral` (def: 200 A) | `motor_current_a <= umbral * 0.9` |
| `COMMUNICATION_LOSS` | MAJOR | Evento `INACTIVITY_EVENT` | Evento `ACTIVITY_EVENT` |

### Umbrales Configurables (Shared Attributes)

Los umbrales se configuran como **shared attributes** en el asset del pozo:

| Atributo (shared) | Default | Descripcion |
|--------------------|---------|-------------|
| `alarm_high_temperature_f` | 250 | Umbral alta temperatura motor |
| `alarm_low_intake_pressure_psi` | 100 | Umbral baja presion intake |
| `alarm_high_vibration_ips` | 5 | Umbral alta vibracion |
| `alarm_low_efficiency_pct` | 50 | Umbral baja eficiencia |
| `alarm_high_current_a` | 200 | Umbral alta corriente |
| `alarm_low_frequency_hz` | - | Umbral baja frecuencia |
| `alarm_high_injection_rate_mscfd` | - | Umbral alta inyeccion GL |
| `alarm_comm_timeout_min` | - | Timeout comunicacion |

### Propagacion de Alarmas

Todas las alarmas se propagan al propietario (owner) del asset.
Las alarmas `HIGH_VIBRATION` y `PUMP_OFF_DETECTED` tambien se propagan al tenant.

Para mostrar alarmas en un dashboard:
- Widget: **Alarms table**
- Datasource: Tipo `Entity` con el asset del pozo, macolla o campo
- Filtrar por alarm type, severity, o status segun se necesite

---

## 9. Datos de Ubicacion (Mapas)

**IMPORTANTE: Actualmente NO existen atributos de ubicacion (latitude, longitude)
en ninguna entidad (pozo, macolla o campo).**

Para utilizar widgets de mapa (OpenStreetMap, Google Maps, Image Map) en dashboards:

### Opcion 1: Agregar atributos manualmente via API

```
POST /api/plugins/telemetry/ASSET/{assetId}/attributes/SERVER_SCOPE
Content-Type: application/json
X-Authorization: Bearer {token}

{
  "latitude": 10.123,
  "longitude": -71.456
}
```

### Opcion 2: Agregar atributos desde la interfaz

1. Ir a la entidad (asset del pozo, macolla o campo)
2. Tab "Attributes" -> "Server attributes"
3. Agregar `latitude` (float) y `longitude` (float)

### Coordenadas de Referencia por Campo

| Campo | Latitud Aprox. | Longitud Aprox. |
|-------|----------------|-----------------|
| Campo Boscan | 10.35 | -71.90 |
| Campo Cerro Negro | 8.50 | -63.50 |
| Campo Anaco | 9.43 | -64.47 |

---

## 10. Cadenas de Reglas (Rule Chains)

El sistema tiene 5 cadenas de reglas disponibles en `/rules/`:

| Archivo | Nombre | Funcion |
|---------|--------|---------|
| `01_ingesta_normalizacion.json` | Atilax - Ingesta y Normalizacion | Recibe telemetria cruda, valida, normaliza |
| `02_propagacion_device_asset.json` | Atilax - Propagacion Device->Asset | Filtra metricas y las copia al asset padre |
| `03_alarmas_operativas.json` | Atilax - Alarmas Operativas | Evalua umbrales y genera alarmas |
| `04_publicacion_kafka.json` | Atilax - Publicacion Kafka | Publica telemetria a Kafka para servicios externos |
| `05_recepcion_resultados.json` | Atilax - Recepcion Resultados | Recibe resultados de optimizacion y los guarda como atributos |

### Flujo de Datos

```
RTU Device
    |
    v
[01] Ingesta y Normalizacion
    |
    +---> [02] Propagacion Device->Asset ---> Asset del Pozo (telemetria filtrada)
    |
    +---> [03] Alarmas Operativas ---> Alarmas en Asset del Pozo
    |
    +---> [04] Publicacion Kafka ---> Kafka Topic
                                          |
                                          v
                                   Servicio Optimizacion
                                          |
                                          v
                                   [05] Recepcion Resultados ---> opt_* attributes
```

### Claves del Filtro de Propagacion (Rule Chain 02)

El nodo "Filtrar Metricas Propagacion" define exactamente que claves se copian al asset:

**Comunes a todos:**
`tubing_pressure_psi`, `casing_pressure_psi`, `wellhead_temperature_f`, `flow_rate_bpd`, `motor_power_kw`

**ESP:**
`frequency_hz`, `motor_current_a`, `motor_voltage_v`, `motor_temperature_f`, `intake_pressure_psi`, `discharge_pressure_psi`, `vibration_ips`

**SRP:**
`spm`, `load_lb`, `pump_fillage_pct`, `motor_current_a`

**Gas Lift:**
`injection_rate_mscfd`, `injection_pressure_psi`

**PCP:**
`speed_rpm`, `motor_torque_ftlb`, `motor_current_a`, `motor_temperature_f`

> **NOTA:** Las claves de Gas Lift en el filtro (`injection_rate_mscfd`, `injection_pressure_psi`)
> no coinciden exactamente con las claves del simulador (`gl_injection_rate_mscfd`,
> `gl_injection_pressure_psi`). Esto significa que estas claves NO se propagaran
> al asset a menos que se modifique el simulador o la Rule Chain para usar nombres consistentes.

---

## 11. Dashboards Existentes

### Dashboard de Produccion

| Dashboard | ID | Estados |
|-----------|----|---------|
| Atilax - Campo Petrolero | `9dfd1110-054b-11f1-8dfb-fb2fc7314bd7` | 2 estados |

### Plantillas de Referencia (en `/dash_plantillas/`)

| Archivo | Widgets | Uso de Referencia |
|---------|---------|-------------------|
| `mine_site_monitoring.json` | 23 | Arquitectura multi-nivel, navegacion por estados |
| `fuel_level_monitoring.json` | 13 | Filtros de entidad, entity alias avanzados |
| `temperature_&_humidity.json` | 9 | Widgets de series temporales, gauges |
| `smart_office.json` | 47 | Dashboard complejo, multiples layouts |

### Dashboards de Diseno (en `/dashboard/`)

| Archivo | Descripcion |
|---------|-------------|
| `01_dashboard_campo.json` | Vista de campo (nivel mas alto) |
| `02_dashboard_macolla.json` | Vista de macolla |
| `03_dashboard_pozo_individual.json` | Vista detallada de pozo |
| `04_dashboard_optimizacion.json` | Vista de resultados de optimizacion |
| `reference_campo_petrolero.json` | Dashboard de referencia |

---

## 12. Guia Rapida: Datasources para Widgets

### Configuracion de Entity Alias

#### Ver todos los campos
```
Alias Type: Entity list
Entity Type: ASSET
Asset Type: field
```

#### Ver macollas de un campo
```
Alias Type: Entity from relations
Entity: [Campo seleccionado]
Direction: FROM
Max level: 1
Relation type: Contains
Entity type: ASSET
```

#### Ver pozos de una macolla
```
Alias Type: Entity from relations
Entity: [Macolla seleccionada]
Direction: FROM
Max level: 1
Relation type: Contains
Entity type: ASSET
```

#### Ver RTU de un pozo
```
Alias Type: Entity from relations
Entity: [Pozo seleccionado]
Direction: FROM
Max level: 1
Relation type: Contains
Entity type: DEVICE
```

#### Filtrar pozos por tipo de levantamiento
```
Alias Type: Entity list
Entity Type: ASSET
Asset type: well
Key filter:
  - Key: lift_type
  - Value type: String
  - Operation: Equal
  - Value: "ESP" (o "SRP", "PCP", "gas_lift")
```

#### Todos los dispositivos de un tipo
```
Alias Type: Entity list
Entity Type: DEVICE
Device type: rtu_esp (o rtu_srp, rtu_pcp, rtu_gaslift)
```

### Configuracion de Timeseries Widgets

Para widgets de series de tiempo (charts, gauges):

1. **Datasource type:** Entity
2. **Entity alias:** Segun corresponda (ver arriba)
3. **Data key:** La clave de telemetria (ej: `flow_rate_bpd`)
4. **Key type:** Timeseries

### Configuracion de Attributes Widgets

Para widgets que muestran atributos (tablas, labels):

1. **Datasource type:** Entity
2. **Entity alias:** Segun corresponda
3. **Data key:** El atributo (ej: `reservoir_pressure_psi`)
4. **Key type:** Attributes -> Server attributes

### Patron de Navegacion entre Estados del Dashboard

Para dashboards multi-nivel (Campo -> Macolla -> Pozo):

1. Crear **estados** del dashboard: `campo`, `macolla`, `pozo`
2. En cada tabla/lista, configurar **accion de click en fila**:
   - Action: Navigate to new dashboard state
   - State: el estado destino
   - Parameters: `entityId` y `entityName` de la entidad seleccionada
3. En el estado destino, usar **Entity alias** de tipo `Entity from dashboard state`

---

## 13. Referencia de Unidades

| Simbolo | Unidad Completa | Descripcion |
|---------|-----------------|-------------|
| BPD | Barriles por dia | Tasa de flujo de liquido |
| PSI | Libras por pulgada cuadrada | Presion |
| F | Grados Fahrenheit | Temperatura |
| A | Amperios | Corriente electrica |
| V | Voltios | Voltaje electrico |
| kW | Kilovatios | Potencia electrica |
| HP | Caballos de fuerza | Potencia mecanica |
| Hz | Hertz | Frecuencia |
| RPM | Revoluciones por minuto | Velocidad rotacional |
| SPM | Golpes por minuto (Strokes per minute) | Velocidad de bombeo mecanico |
| IPS | Pulgadas por segundo | Vibracion |
| lb | Libras | Carga / Peso |
| ft-lb | Pie-libra | Torque |
| ft | Pies | Profundidad / Longitud |
| in | Pulgadas | Diametro |
| cP | Centipoise | Viscosidad |
| API | Grados API | Gravedad del crudo |
| SCF/STB | Pies cubicos estandar por barril | Relacion gas-petroleo |
| MSCFD | Miles de pies cubicos estandar por dia | Tasa de inyeccion de gas |
| mohm | Megaohmios | Resistencia de aislamiento |
| AWG | American Wire Gauge | Calibre de cable |
| % | Porcentaje | Eficiencia, corte de agua, llenado |

---

## Notas Finales

### Convencion de Nombres de Pozos
Formato: `{CAMPO_2LETRAS}-{MACOLLA}-{NUMERO_3DIGITOS}`
Ejemplo: `CA-MAC-ANA-01-003` (Campo Anaco, Macolla ANA-01, Pozo 003)

### Convencion de Nombres de RTU
Formato: `RTU-{NOMBRE_POZO}`
Ejemplo: `RTU-CA-MAC-ANA-01-003`

### Convencion de Nombres de Facilidades
Formato: `{TIPO}-{MACOLLA}-{NUMERO}`
Ejemplo: `SEPARATOR-MAC-BOS-01-01`

### Frecuencia de Telemetria
- Modo tiempo real: cada 30 segundos (configurable)
- Aceleracion de tiempo: 60x (1 minuto real = 1 hora simulada)
- Datos historicos: 365 dias, 48 muestras/dia

### Escenarios de Operacion Disponibles
El simulador puede ejecutar los siguientes escenarios que afectan la telemetria:

| Escenario | Descripcion |
|-----------|-------------|
| `normal_operation` | Operacion normal con ruido gaussiano |
| `pump_degradation` | Degradacion gradual de la bomba |
| `gas_interference` | Interferencia por gas en la bomba |
| `water_breakthrough` | Irrupcion de agua en el pozo |
| `casing_heading` | Oscilaciones de presion en casing (Gas Lift) |
| `electrical_issues` | Problemas electricos en el motor |
| `well_loading` | Carga excesiva del pozo |

### Tipos de Anomalias Inyectadas
Con probabilidad de 2% por pozo por dia, se inyectan:
- `pump_degradation` - Degradacion de bomba
- `sensor_drift` - Deriva de sensores
- `gas_interference` - Interferencia por gas
- `electrical_fluctuation` - Fluctuacion electrica
- `water_breakthrough` - Irrupcion de agua
- `sand_production` - Produccion de arena
- `casing_heading` - Heading de casing
- `stuck_sensor` - Sensor atascado
