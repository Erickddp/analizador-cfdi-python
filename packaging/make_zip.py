from pathlib import Path
import zipfile

SRC_DIR = Path("build_output/AnalizadorCFDI")
OUT_ZIP = Path("site/assets/downloads/AnalizadorCFDI.zip")

def zip_folder(src: Path, out_zip: Path):
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in src.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(src))

if __name__ == "__main__":
    if not SRC_DIR.exists():
        raise SystemExit(f"No existe la carpeta fuente: {SRC_DIR}")
    zip_folder(SRC_DIR, OUT_ZIP)
    print(f"ZIP listo: {OUT_ZIP}")
