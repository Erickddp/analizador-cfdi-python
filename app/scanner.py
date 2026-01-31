"""Escaneo y procesamiento de archivos XML CFDI en segundo plano.

Este módulo define una clase que recorre archivos y carpetas, analiza cada
XML mediante el parser y clasifica el CFDI según el RFC del usuario. El
procesamiento se realiza en un hilo separado para no bloquear la interfaz.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Tuple

from PySide6.QtCore import QObject, Signal, QThread

from .parser_cfdi import parse_cfdi
from .classifier import classify_cfdi
from .models import CFDI, Concepto


def _collect_xml_files(paths: Iterable[str]) -> List[str]:
    """Recorre los elementos de `paths` y devuelve una lista de rutas XML."""
    files: List[str] = []
    for path in paths:
        p = Path(path)
        if p.is_file() and p.suffix.lower() == '.xml':
            files.append(str(p))
        elif p.is_dir():
            for root, _, filenames in os.walk(p):
                for fname in filenames:
                    if fname.lower().endswith('.xml'):
                        files.append(str(Path(root) / fname))
    return files


class XMLScanner(QObject):
    """Procesa de manera concurrente una lista de archivos XML CFDI."""
    progress = Signal(int, int, int, int, int)  # processed, invalid, duplicates, cfdi33, total
    finished = Signal(list, list)  # list of CFDI, list of Concepto

    def __init__(self, paths: Iterable[str], user_rfc: str) -> None:
        super().__init__()
        self.paths = list(paths)
        self.user_rfc = user_rfc

    def start(self):
        """Crea un hilo y comienza el procesamiento."""
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)
        self._thread.start()

    def _run(self):
        files = _collect_xml_files(self.paths)
        total = len(files)
        processed = 0
        invalid_count = 0
        duplicates = 0
        cfdi33_count = 0
        uuids_seen = set()
        cfdis: List[CFDI] = []
        concepts_all: List[Concepto] = []

        for idx, file in enumerate(files, start=1):
            cfdi, concepts = parse_cfdi(file)
            if cfdi is None:
                invalid_count += 1
            else:
                # Deduplicar por UUID
                if cfdi.uuid in uuids_seen:
                    duplicates += 1
                else:
                    uuids_seen.add(cfdi.uuid)
                    # Clasificar
                    clasif = classify_cfdi(cfdi, self.user_rfc)
                    cfdi.clasificacion = clasif
                    if cfdi.version.startswith("3.3"):
                        cfdi33_count += 1
                    cfdis.append(cfdi)
                    concepts_all.extend(concepts)
            processed = idx
            # Emitir progreso
            self.progress.emit(processed, invalid_count, duplicates, cfdi33_count, total)

        # Emitir finalización
        self.finished.emit(cfdis, concepts_all)
        # Terminar hilo
        self._thread.quit()
        self._thread.wait()