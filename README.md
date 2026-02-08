# Atilax Well Simulator

Simulador de pozos petroleros venezolanos para ThingsBoard PE. Genera datos realistas de telemetria para campos de la Faja del Orinoco (crudo extrapesado), Lago de Maracaibo (crudo pesado/medio) y Oriente (crudo liviano).

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

1. Copiar y editar la configuracion:
```bash
cp config/default_config.yaml config/mi_config.yaml
```

2. Configurar la variable de entorno con la contrasena de ThingsBoard:
```bash
export TB_PASSWORD="tu_contrasena"
```

## Uso

### Crear entidades en ThingsBoard
```bash
python main.py create --config config/default_config.yaml
```

Crea la jerarquia completa: campos, macollas, pozos (assets), RTUs, gateways (devices), relaciones y atributos estaticos.

### Simular en tiempo real
```bash
python main.py simulate --config config/default_config.yaml --mode realtime
```

Envia telemetria continuamente via MQTT. Usar `Ctrl+C` para detener.

### Generar datos historicos
```bash
python main.py simulate --config config/default_config.yaml --mode historical --days 365
```

Genera un ano de datos historicos via REST API en batch.

### Ver estado
```bash
python main.py status --config config/default_config.yaml
```

### Eliminar entidades
```bash
python main.py delete --config config/default_config.yaml
```

## Docker

```bash
export TB_PASSWORD="tu_contrasena"
docker compose up -d
```

## Estructura de entidades

```
Campo Petrolero (asset: field)
  |-- Macolla (asset: macolla)
       |-- Pozo (asset: well)
       |    |-- RTU (device: rtu_esp/rtu_srp/rtu_gaslift/rtu_pcp)
       |    |-- Sensor de fondo (device: downhole_gauge) [opcional]
       |    |-- Medidor multifasico (device: multiphase_meter) [opcional]
       |-- Facilidad (asset: facility)
       |-- Gateway IoT (device: iot_gateway)
```

## Tipos de levantamiento artificial

| Tipo | Device Type | Descripcion |
|------|------------|-------------|
| ESP | rtu_esp | Bomba electrosumergible |
| SRP | rtu_srp | Bombeo mecanico (cabillas) |
| Gas Lift | rtu_gaslift | Levantamiento por gas |
| PCP | rtu_pcp | Bomba de cavidades progresivas |

## Anomalias simuladas

- Degradacion de bomba (ESP/SRP/PCP)
- Interferencia de gas (SRP/ESP)
- Irrupcion de agua
- Produccion de arena (PCP/ESP en Faja)
- Casing heading (Gas Lift)
- Problemas electricos (tipico Venezuela)
- Sensor pegado
- Drift de sensor

## Campos preconfigurados

- **Campo Boscan**: Lago de Maracaibo, 3 macollas, 24 pozos, predomina SRP
- **Campo Cerro Negro**: Faja del Orinoco, 2 macollas, 27 pozos, predomina PCP/ESP
- **Campo Anaco**: Oriente liviano, 2 macollas, 12 pozos, predomina Gas Lift/ESP
