"""
Roles de Sofía Consulta (alineados a CDATTG).

Solo dos roles: SUPER ADMINISTRADOR y FORMACION COMPLEMENTARIA.
Ambos pueden usar el módulo Sofía/Betowa.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

ROL_SUPER_ADMIN = "SUPER ADMINISTRADOR"
ROL_FORMACION_COMPLEMENTARIA = "FORMACION COMPLEMENTARIA"

ROLES_VALIDOS = frozenset({ROL_SUPER_ADMIN, ROL_FORMACION_COMPLEMENTARIA})
ROLES_MODULO_CONSULTA = ROLES_VALIDOS
