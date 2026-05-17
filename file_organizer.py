import os
import shutil
from datetime import datetime
from config import DOWNLOADS_DIR, FILE_CATEGORIES


def _get_category(extension: str) -> str:
    ext = extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Outros"


def organize_downloads(dry_run: bool = False, target_dir: str = None) -> list:
    """
    Move arquivos da pasta escolhida para subpastas categorizadas.
    Se dry_run=True, apenas lista o que seria feito sem mover nada.
    Retorna lista de dicts com as operações realizadas.
    """
    base_dir = target_dir or DOWNLOADS_DIR

    if not os.path.isdir(base_dir):
        print(f"[Organizer] Pasta não encontrada: {base_dir}")
        return []

    operations = []
    skipped = 0

    for filename in os.listdir(base_dir):
        src = os.path.join(base_dir, filename)

        # Ignora subpastas
        if os.path.isdir(src):
            skipped += 1
            continue

        _, ext = os.path.splitext(filename)
        if not ext:
            skipped += 1
            continue

        category = _get_category(ext)
        dest_dir = os.path.join(base_dir, category)
        dest = os.path.join(dest_dir, filename)

        # Evita sobrescrever arquivo existente
        if os.path.exists(dest):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, file_ext = os.path.splitext(filename)
            dest = os.path.join(dest_dir, f"{name}_{timestamp}{file_ext}")

        operations.append({"file": filename, "category": category, "dest": dest})

        if not dry_run:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src, dest)
            print(f"[Organizer] Movido: {filename}  →  {category}/")
        else:
            print(f"[Organizer] [DRY RUN] {filename}  →  {category}/")

    print(f"[Organizer] Total: {len(operations)} arquivo(s) processado(s), "
          f"{skipped} ignorado(s) (pastas/sem extensão).")
    return operations


if __name__ == "__main__":
    organize_downloads()
