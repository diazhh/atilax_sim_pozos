#!/usr/bin/env python3
"""
Script para agregar coordenadas GPS (latitude/longitude) a los pozos en ThingsBoard.
PREREQUISITO para el widget de mapa del Dashboard de Campo Petrolero.

Uso:
    python3 agregar_coordenadas_gps.py

Las coordenadas se generan basándose en la ubicación real de los campos petroleros
venezolanos con un offset aleatorio para distribuir los pozos dentro de cada campo.
"""
import requests
import random
import sys

# Configuración de ThingsBoard
TB_URL = "http://144.126.150.120:8080"
TB_USER = "well@atilax.io"
TB_PASS = "10203040"

# Coordenadas base de los campos petroleros venezolanos
FIELD_COORDS = {
    # Campo Boscán - Lago de Maracaibo, Zulia
    "Campo Boscán": {"lat": 9.90, "lon": -71.80, "spread": 0.04},
    "Boscan": {"lat": 9.90, "lon": -71.80, "spread": 0.04},
    # Campo Cerro Negro - Faja Petrolífera del Orinoco, Monagas
    "Campo Cerro Negro": {"lat": 8.50, "lon": -63.50, "spread": 0.05},
    "Cerro Negro": {"lat": 8.50, "lon": -63.50, "spread": 0.05},
    # Campo Anaco - Oriente, Anzoátegui
    "Campo Anaco": {"lat": 9.43, "lon": -64.47, "spread": 0.03},
    "Anaco": {"lat": 9.43, "lon": -64.47, "spread": 0.03},
}

# Coordenadas por defecto si no se reconoce el campo
DEFAULT_COORDS = {"lat": 9.0, "lon": -65.0, "spread": 0.1}


def login():
    """Autenticarse en ThingsBoard y obtener token JWT."""
    r = requests.post(
        f"{TB_URL}/api/auth/login",
        json={"username": TB_USER, "password": TB_PASS}
    )
    r.raise_for_status()
    return r.json()["token"]


def get_wells(token):
    """Obtener todos los pozos."""
    h = {"X-Authorization": f"Bearer {token}"}
    r = requests.get(
        f"{TB_URL}/api/tenant/assets?pageSize=100&page=0&type=well",
        headers=h
    )
    r.raise_for_status()
    return r.json()["data"]


def get_well_field(token, well_id):
    """Obtener el nombre del campo del pozo."""
    h = {"X-Authorization": f"Bearer {token}"}
    r = requests.get(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{well_id}/values/attributes/SERVER_SCOPE",
        headers=h
    )
    r.raise_for_status()
    attrs = {a["key"]: a["value"] for a in r.json()}
    return attrs.get("field_name", "")


def get_coords_for_field(field_name):
    """Determinar coordenadas base según el campo."""
    for key, coords in FIELD_COORDS.items():
        if key.lower() in field_name.lower():
            return coords
    print(f"  ADVERTENCIA: Campo '{field_name}' no reconocido, usando coordenadas por defecto")
    return DEFAULT_COORDS


def set_coordinates(token, well_id, lat, lon):
    """Asignar latitude y longitude como atributos SERVER_SCOPE."""
    h = {"X-Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{well_id}/attributes/SERVER_SCOPE",
        headers=h,
        json={"latitude": lat, "longitude": lon}
    )
    r.raise_for_status()


def check_existing_coords(token, well_id):
    """Verificar si el pozo ya tiene coordenadas."""
    h = {"X-Authorization": f"Bearer {token}"}
    r = requests.get(
        f"{TB_URL}/api/plugins/telemetry/ASSET/{well_id}/values/attributes/SERVER_SCOPE",
        headers=h
    )
    r.raise_for_status()
    attrs = {a["key"]: a["value"] for a in r.json()}
    has_lat = "latitude" in attrs and attrs["latitude"] != 0
    has_lon = "longitude" in attrs and attrs["longitude"] != 0
    return has_lat and has_lon


def main():
    print("=" * 60)
    print("AGREGAR COORDENADAS GPS A POZOS EN THINGSBOARD")
    print("=" * 60)

    # Login
    print("\n[1/4] Autenticando en ThingsBoard...")
    token = login()
    print("  ✓ Autenticación exitosa")

    # Get wells
    print("\n[2/4] Obteniendo lista de pozos...")
    wells = get_wells(token)
    print(f"  ✓ {len(wells)} pozos encontrados")

    # Group by field for organized coordinate assignment
    print("\n[3/4] Asignando coordenadas por campo...")

    # Use macolla grouping for tighter well clustering
    macolla_offsets = {}
    updated = 0
    skipped = 0
    errors = 0

    for w in wells:
        wid = w["id"]["id"]
        wname = w["name"]

        try:
            # Check if already has coords
            if check_existing_coords(token, wid):
                print(f"  ⏭ {wname} - ya tiene coordenadas, saltando")
                skipped += 1
                continue

            # Get field name
            field_name = get_well_field(token, wid)
            coords = get_coords_for_field(field_name)

            # Generate coordinates with macolla-based clustering
            # Wells in same macolla should be close together
            attrs_raw = requests.get(
                f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE",
                headers={"X-Authorization": f"Bearer {token}"}
            ).json()
            macolla = next((a["value"] for a in attrs_raw if a["key"] == "macolla_name"), "unknown")

            if macolla not in macolla_offsets:
                # Each macolla gets a base offset within the field
                macolla_offsets[macolla] = {
                    "lat_offset": random.uniform(-coords["spread"], coords["spread"]),
                    "lon_offset": random.uniform(-coords["spread"], coords["spread"])
                }

            mac_off = macolla_offsets[macolla]
            # Wells within macolla are very close (within ~500m)
            lat = coords["lat"] + mac_off["lat_offset"] + random.uniform(-0.005, 0.005)
            lon = coords["lon"] + mac_off["lon_offset"] + random.uniform(-0.005, 0.005)

            set_coordinates(token, wid, round(lat, 6), round(lon, 6))
            print(f"  ✓ {wname} ({macolla}): {lat:.6f}, {lon:.6f}")
            updated += 1

        except Exception as e:
            print(f"  ✗ {wname}: Error - {e}")
            errors += 1

    # Summary
    print(f"\n{'=' * 60}")
    print("[4/4] RESUMEN")
    print(f"{'=' * 60}")
    print(f"  Pozos actualizados: {updated}")
    print(f"  Pozos saltados (ya tenían coords): {skipped}")
    print(f"  Errores: {errors}")
    print(f"  Total procesados: {updated + skipped + errors}")

    if updated > 0:
        print(f"\n  ✓ ¡Listo! Ahora puedes usar el widget de mapa en el dashboard.")
        print(f"    Los pozos se agruparán por macolla dentro de cada campo.")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
