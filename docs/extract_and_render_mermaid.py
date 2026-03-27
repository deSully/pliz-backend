#!/usr/bin/env python3
"""
Extrait les blocs mermaid du document Marp, les compile en SVG via mmdc,
et remplace les blocs dans le markdown par des références d'images.
"""

import re
import subprocess
import sys
from pathlib import Path

MD_FILE   = Path(__file__).parent / "presentation_backend_BECEAO.md"
DIAG_DIR  = Path(__file__).parent / "diagrams"
DIAG_DIR.mkdir(exist_ok=True)

# Noms lisibles par diagramme (dans l'ordre d'apparition)
NAMES = [
    "01_acteurs_ecosysteme",
    "02_architecture_couches",
    "03_architecture_aws_ha",
    "04_flux_authentification",
    "05_dispositif_lcbft",
    "06_niveaux_resilience",
    "07_cycle_transfert_interne",
    "08_cycle_topup_partenaire",
    "09_systeme_frais",
    "10_integration_factory",
    "11_stack_observabilite",
    "12_procedure_incidents",
    "13_architecture_aws_complete",
    "14_flux_transactionnel",
    "15_securite_profondeur",
    "16_pipeline_cicd",
]

MERMAID_THEME = """%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor':        '#1a3a5c',
    'primaryTextColor':    '#ffffff',
    'primaryBorderColor':  '#e8a020',
    'lineColor':           '#e8a020',
    'secondaryColor':      '#0d2137',
    'tertiaryColor':       '#f0f7ff',
    'edgeLabelBackground': '#ffffff',
    'fontFamily':          'Segoe UI, Helvetica Neue, Arial, sans-serif',
    'fontSize':            '14px'
  }
}}%%
"""

def extract_blocks(text):
    """Retourne une liste de (bloc_complet, contenu_mermaid)."""
    pattern = re.compile(r'```mermaid\n(.*?)```', re.DOTALL)
    return [(m.group(0), m.group(1)) for m in pattern.finditer(text)]


def render_svg(mmd_content, name):
    mmd_path = DIAG_DIR / f"{name}.mmd"
    svg_path = DIAG_DIR / f"{name}.svg"

    # Injecter le thème en tête du diagramme
    full_content = MERMAID_THEME + mmd_content.strip()
    mmd_path.write_text(full_content, encoding="utf-8")

    result = subprocess.run(
        ["mmdc", "-i", str(mmd_path), "-o", str(svg_path),
         "-b", "white", "--width", "1000"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"  ✗ Erreur sur {name}:\n{result.stderr.strip()}")
        return None

    print(f"  ✓ {name}.svg")
    return svg_path


def main():
    text = MD_FILE.read_text(encoding="utf-8")
    blocks = extract_blocks(text)

    if len(blocks) > len(NAMES):
        # Si plus de blocs que de noms, générer des noms automatiques
        extra = [f"diagram_{i+1:02d}" for i in range(len(NAMES), len(blocks))]
        NAMES.extend(extra)

    print(f"→ {len(blocks)} diagrammes Mermaid trouvés\n")

    updated = text
    for i, (full_block, content) in enumerate(blocks):
        name = NAMES[i] if i < len(NAMES) else f"diagram_{i+1:02d}"
        print(f"[{i+1:02d}/{len(blocks)}] {name}")

        svg_path = render_svg(content, name)
        if svg_path is None:
            continue

        # Chemin relatif depuis le dossier docs/
        rel = svg_path.relative_to(MD_FILE.parent)
        img_tag = f"![{name}]({rel})"
        updated = updated.replace(full_block, img_tag, 1)

    MD_FILE.write_text(updated, encoding="utf-8")
    print(f"\n✅ Markdown mis à jour : {MD_FILE.name}")
    print(f"   SVGs dans           : {DIAG_DIR}")


if __name__ == "__main__":
    main()
