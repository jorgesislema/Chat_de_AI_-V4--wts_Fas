"""Redacción de evidencia (CORR01C/B2).

Uso del pipeline de evidencia:
  1. Redactar ANTES de persistir:
     python tools/redact_evidencia.py --in-place <archivo|carpeta>
  2. Revisar por conteos (nunca muestra coincidencias):
     python tools/redact_evidencia.py --check <archivo|carpeta>

Patrones redactados: URLs postgres con credenciales (usuario:contraseña@),
tokens tipo Bearer y claves en el formato KEY=valor de 16+ caracteres.
El comando útil se conserva referenciando variables de entorno privadas.
Exclusión declarada: las URLs de reproducción sintética
``postgresql://fixture:fixture@…`` NO se redactan (no son secretos y aparecen
en dictámenes de Codex que deben conservarse byte a byte).
"""
import re
import sys
from pathlib import Path

# URL postgres con credenciales: postgresql://user:pass@... (no imprime el match)
PATTERNS = [
    (re.compile(r'postgres(?:ql)?://(?!fixture:fixture@)[^\s/:@]+:[^\s/@]+@',
                re.IGNORECASE), '[REDACTADO-credenciales-DB]@'),
    (re.compile(r'(?i)bearer\s+[a-z0-9._\-]{16,}'), '[REDACTADO-token]'),
    (re.compile(r'(?i)^(CRM_PREMIUM_TEST_URL|DATABASE_URL|SECRET_KEY)=(.{8,})$',
                re.MULTILINE), lambda m: f'{m.group(1)}=[REDACTADO]'),
]


def redact_text(text):
    total = 0
    for pattern, replacement in PATTERNS:
        text, n = pattern.subn(replacement, text)
        total += n
    return text, total


def _targets(target):
    path = Path(target)
    if path.is_dir():
        yield from path.rglob('*.txt')
        yield from path.rglob('*.log')
        yield from path.rglob('*.md')
    else:
        yield path


def main(argv):
    if '--check' in argv:
        target = argv[argv.index('--check') + 1]
        hits = 0
        files = 0
        for path in _targets(target):
            if not path.exists():
                continue
            files += 1
            text = path.read_text(encoding='utf-8', errors='replace')
            for pattern, _ in PATTERNS:
                hits += len(pattern.findall(text))
        print(f'revision: {files} archivo(s), {hits} coincidencia(s) sin redactar')
        print('contenido de coincidencias OMITIDO por diseño')
        return 0 if hits == 0 else 1

    if '--in-place' in argv:
        target = argv[argv.index('--in-place') + 1]
        total = 0
        count = 0
        for path in _targets(target):
            if not path.exists():
                continue
            original = path.read_text(encoding='utf-8', errors='replace')
            redacted, n = redact_text(original)
            if n:
                path.write_text(redacted, encoding='utf-8')
            total += n
            count += 1
        print(f'redactado en {count} archivo(s): {total} sustitucion(es)')
        return 0

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
