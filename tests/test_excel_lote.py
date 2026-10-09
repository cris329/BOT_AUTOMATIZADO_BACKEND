"""
Pruebas de parseo Excel/CSV de lotes.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

import io

from server.services import excel_lote


def test_parse_csv_documentos_feliz():
    raw = io.BytesIO(b"numero_documento,tipo_documento\n111,CC\n222,\n")
    docs = excel_lote.parse_documentos(raw, "lote.csv")
    assert len(docs) == 2
    assert docs[0].numero_documento == "111"
    assert docs[0].tipo_documento == "CC"


def test_parse_csv_vacio_borde():
    raw = io.BytesIO(b"numero_documento\n\n")
    assert excel_lote.parse_documentos(raw, "x.csv") == []


def test_parse_inscripciones_feliz():
    raw = io.BytesIO(b"numero_documento,programa,tipo\n999,ADSO,CC\n")
    filas = excel_lote.parse_inscripciones(raw, "i.csv")
    assert filas[0]["programa"] == "ADSO"


def test_plantillas_bytes():
    assert len(excel_lote.plantilla_registro_xlsx()) > 100
    assert len(excel_lote.plantilla_inscripciones_xlsx()) > 100
