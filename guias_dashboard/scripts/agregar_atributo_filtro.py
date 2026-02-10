#!/usr/bin/env python3
"""
Script para agregar el atributo 'wellFilter' a cada pozo en ThingsBoard.
PREREQUISITO para el sistema de filtros dinámicos del Dashboard.

El filtro funciona así:
1. Cada pozo tiene un atributo 'wellFilter' con su tipo (esp, srp, pcp, gaslift)
2. El usuario actual tiene atributos booleanos (show_esp, show_srp, etc.)
3. El filtro del dashboard usa CURRENT_USER attributes para filtrar dinámicamente

Uso:
    python3 agregar_atributo_filtro.py
"""
import requests
import sys

# Configuración de ThingsBoard
TB_URL = "http://144.126.150.120:8080"
TB_USER = "well@atilax.io"
TB_PASS = "10203040"


def login():
    """Autenticarse en ThingsBoard."""
    r = requests.post(
        f"{TB_URL}/api/auth/login",
        json={"username": TB_USER, "password": TB_PASS}
    )
    r.raise_for_status()
    return r.json()["token"]


def get_current_user(token):
    """Obtener el usuario actual."""
    h = {"X-Authorization": f"Bearer {token}"}
    r = requests.get(f"{TB_URL}/api/auth/user", headers=h)
    r.raise_for_status()
    return r.json()


def main():
    print("=" * 60)
    print("CONFIGURAR ATRIBUTOS DE FILTRO PARA DASHBOARD")
    print("=" * 60)

    # Login
    print("\n[1/3] Autenticando...")
    token = login()
    h = {"X-Authorization": f"Bearer {token}"}
    print("  ✓ Autenticación exitosa")

    # Get current user info
    user = get_current_user(token)
    user_id = user["id"]["id"]
    print(f"  Usuario: {user['email']} (ID: {user_id})")

    # Step 1: Add wellFilter attribute to each well based on lift_type
    print("\n[2/3] Agregando atributo 'wellFilter' a cada pozo...")
    wells = requests.get(
        f"{TB_URL}/api/tenant/assets?pageSize=100&page=0&type=well",
        headers=h
    ).json()["data"]

    updated = 0
    for w in wells:
        wid = w["id"]["id"]
        wname = w["name"]

        # Get lift_type
        attrs_raw = requests.get(
            f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/values/attributes/SERVER_SCOPE",
            headers=h
        ).json()
        attrs = {a["key"]: a["value"] for a in attrs_raw}
        lift_type = attrs.get("lift_type", "unknown")

        # Map lift_type to filter value
        filter_map = {
            "esp": "esp",
            "srp": "srp",
            "pcp": "pcp",
            "gaslift": "gaslift",
            "gas_lift": "gaslift",
        }
        filter_value = filter_map.get(lift_type.lower(), lift_type.lower())

        # Also create a field filter value
        field_name = attrs.get("field_name", "")
        field_filter_map = {
            "Campo Boscán": "campo_boscan",
            "Campo Cerro Negro": "campo_cerronegro",
            "Campo Anaco": "campo_anaco",
        }
        field_filter = ""
        for key, val in field_filter_map.items():
            if key.lower() in field_name.lower():
                field_filter = val
                break

        # Set wellFilter and fieldFilter attributes
        payload = {
            "wellFilter": filter_value,
            "fieldFilter": field_filter
        }

        requests.post(
            f"{TB_URL}/api/plugins/telemetry/ASSET/{wid}/attributes/SERVER_SCOPE",
            headers=h,
            json=payload
        )
        print(f"  ✓ {wname}: wellFilter={filter_value}, fieldFilter={field_filter}")
        updated += 1

    # Step 2: Initialize user filter attributes (all enabled by default)
    print(f"\n[3/3] Inicializando filtros del usuario ({user['email']})...")
    user_attrs = {
        "show_esp": "esp",
        "show_srp": "srp",
        "show_pcp": "pcp",
        "show_gaslift": "gaslift",
        "show_campo_boscan": "campo_boscan",
        "show_campo_cerronegro": "campo_cerronegro",
        "show_campo_anaco": "campo_anaco",
    }

    # User attributes go on the USER entity
    requests.post(
        f"{TB_URL}/api/plugins/telemetry/USER/{user_id}/attributes/SERVER_SCOPE",
        headers=h,
        json=user_attrs
    )
    print(f"  ✓ Atributos de filtro inicializados (todos activos)")
    for k, v in user_attrs.items():
        print(f"    {k} = {v}")

    # Summary
    print(f"\n{'=' * 60}")
    print("RESUMEN")
    print(f"{'=' * 60}")
    print(f"  Pozos actualizados con wellFilter: {updated}")
    print(f"  Atributos de usuario inicializados: {len(user_attrs)}")
    print(f"\n  ✓ ¡Listo! Los filtros del dashboard ahora funcionarán.")
    print(f"    Cada toggle switch en el dashboard controlará la visibilidad")
    print(f"    de los pozos según su tipo de levantamiento y campo.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
