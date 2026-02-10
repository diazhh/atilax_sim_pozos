# Prompts para Proyecto Atilax - Optimización de Producción Petrolera

---

## PROMPT 1: Claude Code — Simulador de Datos Multi-Pozo para ThingsBoard

```
Eres un ingeniero de software especializado en IoT industrial y el sector petrolero venezolano. Vas a construir un simulador completo en Python que genere datos realistas de pozos petroleros, macollas y campos, y los registre como dispositivos y assets en una instancia de ThingsBoard PE llamada "Atilax".

## CONTEXTO DEL PROYECTO

Atilax es una plataforma de monitoreo y optimización de producción petrolera construida sobre ThingsBoard PE. Necesitamos poblarla con datos simulados realistas para desarrollo, pruebas y demos. Los datos deben representar fielmente la operación de campos petroleros venezolanos, incluyendo crudo pesado y extrapesado de la Faja del Orinoco (6-12°API), crudo medio del Lago de Maracaibo (18-26°API) y crudo liviano del oriente (28-36°API).

## ARQUITECTURA DE ENTIDADES EN THINGSBOARD

La jerarquía de entidades es estricta y debe respetarse:

### Assets (entidades lógicas de negocio):
- **Campo Petrolero** (Asset type: "field") → Contiene macollas
- **Macolla / Estación** (Asset type: "macolla") → Contiene pozos y facilidades
- **Pozo** (Asset type: "well") → Entidad central de optimización
- **Facilidades de Superficie** (Asset type: "facility") → Separadores, compresores, tanques

### Devices (fuentes de datos físicas):
- **RTU/PLC del pozo** (Device type según levantamiento: "rtu_esp", "rtu_srp", "rtu_gaslift", "rtu_pcp") → Envía telemetría en tiempo real
- **Sensor de fondo** (Device type: "downhole_gauge") → Presión y temperatura de fondo (solo en algunos pozos ESP)
- **Medidor multifásico** (Device type: "multiphase_meter") → Tasas de flujo (solo en algunos pozos)
- **Gateway IoT** (Device type: "iot_gateway") → Un gateway por macolla

### Relaciones:
- Campo —[Contains]→ Macolla
- Macolla —[Contains]→ Pozo
- Macolla —[Contains]→ Facilidad
- Pozo —[Contains]→ RTU (y opcionalmente downhole_gauge, multiphase_meter)
- Macolla —[Contains]→ Gateway
- Pozo —[Uses]→ Facilidad (ej: pozo usa separador X)

## ESTRUCTURA DEL SIMULADOR

```
well-simulator/
├── main.py                      # Entry point, CLI con argparse
├── config/
│   ├── default_config.yaml      # Configuración por defecto
│   ├── field_templates/
│   │   ├── faja_orinoco.yaml    # Template campo Faja (extrapesado, PCP/ESP)
│   │   ├── lago_maracaibo.yaml  # Template campo Lago (pesado, SRP/GL)
│   │   └── oriente_liviano.yaml # Template campo oriente (liviano, ESP/GL)
│   └── well_profiles/
│       ├── esp_heavy.yaml       # Perfil pozo ESP crudo pesado
│       ├── esp_extraheavy.yaml  # Perfil pozo ESP crudo extrapesado
│       ├── srp_heavy.yaml       # Perfil pozo bombeo mecánico
│       ├── gaslift_medium.yaml  # Perfil pozo gas lift crudo medio
│       └── pcp_extraheavy.yaml  # Perfil pozo PCP Faja
├── tb_client/
│   ├── __init__.py
│   ├── api_client.py            # Cliente REST API de ThingsBoard
│   ├── entity_creator.py        # Crea assets, devices, relaciones
│   └── telemetry_sender.py      # Envía telemetría por MQTT o REST
├── models/
│   ├── __init__.py
│   ├── field_model.py           # Modelo de campo petrolero
│   ├── macolla_model.py         # Modelo de macolla
│   ├── well_model.py            # Modelo base de pozo
│   ├── reservoir_model.py       # Modelo simplificado de yacimiento (IPR, presión)
│   ├── fluid_model.py           # Modelo PVT simplificado
│   ├── esp_model.py             # Modelo de bomba ESP (curvas, eficiencia, fallas)
│   ├── srp_model.py             # Modelo de bombeo mecánico (cartas, llenado)
│   ├── gaslift_model.py         # Modelo de gas lift (GLPC, casing heading)
│   └── pcp_model.py             # Modelo de PCP (torque, RPM, eficiencia)
├── generators/
│   ├── __init__.py
│   ├── telemetry_generator.py   # Genera datos de telemetría con ruido realista
│   ├── event_generator.py       # Genera eventos (workovers, fallas, paros)
│   ├── decline_generator.py     # Genera declinación de producción realista
│   └── anomaly_injector.py      # Inyecta anomalías y condiciones de falla
├── scenarios/
│   ├── __init__.py
│   ├── normal_operation.py      # Operación normal con variabilidad
│   ├── pump_degradation.py      # Degradación progresiva de bomba
│   ├── gas_interference.py      # Interferencia de gas en SRP
│   ├── water_breakthrough.py    # Irrupción de agua
│   ├── casing_heading.py        # Oscilaciones en gas lift
│   ├── electrical_issues.py     # Problemas eléctricos (Venezuela)
│   └── well_loading.py          # Pozo cargándose / dying
└── utils/
    ├── noise.py                 # Generador de ruido gaussiano + outliers
    ├── correlations.py          # Correlaciones PVT (Standing, Vasquez-Beggs)
    └── units.py                 # Conversión de unidades
```

## CONFIGURACIÓN YAML DE EJEMPLO

El archivo de configuración principal define qué se va a simular:

```yaml
# config/default_config.yaml
thingsboard:
  url: "https://atilax.vasteix.com"
  username: "admin@vasteix.com"
  password: "${TB_PASSWORD}"  # Variable de entorno

simulation:
  mode: "realtime"          # "realtime" (continuo) o "historical" (batch)
  historical_days: 365      # Si es historical, cuántos días generar
  realtime_interval_sec: 30 # Si es realtime, intervalo entre muestras
  time_acceleration: 60     # 1 minuto real = 1 hora simulada (para demos)
  seed: 42                  # Reproducibilidad

fields:
  - name: "Campo Boscán"
    template: "lago_maracaibo"
    num_macollas: 3
    wells_per_macolla: [8, 10, 6]  # Distribución por macolla
    lift_distribution:
      SRP: 0.65             # 65% bombeo mecánico
      ESP: 0.20             # 20% ESP
      gas_lift: 0.10        # 10% gas lift
      PCP: 0.05             # 5% PCP
    reservoir:
      pressure_psi: [2200, 3000]    # Rango
      temperature_f: [160, 200]
      api_gravity: [10, 15]
      viscosity_cp: [500, 5000]
      water_cut_range: [0.20, 0.75]
      gor_range: [80, 200]
    production:
      avg_rate_bpd: [200, 1500]
      decline_rate_annual: [0.05, 0.15]

  - name: "Campo Cerro Negro"
    template: "faja_orinoco"
    num_macollas: 2
    wells_per_macolla: [12, 15]
    lift_distribution:
      PCP: 0.55
      ESP: 0.35
      SRP: 0.10
    reservoir:
      pressure_psi: [800, 1500]
      temperature_f: [120, 160]
      api_gravity: [6, 10]
      viscosity_cp: [2000, 12000]
      water_cut_range: [0.10, 0.50]
      gor_range: [50, 120]
    production:
      avg_rate_bpd: [300, 2500]
      decline_rate_annual: [0.03, 0.10]

  - name: "Campo Anaco"
    template: "oriente_liviano"
    num_macollas: 2
    wells_per_macolla: [5, 7]
    lift_distribution:
      gas_lift: 0.50
      ESP: 0.35
      SRP: 0.15
    reservoir:
      pressure_psi: [2500, 4000]
      temperature_f: [200, 280]
      api_gravity: [28, 36]
      viscosity_cp: [1, 10]
      water_cut_range: [0.30, 0.85]
      gor_range: [400, 1500]
    production:
      avg_rate_bpd: [100, 800]
      decline_rate_annual: [0.08, 0.20]

anomalies:
  enabled: true
  probability_per_well_per_day: 0.02   # 2% de probabilidad diaria
  types:
    - pump_degradation      # Degradación gradual
    - sensor_drift          # Sensor descalibrado
    - gas_interference      # Gas en la bomba
    - electrical_fluctuation # Típico Venezuela
    - water_breakthrough    # Irrupción de agua
    - sand_production       # Producción de arena (Faja)
    - casing_heading        # Oscilaciones gas lift
    - stuck_sensor          # Sensor pegado (mismo valor)
```

## TELEMETRÍA POR TIPO DE LEVANTAMIENTO

### ESP (Bombeo Electrosumergible):
```json
{
  "thp_psi": "float, 50-500",
  "chp_psi": "float, 100-800",
  "tht_f": "float, 100-200",
  "intake_pressure_psi": "float, 200-2000",
  "discharge_pressure_psi": "float, 1000-5000",
  "motor_temp_f": "float, 150-350",
  "intake_temp_f": "float, 120-250",
  "motor_current_a": "float, 10-120",
  "motor_voltage_v": "float, 500-4000",
  "motor_power_kw": "float, calculado V*I*sqrt(3)*pf/1000",
  "vsd_frequency_hz": "float, 30-75",
  "vibration_x_ips": "float, 0.01-1.0",
  "vibration_y_ips": "float, 0.01-1.0",
  "insulation_mohm": "float, 0-2000",
  "flow_rate_bpd": "float, calculado del modelo",
  "water_cut_pct": "float, 0-100",
  "gor_scf_stb": "float, según yacimiento"
}
```

### SRP (Bombeo Mecánico):
```json
{
  "thp_psi": "float, 20-200",
  "chp_psi": "float, 50-400",
  "motor_current_a": "float, 10-80",
  "motor_power_kw": "float, 5-50",
  "spm": "float, 3-12",
  "polished_rod_load_max_lb": "float, 5000-25000",
  "polished_rod_load_min_lb": "float, 1000-8000",
  "fluid_level_ft": "float, 500-6000",
  "pump_fillage_pct": "float, 40-100",
  "stroke_counter": "integer, incremental",
  "flow_rate_bpd": "float, calculado",
  "water_cut_pct": "float, 0-100",
  "dynamo_card_surface": "array [[pos,load],...] cada 15-60 min"
}
```

### Gas Lift:
```json
{
  "thp_psi": "float, 80-500",
  "chp_psi": "float, 300-1500",
  "tht_f": "float, 100-200",
  "gl_injection_rate_mscfd": "float, 100-2000",
  "gl_injection_pressure_psi": "float, 500-2000",
  "choke_size_64ths": "integer, 8-64",
  "flow_rate_bpd": "float, calculado",
  "water_cut_pct": "float, 0-100",
  "gor_scf_stb": "float, alto por inyección"
}
```

### PCP (Bombeo de Cavidades Progresivas):
```json
{
  "thp_psi": "float, 30-300",
  "chp_psi": "float, 50-500",
  "drive_torque_ftlb": "float, 200-5000",
  "drive_rpm": "float, 50-500",
  "motor_current_a": "float, 10-60",
  "motor_power_kw": "float, 5-80",
  "intake_pressure_psi": "float, 100-1000 (si hay sensor)",
  "flow_rate_bpd": "float, calculado",
  "water_cut_pct": "float, 0-100",
  "sand_pct": "float, 0-5 (Faja)"
}
```

## ATRIBUTOS ESTÁTICOS DEL POZO (SERVER ATTRIBUTES)

Cada Asset de tipo "well" debe tener estos server attributes al crearse:

### Datos del yacimiento:
reservoir_pressure_psi, reservoir_temperature_f, bubble_point_psi, api_gravity, gor_scf_stb, water_cut_initial_pct, oil_viscosity_cp, bo_factor, productivity_index_bpd_psi, ipr_model ("vogel" | "fetkovich" | "darcy"), ipr_qmax_bpd, drive_mechanism, pvt_source, last_buildup_date

### Datos mecánicos:
total_depth_md_ft, total_depth_tvd_ft, casing_od_in, casing_id_in, tubing_od_in, tubing_id_in, pump_depth_ft, perforations_top_ft, perforations_bottom_ft, completion_type, deviation_survey (JSON array)

### Configuración de levantamiento (varía por tipo):
lift_type ("ESP"|"SRP"|"gas_lift"|"PCP"), install_date, más todos los parámetros específicos del equipo (etapas ESP, sarta de cabillas SRP, válvulas gas lift, specs PCP).

### Resultados de optimización (inicialmente vacíos):
opt_last_run, opt_current_operating_point_bpd, opt_recommended_rate_bpd, opt_potential_gain_bpd, opt_potential_gain_percent, opt_recommended_action, opt_efficiency_percent, opt_specific_energy_kwh_bbl, opt_well_health_score, opt_status, opt_decline_rate_monthly_percent, opt_cluster_id, opt_similar_wells

## MODELO DE SIMULACIÓN FÍSICO

### Yacimiento:
- Usar IPR de Vogel para yacimientos saturados: q = qmax × [1 - 0.2(Pwf/Pr) - 0.8(Pwf/Pr)²]
- Declinación exponencial/hiperbólica con parámetros de Arps
- Presión de yacimiento declina con producción acumulada (balance de materiales simplificado)
- El water cut debe aumentar gradualmente con el tiempo

### Generación de ruido:
- Ruido gaussiano base: ±1-3% del valor nominal para presiones y temperaturas
- Ruido mayor en tasas de flujo: ±5-10%
- Outliers ocasionales: 0.5% de las muestras con desviación >3σ
- Ciclos diurnos en temperatura ambiente que afectan temperaturas de cabezal
- Correlación entre variables: si sube corriente ESP, sube temperatura motor

### Escenarios de anomalía:
- **Degradación de bomba**: eficiencia volumétrica baja gradualmente (0.1%/día), corriente sube, producción baja
- **Interferencia de gas**: llenado de bomba irregular, cartas dinamométricas con forma característica, producción errática
- **Falla eléctrica venezolana**: caída de voltaje súbita 10-20%, variación de frecuencia, paros y arranques
- **Irrupción de agua**: BSW sube rápidamente en 2-4 semanas, producción de petróleo baja
- **Producción de arena**: torque PCP sube, vibración sube, desgaste acelerado
- **Casing heading en gas lift**: oscilaciones senoidales en presión con período 5-30 minutos
- **Sensor pegado**: un sensor reporta exactamente el mismo valor por horas

## REQUERIMIENTOS FUNCIONALES

1. **CLI completo**:
   - `python main.py create --config config.yaml` → Crea toda la estructura en TB (assets, devices, relaciones, attributes)
   - `python main.py simulate --config config.yaml --mode realtime` → Inicia simulación continua
   - `python main.py simulate --config config.yaml --mode historical --days 365` → Genera 1 año de datos históricos
   - `python main.py delete --config config.yaml` → Limpia todo de TB
   - `python main.py status` → Muestra resumen de entidades creadas

2. **Creación de entidades**: Debe ser idempotente (si ya existe, no duplicar). Debe crear la jerarquía completa con todas las relaciones. Debe asignar Device Profiles adecuados.

3. **Simulación realista**: Variables correlacionadas físicamente. Declinación natural. Eventos aleatorios. Ruido realista. Transitorios al arrancar/parar pozo.

4. **Envío de telemetría**: Por MQTT (preferido para tiempo real) o REST API (para históricos batch). Respetar rate limits de TB. Manejar reconexiones.

5. **Logging**: Log detallado de todo lo que se crea y simula. Archivo de log rotativo.

6. **Reproducibilidad**: Mismo seed = mismos datos generados.

## CONEXIÓN A THINGSBOARD

- URL base: Configurable en YAML
- Autenticación: JWT via /api/auth/login
- Creación de assets: POST /api/asset
- Creación de devices: POST /api/device
- Relaciones: POST /api/relation
- Attributes: POST /api/plugins/telemetry/{entityType}/{entityId}/attributes/{scope}
- Telemetría: POST /api/plugins/telemetry/{entityType}/{entityId}/timeseries/{scope} (REST) o MQTT v1/devices/me/telemetry
- Device Profiles: Crear o reutilizar existentes

## INSTRUCCIONES ADICIONALES

- Usar Python 3.10+ con tipado completo (type hints)
- Dependencias: paho-mqtt, requests, pyyaml, numpy, scipy
- NO usar frameworks pesados innecesarios
- Código limpio, documentado, con docstrings
- Tests unitarios para los modelos físicos
- README.md completo con instrucciones de instalación y uso
- Docker Compose opcional para correr el simulador como servicio
- El simulador debe poder correr como un servicio persistente que genere datos continuamente, o ejecutarse una vez para generar históricos
```

---

## PROMPT 2: Claude Code — Servicio de Optimización de Producción

```
Eres un ingeniero de software senior especializado en optimización de producción petrolera e integración con plataformas IoT industriales. Vas a construir el servicio completo de optimización de producción que se integra con ThingsBoard PE (instancia llamada "Atilax") para una consultora de automatización industrial venezolana llamada VASTEIX.

## CONTEXTO

Atilax (ThingsBoard PE) ya recibe telemetría en tiempo real de pozos petroleros con diferentes tipos de levantamiento artificial (ESP, bombeo mecánico/SRP, gas lift, PCP). Los pozos están modelados como Assets con sus datos estáticos en server attributes. Los RTU/PLC son Devices que envían telemetría. El servicio de optimización debe consumir estos datos, ejecutar análisis y cálculos de ingeniería de producción, y devolver los resultados a ThingsBoard como atributos y alarmas.

## ARQUITECTURA GENERAL

```
ThingsBoard PE (Atilax)
    ↕ (MQTT + REST API)
Kafka (Message Broker)
    ↕
Optimization Service (Python + FastAPI)
    ├── Ingesta y Buffer (Kafka Consumer)
    ├── Data Store (PostgreSQL + Redis)
    ├── Motor de Cálculos Clásicos
    ├── Motor de ML/AI
    ├── Scheduler (tareas programadas)
    ├── API REST (consultas, configuración, dashboards custom)
    └── Publicador de Resultados (Kafka Producer → TB)
```

## ESTRUCTURA DEL PROYECTO

```
optimization-service/
├── docker-compose.yaml          # Servicio + Kafka + Zookeeper + PostgreSQL + Redis
├── Dockerfile
├── requirements.txt
├── alembic/                     # Migraciones de base de datos
│   └── versions/
├── main.py                      # FastAPI application entry point
├── config/
│   ├── settings.py              # Pydantic Settings (env vars)
│   ├── logging_config.py
│   └── well_configs/            # Configuraciones específicas por pozo/campo
│
├── api/                         # REST API endpoints
│   ├── __init__.py
│   ├── router.py
│   ├── endpoints/
│   │   ├── wells.py             # CRUD y consultas de pozos
│   │   ├── optimization.py      # Trigger manual, resultados, historial
│   │   ├── forecasts.py         # Pronósticos DCA y ML
│   │   ├── clusters.py          # Clusters de pozos similares
│   │   ├── field.py             # Optimización de campo completo
│   │   ├── alarms.py            # Gestión de alarmas de optimización
│   │   └── health.py            # Health check del servicio
│   └── schemas/                 # Pydantic models para request/response
│       ├── well_schemas.py
│       ├── optimization_schemas.py
│       └── forecast_schemas.py
│
├── ingestion/                   # Ingesta de datos desde TB via Kafka
│   ├── __init__.py
│   ├── kafka_consumer.py        # Consumer de telemetría
│   ├── tb_listener.py           # Listener MQTT directo a TB (alternativa)
│   ├── data_validator.py        # Validación y limpieza de datos entrantes
│   ├── data_enricher.py         # Enriquece con atributos estáticos del pozo
│   └── buffer_manager.py        # Gestión de buffer en Redis
│
├── tb_client/                   # Cliente ThingsBoard
│   ├── __init__.py
│   ├── rest_client.py           # REST API client (auth, assets, telemetry, attributes, alarms)
│   ├── mqtt_client.py           # MQTT publisher para telemetría de resultados
│   └── entity_manager.py        # Cache de entidades TB (assets, devices, relaciones)
│
├── store/                       # Persistencia
│   ├── __init__.py
│   ├── database.py              # SQLAlchemy engine + session
│   ├── models.py                # ORM models
│   ├── redis_cache.py           # Redis para buffer y cache
│   └── repositories/
│       ├── well_repo.py
│       ├── telemetry_repo.py
│       ├── optimization_repo.py
│       └── forecast_repo.py
│
├── engines/                     # Motores de cálculo de ingeniería de producción
│   ├── __init__.py
│   ├── base_engine.py           # Clase base para todos los engines
│   ├── nodal_analysis.py        # Análisis Nodal: IPR (Vogel, Fetkovich, Darcy) + VLP
│   ├── esp_optimizer.py         # Optimización ESP: punto operativo, frecuencia, eficiencia
│   ├── srp_optimizer.py         # Optimización SRP: velocidad, diagnóstico carta dinamo
│   ├── gaslift_optimizer.py     # Optimización Gas Lift: GLPC, asignación gas, casing heading
│   ├── pcp_optimizer.py         # Optimización PCP: RPM, torque, eficiencia
│   ├── decline_analysis.py      # Decline Curve Analysis: Arps (exp, hyp, harm)
│   ├── field_optimizer.py       # Optimización multi-pozo: GA/PSO asignación recursos
│   ├── well_health.py           # Scoring de salud del pozo (ponderado multi-variable)
│   └── energy_optimizer.py      # Optimización energética: kWh/bbl
│
├── ml/                          # Modelos de Machine Learning
│   ├── __init__.py
│   ├── base_model.py            # Clase base para modelos ML
│   ├── production_forecast.py   # Pronóstico producción: LSTM, XGBoost
│   ├── anomaly_detector.py      # Detección anomalías: Isolation Forest, Autoencoder
│   ├── esp_failure_predictor.py # Predicción fallas ESP: XGBoost + features temporales
│   ├── dynamo_classifier.py     # Clasificación cartas dinamo: CNN (si hay datos)
│   ├── virtual_flow_meter.py    # VFM: modelo híbrido física+ML
│   ├── well_clustering.py       # Clustering: K-means, DBSCAN, UMAP+HDBSCAN
│   ├── decline_ml.py            # DCA mejorado con ML: XGBoost predicción parámetros Arps
│   └── training/
│       ├── train_pipeline.py    # Pipeline genérico de entrenamiento
│       ├── feature_engineering.py
│       └── model_registry.py    # Versionado de modelos (MLflow-lite)
│
├── schedulers/                  # Tareas programadas
│   ├── __init__.py
│   ├── scheduler_manager.py     # APScheduler o Celery Beat
│   ├── realtime_tasks.py        # Cada 5-15 min: anomalías, eficiencia instantánea
│   ├── hourly_tasks.py          # Cada hora: análisis nodal, punto operativo
│   ├── daily_tasks.py           # Diario: DCA, KPIs, recomendaciones, well health score
│   ├── weekly_tasks.py          # Semanal: clustering, benchmarking, reentrenamiento ML
│   └── monthly_tasks.py         # Mensual: reportes, recálculo EUR, revisión de modelos
│
├── publishers/                  # Publicación de resultados a TB
│   ├── __init__.py
│   ├── attribute_publisher.py   # Escribe server attributes con resultados
│   ├── alarm_publisher.py       # Genera alarmas de optimización
│   ├── telemetry_publisher.py   # Publica métricas calculadas como telemetría
│   └── notification_publisher.py # Notificaciones por email/webhook
│
├── utils/
│   ├── __init__.py
│   ├── units.py                 # Conversión de unidades oilfield
│   ├── correlations.py          # Correlaciones PVT: Standing, Vasquez-Beggs, Beggs-Robinson
│   ├── fluid_properties.py      # Calculadora de propiedades de fluido
│   ├── multiphase_flow.py       # Correlaciones flujo multifásico simplificadas
│   └── statistics.py            # Estadísticas y métricas
│
├── models/                      # Modelos ML serializados
│   └── .gitkeep
│
└── tests/
    ├── test_engines/
    ├── test_ml/
    ├── test_ingestion/
    └── test_api/
```

## DETALLE DE CADA COMPONENTE

### 1. Ingesta via Kafka

ThingsBoard PE puede publicar telemetría a Kafka mediante una Integration o Rule Chain con nodo "Kafka".
El servicio consume de topics organizados por tipo:

```
Topics Kafka:
- atilax.telemetry.esp        → Telemetría de pozos ESP
- atilax.telemetry.srp        → Telemetría de pozos SRP
- atilax.telemetry.gaslift    → Telemetría de pozos Gas Lift
- atilax.telemetry.pcp        → Telemetría de pozos PCP
- atilax.events.alarms        → Alarmas generadas en TB
- atilax.events.lifecycle      → Eventos connect/disconnect de devices
- atilax.optimization.results → Resultados de optimización (producer)
```

El consumer debe:
- Deserializar mensajes (JSON)
- Validar rangos físicos (rechazar datos fuera de rango)
- Enriquecer con metadata del pozo (desde cache Redis)
- Almacenar en buffer temporal (Redis, ventana deslizante de 24h)
- Persistir en PostgreSQL (tabla de telemetría particionada por tiempo)
- Trigger engines de tiempo real cuando hay datos suficientes

### 2. Motores de Cálculo Clásicos

#### Análisis Nodal (nodal_analysis.py):
- IPR Vogel: q = qmax × [1 - 0.2(Pwf/Pr) - 0.8(Pwf/Pr)²]
- IPR Fetkovich: q = C × (Pr² - Pwf²)^n
- IPR Darcy (lineal): q = J × (Pr - Pwf)
- VLP simplificada usando correlaciones de gradiente de presión (Hagedorn-Brown o Beggs-Brill simplificado)
- Intersección IPR-VLP para encontrar punto operativo
- Comparación punto actual vs óptimo
- Input: reservoir_pressure, productivity_index, ipr_model, qmax, pump_depth, tubing geometry, PVT, presiones actuales
- Output: operating_point_bpd, optimal_point_bpd, pwf_current, pwf_optimal, curves (IPR y VLP como arrays para graficar)

#### ESP Optimizer (esp_optimizer.py):
- Calcular head requerido vs head disponible a frecuencia actual
- Eficiencia volumétrica: caudal real / caudal teórico
- Posición relativa al BEP usando leyes de afinidad: Q∝N, H∝N², P∝N³
- Frecuencia óptima para operar en rango 80-110% del BEP
- Consumo específico de energía (kWh/bbl)
- Detección de operación fuera de rango (upthrust, downthrust)
- Input: pump curves (del atributo), current freq/rate/pressures, fluid properties
- Output: efficiency_pct, operating_pct_bep, recommended_freq_hz, energy_kwh_bbl, status

#### SRP Optimizer (srp_optimizer.py):
- Análisis de carta dinamométrica: identificar llenado, fugas, interferencia gas
- Cálculo de llenado de bomba (fillage) desde carta de superficie
- Velocidad óptima (SPM) que maximiza producción sin golpe de fluido
- Contrabalanceo óptimo
- Si no hay carta dinamométrica: usar método simplificado con nivel de fluido y presiones
- Input: dynamo_card (si disponible), spm, stroke_length, rod_string, pump_diameter, fluid_level
- Output: fillage_pct, recommended_spm, pump_status (normal/gas_lock/fluid_pound/leak), predicted_rate

#### Gas Lift Optimizer (gaslift_optimizer.py):
- Curva GLPC (Gas Lift Performance Curve): producción vs tasa inyección gas
- Punto óptimo técnico (máxima producción) y económico (máximo beneficio)
- Detección de casing heading (análisis frecuencia de oscilaciones en presión)
- Asignación óptima de gas entre pozos de la macolla (método de pendiente igual / programación lineal)
- Input: IPR, gas injection rate, injection pressure, tubing/casing geometry, valve survey
- Output: optimal_gl_rate, max_production_rate, economic_rate, heading_detected, recommended_choke

#### PCP Optimizer (pcp_optimizer.py):
- Eficiencia volumétrica: caudal real / (desplazamiento × RPM)
- Torque vs RPM: verificar que no exceda límites
- RPM óptima balanceando producción vs desgaste
- Detección de desgaste por tendencia de eficiencia
- Input: rpm, torque, flow_rate, pump_specs (displacement, max_dp, max_rpm)
- Output: efficiency_pct, recommended_rpm, wear_indicator, status

#### Decline Analysis (decline_analysis.py):
- Arps exponencial: q(t) = qi × exp(-Di × t)
- Arps hiperbólica: q(t) = qi / (1 + b × Di × t)^(1/b)
- Arps harmónica: q(t) = qi / (1 + Di × t)
- Ajuste automático de parámetros (qi, Di, b) por mínimos cuadrados
- Selección automática del mejor modelo (AIC/BIC)
- Proyección y cálculo de EUR
- Input: historial de producción (array de fechas + tasas)
- Output: best_model, qi, Di, b, forecast_array, eur_stb, decline_rate_monthly_pct

#### Field Optimizer (field_optimizer.py):
- Optimización multi-pozo con restricciones compartidas
- Para gas lift: asignación óptima de gas disponible entre N pozos
  - Método de pendiente igual (analítico)
  - Algoritmo Genético (GA) para problemas complejos con restricciones no lineales
  - PSO como alternativa
- Para ESP: priorización de frecuencia cuando hay limitación eléctrica
- Restricciones: gas total disponible, capacidad de separación, potencia eléctrica, manejo de agua
- Input: array de pozos con sus modelos individuales + restricciones de campo
- Output: asignación óptima por pozo, producción total optimizada, mejora vs actual

### 3. Motores de ML/AI

#### Production Forecast (production_forecast.py):
- XGBoost para pronóstico a corto plazo (features: últimos 30 días de telemetría + atributos estáticos)
- LSTM para pronóstico a largo plazo (secuencia de 90+ días)
- Features: tasas históricas, presiones, frecuencia/SPM/RPM, water cut, GOR
- Entrenamiento: por cluster de pozos similares (transfer learning intra-cluster)
- Mínimo: 6 meses de datos históricos para entrenar

#### Anomaly Detector (anomaly_detector.py):
- Isolation Forest para detección multivariable
- Reglas de negocio como complemento (no solo ML)
- Detección de sensor pegado (varianza = 0 en ventana)
- Detección de drift (media móvil se aleja de referencia)
- Detección de cambio de régimen (CUSUM, PELT)
- Output: anomaly_score (0-1), anomaly_type, affected_variables, severity

#### ESP Failure Predictor (esp_failure_predictor.py):
- Features: tendencia de corriente, temperatura, vibración, aislamiento en ventana de 30 días
- Modelo: XGBoost clasificador (falla en próximos N días: sí/no)
- Features derivadas: ratio corriente/frecuencia, tendencia de aislamiento, variabilidad de vibración
- Necesita: historial de fallas etiquetado para entrenar (puede comenzar con reglas)

#### Well Clustering (well_clustering.py):
- Features: API, viscosidad, WC, GOR, profundidad, tasa, tipo levantamiento, declinación
- Pipeline: StandardScaler → PCA (si >10 vars) → K-means / UMAP+HDBSCAN
- K óptimo por método del codo + silhouette score
- Actualización semanal
- Output: cluster_id por pozo, cluster_centroids, similar_wells (top 5 por distancia)

### 4. Schedulers

```python
# Frecuencias de ejecución:
REALTIME_INTERVAL = 300      # 5 minutos: anomalías, eficiencia instantánea
HOURLY_INTERVAL = 3600       # 1 hora: análisis nodal, punto operativo, recomendaciones
DAILY_HOUR = 6               # 6 AM: DCA, KPIs diarios, well health score
WEEKLY_DAY = 0               # Lunes: clustering, benchmarking, reentrenamiento
MONTHLY_DAY = 1              # Día 1: reportes, revisión EUR, auditoría de modelos
```

Cada scheduler:
1. Consulta la lista de pozos activos desde cache
2. Para cada pozo, obtiene datos necesarios (buffer Redis + atributos TB)
3. Ejecuta el engine correspondiente
4. Publica resultados a TB (attributes + alarmas)
5. Persiste resultados en PostgreSQL para historial
6. Loguea métricas de ejecución (duración, errores, pozos procesados)

### 5. Publicación de Resultados a ThingsBoard

Los resultados se escriben como **server attributes** en el Asset del pozo:

```python
# Ejemplo de resultados que se publican
optimization_results = {
    "opt_last_run": "2025-02-08T10:30:00Z",
    "opt_status": "suboptimal",               # optimal | suboptimal | critical | unknown
    "opt_current_rate_bpd": 850,
    "opt_recommended_rate_bpd": 1050,
    "opt_potential_gain_bpd": 200,
    "opt_potential_gain_pct": 23.5,
    "opt_recommended_action": "increase_vsd_frequency",
    "opt_recommended_value": 65,               # Hz, SPM, MSCFD según tipo
    "opt_recommended_action_detail": "Incrementar frecuencia VSD de 58 Hz a 65 Hz. Ganancia estimada: +200 BPD.",
    "opt_efficiency_pct": 72,
    "opt_energy_kwh_bbl": 8.5,
    "opt_well_health_score": 68,               # 0-100
    "opt_decline_rate_monthly_pct": 2.1,
    "opt_eur_mstb": 450,
    "opt_days_to_predicted_failure": null,      # null si no aplica
    "opt_failure_probability": 0.12,
    "opt_cluster_id": 3,
    "opt_similar_wells": ["BOS-1207", "BOS-1312"],
    "opt_anomaly_score": 0.15,
    "opt_anomaly_type": null,
    "opt_nodal_ipr_curve": [[0, 2850], [200, 2500], ...],   # Para widget de gráfico
    "opt_nodal_vlp_curve": [[0, 500], [200, 900], ...],
    "opt_nodal_vlp_optimal": [[0, 450], [200, 820], ...],
    "opt_dca_forecast": [["2025-03", 830], ["2025-04", 815], ...],
    "opt_glpc_curve": [[0, 0], [200, 500], [400, 800], ...]  # Solo gas lift
}
```

Las **alarmas de optimización** se generan cuando:
- Pozo opera >20% por debajo de su potencial → WELL_SUBOPTIMAL (WARNING)
- Eficiencia de bomba <55% → PUMP_DEGRADATION (MAJOR)
- Declinación >5%/mes → ACCELERATED_DECLINE (WARNING)
- Probabilidad falla ESP >70% → ESP_FAILURE_PREDICTED (CRITICAL)
- Anomalía detectada con score >0.8 → ANOMALY_DETECTED (WARNING/MAJOR)
- Casing heading detectado → CASING_HEADING (WARNING)
- Pozo candidato a cambio de levantamiento → LIFT_METHOD_REVIEW (INFO)

### 6. API REST (FastAPI)

Endpoints principales:

```
GET  /api/v1/wells                           → Lista pozos con estado de optimización
GET  /api/v1/wells/{well_id}                 → Detalle completo de un pozo
GET  /api/v1/wells/{well_id}/optimization    → Últimos resultados de optimización
GET  /api/v1/wells/{well_id}/forecast        → Pronóstico de producción
GET  /api/v1/wells/{well_id}/nodal           → Curvas IPR/VLP actuales
GET  /api/v1/wells/{well_id}/history         → Historial de optimizaciones
POST /api/v1/wells/{well_id}/optimize        → Trigger manual de optimización
GET  /api/v1/fields/{field_id}/optimization  → Optimización de campo completo
GET  /api/v1/fields/{field_id}/ranking       → Ranking de oportunidades
GET  /api/v1/clusters                        → Clusters actuales
GET  /api/v1/clusters/{cluster_id}/wells     → Pozos en un cluster
POST /api/v1/ml/train/{model_type}           → Trigger entrenamiento de modelo
GET  /api/v1/ml/models                       → Modelos disponibles y estado
GET  /api/v1/health                          → Health check
GET  /api/v1/metrics                         → Métricas del servicio (Prometheus format)
```

### 7. Docker Compose

```yaml
services:
  optimization-service:
    build: .
    ports:
      - "8080:8080"
    environment:
      - TB_URL=https://atilax.vasteix.com
      - TB_USERNAME=admin@vasteix.com
      - TB_PASSWORD=${TB_PASSWORD}
      - KAFKA_BOOTSTRAP=kafka:9092
      - POSTGRES_URL=postgresql://opt:password@postgres:5432/optimization
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - kafka
      - postgres
      - redis

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: optimization
      POSTGRES_USER: opt
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

## CORRELACIONES Y FÓRMULAS CLAVE

### PVT (utils/correlations.py):
- Standing: Pb = 18.2 × [(Rs/γg)^0.83 × 10^(0.00091×T - 0.0125×API) - 1.4]
- Vasquez-Beggs Bo: Bo = 1 + C1×Rs + C2×(T-60)×(API/γg) + C3×Rs²
- Beggs-Robinson viscosidad: μod = 10^(10^(3.0324 - 0.02023×API) / T^1.163) - 1
- Standing GOR: Rs = γg × [(P/18.2 + 1.4) × 10^(0.0125×API - 0.00091×T)]^1.2048

### Leyes de Afinidad ESP:
- Q₂/Q₁ = N₂/N₁
- H₂/H₁ = (N₂/N₁)²
- BHP₂/BHP₁ = (N₂/N₁)³

### Gradiente de presión simplificado:
- dP/dZ = [ρm×g + f×ρm×vm²/(2×d)] / [1 - ρm×vm×vsg/P]
- Para implementación inicial, usar correlación de Hagedorn-Brown tabulada

## REQUERIMIENTOS TÉCNICOS

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 + Alembic
- Confluent Kafka Python
- Redis (aioredis)
- NumPy, SciPy, Pandas
- scikit-learn, XGBoost
- TensorFlow o PyTorch (para LSTM, solo si hay datos suficientes)
- APScheduler o Celery Beat
- Pydantic v2 para validación
- Pytest para testing
- Prometheus client para métricas
- Estructurar código para ser extensible: nuevos engines y modelos ML se agregan sin modificar código existente (strategy pattern)
- Logging estructurado (JSON) con correlation IDs
- Health checks y métricas para cada componente
- Graceful shutdown
- Manejo de errores robusto: un pozo con datos malos NO debe tumbar el procesamiento de los demás
```

---

## PROMPT 3: Claude Cowork — Documentación Técnica de Implementación

```
Eres un documentador técnico experto en plataformas IoT industriales y producción petrolera. Vas a crear la documentación técnica completa de implementación del proyecto "Atilax" — una plataforma de monitoreo y optimización de producción petrolera construida sobre ThingsBoard PE para la empresa VASTEIX.

## TU TAREA

Crear un documento profesional completo (Word/PDF) titulado "Atilax — Guía de Implementación Técnica" que sirva como referencia para el equipo técnico que va a configurar ThingsBoard y desplegar los servicios. El documento debe ser exhaustivo, paso a paso, y no dejar nada a la interpretación.

## ESTRUCTURA DEL DOCUMENTO

### 1. Resumen Ejecutivo
- Qué es Atilax
- Objetivo: pasar de monitoreo puro a optimización de producción
- Componentes: ThingsBoard PE + Servicio de Optimización + Simulador
- Beneficios esperados: 5-20% incremento producción, reducción de fallas, ahorro energético

### 2. Arquitectura General
- Diagrama de arquitectura de alto nivel
- Componentes y sus roles
- Flujos de datos principales
- Protocolos de comunicación (MQTT, REST, Kafka, Modbus/OPC)
- Requisitos de infraestructura (servidores, red, almacenamiento)

### 3. Modelo de Datos en ThingsBoard

#### 3.1 Tipos de Asset (crear en TB → Asset Profiles)
Documentar para cada tipo:
- **field**: nombre, ubicación GPS, operadora, número de macollas, producción total
- **macolla**: nombre, campo padre, número de pozos, facilidades asociadas
- **well**: TODOS los atributos (listar cada server attribute con nombre, tipo de dato, unidad, descripción, ejemplo, si es obligatorio o opcional). Separar por categoría:
  - Identificación (nombre, código PDVSA, estado, tipo levantamiento)
  - Yacimiento (presión, temperatura, API, viscosidad, GOR, WC, IP, modelo IPR, Qmax, Pb, Bo, mecanismo empuje)
  - Mecánica del pozo (profundidades, casings, tubing, perforaciones, survey, completación)
  - Equipo de levantamiento ESP (modelo, etapas, BEP, motor, VSD, cable, fecha instalación)
  - Equipo de levantamiento SRP (unidad, carrera, cabillas, bomba, contrabalanceo)
  - Equipo de levantamiento Gas Lift (tipo, válvulas con profundidad/puerto/tipo, fuente gas)
  - Equipo de levantamiento PCP (modelo rotor/estator, desplazamiento, límites)
  - Resultados de optimización (todos los campos opt_* con descripción)
- **facility**: tipo (separador, tanque, compresor), capacidad, estado

#### 3.2 Tipos de Device (crear en TB → Device Profiles)
Para cada tipo:
- **rtu_esp**: telemetría esperada (cada key con tipo, unidad, rango válido, frecuencia)
- **rtu_srp**: ídem
- **rtu_gaslift**: ídem
- **rtu_pcp**: ídem
- **downhole_gauge**: telemetría de sensor de fondo
- **multiphase_meter**: telemetría de medidor
- **iot_gateway**: metadatos del gateway

Para cada Device Profile, documentar:
- Alarm Rules (qué alarmas configurar, con umbrales, duración, severidad)
- Transport configuration (MQTT topic pattern)
- Provisioning (si aplica)

#### 3.3 Relaciones
Tabla completa: Entidad A → Tipo Relación → Entidad B → Dirección → Descripción

#### 3.4 Shared Attributes (setpoints de control)
Lista de shared attributes por tipo de levantamiento con nombre, tipo, descripción, quién los escribe.

### 4. Rule Chains

#### 4.1 Root Rule Chain: "Ingesta y Normalización"
- Diagrama de flujo nodo por nodo
- Configuración de cada nodo (tipo, nombre, script si aplica)
- Scripts de transformación/validación con código completo

#### 4.2 Rule Chain: "Propagación Device→Asset"
- Cómo copiar telemetría del Device RTU al Asset Pozo
- Nodos: Related Entity → Change Originator → Save Timeseries
- Configuración exacta del filtro de relación

#### 4.3 Rule Chain: "Alarmas Operativas"
- Lista de todas las alarmas con su lógica
- Cómo referenciar shared attributes para umbrales dinámicos
- Propagación de alarmas en la jerarquía

#### 4.4 Rule Chain: "Publicación a Kafka"
- Configuración del nodo Kafka producer
- Formato del mensaje
- Topics por tipo de levantamiento
- Manejo de errores y reintentos

#### 4.5 Rule Chain: "Recepción de Resultados"
- Cómo el servicio externo publica resultados de vuelta a TB
- REST API call para escribir server attributes
- Generación de alarmas de optimización desde el servicio

### 5. Dashboards

#### 5.1 Dashboard "Campo" (vista ejecutiva)
- Widgets: mapa de pozos con color por estado, producción total, KPIs, ranking
- Fuente de datos de cada widget
- Filtros: por macolla, por tipo levantamiento, por estado

#### 5.2 Dashboard "Macolla"
- Widgets: tabla de pozos con métricas, asignación de recursos, oportunidades
- Gráfico de producción acumulada por macolla
- Benchmarking entre pozos

#### 5.3 Dashboard "Pozo Individual"
- Layout detallado (referencia al diseño del documento de arquitectura)
- Widget de producción (time series)
- Widget de análisis nodal (custom: gráfico IPR/VLP)
- Widget de recomendación de optimización (card custom)
- Widget de salud del equipo (gauges)
- Widget de DCA y pronóstico (time series + proyección)
- Widget de alarmas activas
- Configuración de cada widget: datasource, keys, colores, umbrales

#### 5.4 Dashboard "Optimización de Campo"
- Ranking de oportunidades
- Asignación óptima de gas lift
- Clusters de pozos similares
- Producción actual vs potencial

### 6. Integración con Servicio de Optimización

#### 6.1 Configuración de Kafka en ThingsBoard
- Cómo configurar la Integration o Rule Chain para publicar a Kafka
- Topics, serialización, particionamiento

#### 6.2 API de ThingsBoard usada por el servicio
- Endpoints necesarios con ejemplos curl
- Autenticación JWT
- Rate limits y buenas prácticas

#### 6.3 Formato de intercambio de datos
- Estructura JSON de telemetría publicada a Kafka
- Estructura JSON de resultados de optimización
- Estructura JSON de alarmas

### 7. Datos Necesarios por Pozo (Checklist)

Tabla tipo checklist que el ingeniero de campo llena para cada pozo:
- Dato | Fuente | Obligatorio | Cómo obtenerlo | Dónde cargarlo en TB

Separado por:
- Datos que ya vienen del SCADA/RTU (automático)
- Datos de archivos del pozo (carga manual única)
- Datos de laboratorio PVT (carga manual, actualización anual)
- Datos de pruebas de pozo (carga periódica)

### 8. Procedimientos Operativos

#### 8.1 Agregar un nuevo pozo
Paso a paso: crear Asset, crear Device, crear relaciones, cargar atributos, verificar telemetría, configurar en servicio de optimización.

#### 8.2 Cambiar equipo de levantamiento
Qué atributos actualizar, cómo registrar el evento de workover.

#### 8.3 Actualizar datos de yacimiento
Después de una prueba de presión o build-up, qué atributos actualizar.

#### 8.4 Interpretar resultados de optimización
Guía para el ingeniero de producción: qué significa cada campo opt_*, cuándo actuar, cómo validar la recomendación.

### 9. Troubleshooting
- Pozo no muestra datos → verificar Device, relación, rule chain
- Resultados de optimización no se actualizan → verificar servicio, Kafka, logs
- Alarmas falsas → ajustar umbrales en shared attributes
- Dashboard no carga → verificar permisos, datasources

### 10. Apéndices
- A: Glosario de términos petroleros y de ThingsBoard
- B: Mapeo completo de telemetría por tipo de levantamiento
- C: Scripts completos de Rule Chain
- D: Plantilla de carga de datos de pozo (formato CSV)
- E: Diagramas de arquitectura en alta resolución

## FORMATO
- Documento profesional, con logos de VASTEIX y Atilax si los proveen
- Tablas claras y bien formateadas
- Diagramas descriptivos (describir con texto para que se puedan recrear)
- Numeración consistente
- Índice/tabla de contenidos
- Versión del documento y fecha
```

---

## PROMPT 4: Claude Cowork — Documentación de Sistema para Stakeholders

```
Eres un consultor senior de automatización industrial y transformación digital para el sector petrolero. Vas a crear un documento ejecutivo y funcional titulado "Sistema Atilax — Plataforma Inteligente de Monitoreo y Optimización de Producción Petrolera" para la empresa VASTEIX.

Este documento NO es técnico de implementación. Es el documento que se entrega al cliente (operadora petrolera, gerencia de producción, ingenieros de yacimiento) para que entiendan qué hace el sistema, qué optimiza, qué datos necesita, qué resultados entrega y qué beneficios trae.

## ESTRUCTURA DEL DOCUMENTO

### 1. Introducción
- Qué es Atilax
- Visión: transformar el monitoreo pasivo en optimización activa de producción
- Quién lo desarrolla (VASTEIX, consultora de automatización industrial especializada en IoT y SCADA para el sector petrolero)
- Para quién está diseñado (operadoras petroleras, empresas mixtas, campos en Venezuela y región)

### 2. El Problema
- La mayoría de los pozos en Venezuela operan por debajo de su potencial óptimo
- El monitoreo tradicional (SCADA) captura datos pero no genera recomendaciones
- Los ingenieros de producción están sobrecargados y no pueden analizar todos los pozos diariamente
- Los datos estáticos del pozo (PVT, completación) están en papel o en la memoria de los ingenieros
- La rotación de personal ha causado pérdida de conocimiento técnico
- No hay herramienta integrada que combine monitoreo + ingeniería de producción + inteligencia artificial

### 3. La Solución: Atilax
- Plataforma que integra tres capas:
  1. **Monitoreo en tiempo real**: captura y visualización de datos operativos
  2. **Ingeniería de producción automatizada**: análisis nodal, eficiencia, declinación
  3. **Inteligencia artificial**: predicción de fallas, optimización de campo, agrupamiento de pozos

### 4. Qué Monitorea (Capa 1)
Para cada tipo de levantamiento artificial, explicar en lenguaje de ingeniería de producción (NO en lenguaje de TI):

#### 4.1 Pozos con Bombeo Electrosumergible (ESP/BES)
- Variables monitoreadas: presiones (cabezal tubing/casing, admisión, descarga), temperaturas (motor, admisión, cabezal), corriente/voltaje/potencia del motor, frecuencia del variador, vibración, aislamiento, tasa de flujo, corte de agua
- Alarmas automáticas: sobretemperatura motor, baja presión admisión, alto consumo eléctrico, vibración excesiva, degradación de aislamiento, pozo inactivo
- Frecuencia de captura: cada 30 segundos a 5 minutos

#### 4.2 Pozos con Bombeo Mecánico (SRP)
- Variables: presiones cabezal, corriente motor, SPM, carga en pulido, nivel de fluido, llenado de bomba, carta dinamométrica
- Alarmas: golpe de fluido, bloqueo por gas, rotura de cabillas, pozo parado
- Frecuencia: cada 1-5 minutos, carta dinamométrica cada 15-60 minutos

#### 4.3 Pozos con Gas Lift
- Variables: presión inyección/producción, temperatura, tasa inyección gas, apertura choke, tasa de producción
- Alarmas: oscilaciones de presión (casing heading), baja tasa de inyección, pérdida de gas

#### 4.4 Pozos con Bombeo de Cavidades Progresivas (PCP)
- Variables: torque, RPM, corriente, presiones, tasa de flujo, contenido de arena
- Alarmas: sobretorque, baja eficiencia, alta temperatura

#### 4.5 Nivel de Macolla y Campo
- Producción total por macolla y campo
- Disponibilidad de gas lift (compresores)
- Estado de separadores y facilidades
- Runtime y producción diferida

### 5. Qué Optimiza (Capa 2)
Explicar cada cálculo en términos de beneficio para la producción:

#### 5.1 Análisis Nodal Automatizado
- Qué es: determina si el pozo está produciendo lo que el yacimiento puede entregar
- Qué calcula: punto operativo actual vs. punto óptimo
- Resultado: "Este pozo produce 850 BPD pero podría producir 1,050 BPD si sube la frecuencia del variador a 65 Hz"
- Beneficio: identifica producción diferida recuperable sin inversión en workover

#### 5.2 Optimización por Tipo de Levantamiento
- **ESP**: frecuencia óptima del VSD, eficiencia de bomba, consumo energético específico
- **SRP**: velocidad óptima (SPM), diagnóstico automático de carta dinamométrica
- **Gas Lift**: tasa óptima de inyección de gas por pozo y asignación óptima entre pozos
- **PCP**: RPM óptima, indicador de desgaste

#### 5.3 Análisis de Declinación
- Qué es: proyecta la producción futura basada en la tendencia histórica
- Modelos: Arps (clásico) + machine learning (mejorado)
- Resultado: pronóstico mensual de producción, EUR (reservas estimadas), tasa de declinación
- Beneficio: planificación de producción, identificación de pozos que declinan más rápido de lo esperado

#### 5.4 Optimización de Campo Completo
- Redistribuir recursos compartidos (gas, potencia) entre pozos para maximizar producción total
- Ranking de oportunidades: qué pozos intervenir primero para mayor retorno

#### 5.5 Score de Salud del Pozo
- Indicador compuesto 0-100 que resume el estado operativo, eficiencia y tendencia
- Permite priorizar atención entre decenas o cientos de pozos

### 6. Qué Predice (Capa 3 — Inteligencia Artificial)

#### 6.1 Predicción de Fallas
- Anticipa fallas de equipos (ESP, bombas) días o semanas antes
- Permite programar mantenimiento preventivo en lugar de correctivo
- Reduce producción diferida por paros no programados

#### 6.2 Detección de Anomalías
- Identifica automáticamente cuando un pozo se comporta fuera de lo normal
- Detecta: sensores descalibrados, irrupción de agua, interferencia de gas, desgaste
- Alerta al ingeniero antes de que el problema cause pérdida significativa de producción

#### 6.3 Agrupamiento de Pozos Similares
- Clasifica automáticamente los pozos en grupos según sus características
- Permite: aplicar lecciones de un pozo a otros similares, identificar benchmarks, detectar pozos que se desvían de su grupo

#### 6.4 Pronóstico de Producción con IA
- Modelos de machine learning que aprenden del comportamiento histórico
- Más precisos que los métodos tradicionales para pozos con comportamiento complejo
- Mejoran con el tiempo a medida que se acumulan más datos

### 7. Qué Datos Necesita

#### 7.1 Datos automáticos (del SCADA/RTU)
- Tabla con cada variable, frecuencia, y de dónde viene
- Estos datos se capturan sin intervención humana una vez conectado el equipo

#### 7.2 Datos que debe cargar el ingeniero (una vez)
- Tabla con cada dato, fuente (archivo del pozo, registro, laboratorio), formato, y frecuencia de actualización
- Datos del yacimiento: presión (build-up), temperatura, mecanismo empuje
- Datos PVT: API, GOR, Pb, viscosidad, Bo (del análisis de laboratorio)
- Datos mecánicos: profundidades, casings, tubing, perforaciones (del programa de completación)
- Datos del equipo: modelo y specs de bomba, motor, variador, cabillas, válvulas

#### 7.3 Datos que mejoran el sistema con el tiempo
- Registros de eventos: workovers, cambios de bomba, estimulaciones, paros
- Etiquetado de fallas: qué falló, cuándo, por qué (para entrenar IA)
- Pruebas de producción periódicas: tasa medida vs. estimada
- Build-up / pruebas de presión: actualización de presión de yacimiento

#### 7.4 Checklist por pozo
Formato simple que el cliente pueda imprimir y llenar:
- [ ] Datos PVT disponibles → Archivo: ___
- [ ] Última presión de yacimiento → Valor: ___ psi, Fecha: ___
- [ ] Programa de completación → Archivo: ___
- [ ] Specs del equipo de levantamiento → Modelo: ___, Fecha instalación: ___
- [ ] RTU conectado y transmitiendo → Sí/No
- [ ] Historial de producción digitalizado → Meses disponibles: ___

### 8. Qué Resultados Entrega

#### 8.1 Dashboards en tiempo real
- Capturas/mockups de los dashboards principales (describir layout)
- Dashboard de campo: vista ejecutiva con KPIs
- Dashboard de macolla: detalle operativo
- Dashboard de pozo: análisis completo individual

#### 8.2 Alarmas inteligentes
- Dos niveles: operativas (automáticas, instantáneas) y de optimización (calculadas, periódicas)
- Tabla de todos los tipos de alarma con descripción, severidad, y acción recomendada

#### 8.3 Reportes
- Reporte diario: producción, eventos, oportunidades
- Reporte semanal: tendencias, benchmarking, clustering
- Reporte mensual: DCA, EUR, evolución de salud de pozos

#### 8.4 Recomendaciones accionables
- Cada recomendación incluye: qué hacer, cuánto ganar, nivel de confianza
- Priorizadas por impacto y facilidad de implementación

### 9. Beneficios Cuantificados

Basados en casos documentados del sector:
- **5-20% incremento producción** por optimización de punto operativo
- **21% mejora mediana** con VSD en bombeo mecánico (caso PDVSA, SPE-103157)
- **23% reducción consumo eléctrico** por optimización ESP (caso PDVSA Morichal)
- **30-50% reducción tiempo inactivo** por mantenimiento predictivo
- **50% reducción costo levantamiento** con tecnologías apropiadas (caso PCP vs SRP en Faja)
- ROI típico: 6-12 meses

### 10. Ruta de Implementación

#### Fase 1: Monitoreo (mes 1-3)
- Conectar RTUs existentes a Atilax
- Configurar dashboards de monitoreo
- Cargar datos estáticos de los pozos
- Resultado: visibilidad completa del campo en tiempo real

#### Fase 2: Optimización clásica (mes 3-6)
- Activar motores de análisis nodal y eficiencia
- Configurar alarmas de optimización
- Generar primeras recomendaciones
- Resultado: recomendaciones accionables para cada pozo

#### Fase 3: Inteligencia artificial (mes 6-12)
- Entrenar modelos con datos acumulados
- Activar predicción de fallas y detección de anomalías
- Optimización de campo completo
- Resultado: sistema autónomo de mejora continua

#### Fase 4: Evolución continua (mes 12+)
- Refinamiento de modelos con más datos
- Expansión a nuevos campos
- Integración con sistemas corporativos
- Gemelo digital por pozo

### 11. Requisitos para el Cliente
- Infraestructura: conectividad de red, RTUs con protocolo compatible
- Personal: ingeniero de producción como punto focal, técnico de instrumentación
- Datos: acceso a archivos de pozo, PVT, historial de producción
- Compromiso: carga inicial de datos estáticos, registro de eventos

### 12. Sobre VASTEIX
- Breve descripción de la empresa
- Experiencia en automatización industrial y sector petrolero
- Contacto

## TONO Y FORMATO
- Profesional pero accesible (no excesivamente técnico)
- Orientado a beneficios y resultados
- Visual: usar tablas, íconos descriptivos, layouts de dashboard
- Extensión: 25-40 páginas
- Idioma: español
- Formato: documento Word profesional con portada, índice, numeración de páginas
```
