#!/usr/bin/env python3
"""Batch processing loop for ER-0019 v3 full-Bible review.

Usage:
    python3 scripts/ship_batch_loop.py <lote_start> [<lote_end>]

For each lote number, reads the chapter list from qa/reports/review-input/,
validates review-out JSONs (fixing inner-quote issues), runs
ship_review_batch.py, and commits.

Does NOT push — caller pushes after each lote or in bulk.
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fix_inner_quotes(path):
    """Fix unescaped inner quotes and control chars in JSON string values.

    Uses field-boundary regex: for each known string field, find the value
    between the field key and the next known field, then escape any inner
    quotes and control characters. This preserves all verse objects intact.
    """
    import re

    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    try:
        json.loads(text)
        return False
    except Exception:
        pass

    def fix_field_values(text, field_name, next_fields):
        """Fix unescaped quotes and control chars in values of field_name."""
        pattern = re.compile(
            r'("' + re.escape(field_name) + r'": ")(.*?)("\s*,?\s*\n\s*"(?:' +
            '|'.join(re.escape(nf) for nf in next_fields) + r')")',
            re.DOTALL
        )

        def replacer(m):
            prefix = m.group(1)
            raw_value = m.group(2)
            suffix = m.group(3)
            # Unescape then re-escape quotes
            raw_value = raw_value.replace('\\"', '"')
            raw_value = raw_value.replace('"', '\\"')
            # Fix control characters: literal newlines/tabs inside strings
            raw_value = raw_value.replace('\r\n', '\\n')
            raw_value = raw_value.replace('\n', '\\n')
            raw_value = raw_value.replace('\r', '\\n')
            raw_value = raw_value.replace('\t', '\\t')
            return prefix + raw_value + suffix

        return pattern.sub(replacer, text)

    # Apply to all string fields that might contain quotes
    text = fix_field_values(text, 'texto_bv_revisto',
                            ['mudancas', 'objecoes', 'veredito', 'justificativa'])
    text = fix_field_values(text, 'justificativa',
                            ['veredito', 'osis', 'mudancas'])
    text = fix_field_values(text, 'antes', ['depois', 'motivo', 'tipo'])
    text = fix_field_values(text, 'depois', ['motivo', 'tipo', 'antes'])
    text = fix_field_values(text, 'motivo',
                            ['tipo', 'questao', 'antes', 'depois'])
    text = fix_field_values(text, 'problema',
                            ['evidencia', 'gravidade', 'tipo'])
    text = fix_field_values(text, 'evidencia',
                            ['gravidade', 'tipo', 'problema'])
    text = fix_field_values(text, 'escolha',
                            ['justificativa', 'alternativas', 'lexico_ref',
                             'diretriz_ref'])
    text = fix_field_values(text, 'questao', ['escolha', 'justificativa'])

    try:
        data = json.loads(text)
        # Verify verse count against review-input
        book_dir = data.get('book_dir', '')
        chapter = data.get('chapter', 0)
        input_path = os.path.join(
            ROOT, f'qa/reports/review-input/{book_dir}-{chapter:03d}.json')
        if os.path.exists(input_path):
            expected = len(json.load(open(input_path)).get('versos', []))
            actual = len(data.get('versos', []))
            if actual != expected:
                print(f'  VERSE COUNT MISMATCH: expected {expected}, got {actual}')
                return False
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        return True
    except Exception as e:
        print(f'  STILL BROKEN: {e}')
        return False


def get_batch_chapters(batch_num, batch_size=16):
    """Get chapter list for a batch number (0-indexed)."""
    all_chapters = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'qa/reports/review-input/*.json'))):
        d = json.load(open(f))
        all_chapters.append((d['livro_dir'], d['capitulo']))

    start = batch_num * batch_size
    end = min(start + batch_size, len(all_chapters))
    return all_chapters[start:end]


def validate_batch(chapters):
    """Validate and fix review-out JSONs for a batch."""
    fixed_count = 0
    errors = []
    for book_dir, chap in chapters:
        pad = f'{chap:03d}'
        path = os.path.join(ROOT, f'qa/reports/review-out/{book_dir}-{pad}.json')
        if not os.path.exists(path):
            errors.append(f'MISSING: {path}')
            continue
        try:
            json.load(open(path))
        except Exception:
            if fix_inner_quotes(path):
                fixed_count += 1
            else:
                errors.append(f'BROKEN: {path}')
    return fixed_count, errors


def ship_batch(chapters):
    """Run ship_review_batch.py on the batch files."""
    files = []
    for book_dir, chap in chapters:
        pad = f'{chap:03d}'
        path = os.path.join(ROOT, f'qa/reports/review-out/{book_dir}-{pad}.json')
        if os.path.exists(path):
            files.append(path)

    if not files:
        print('  No files to ship')
        return False

    cmd = [sys.executable, os.path.join(ROOT, 'scripts/ship_review_batch.py'),
           '-modelo', 'qwen3.7-max', '-no-push'] + files
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    print(result.stdout)
    if result.returncode != 0:
        print(f'  SHIP ERROR: {result.stderr}')
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print('Usage: ship_batch_loop.py <lote_start> [<lote_end>]')
        sys.exit(1)

    lote_start = int(sys.argv[1])
    lote_end = int(sys.argv[2]) if len(sys.argv) > 2 else lote_start + 1

    for lote in range(lote_start, lote_end):
        chapters = get_batch_chapters(lote)
        if not chapters:
            print(f'Lote {lote}: sem capítulos')
            continue

        print(f'\n=== LOTE {lote} ({len(chapters)} capítulos) ===')
        print(f'  {chapters[0][0]}/{chapters[0][1]:03d} → {chapters[-1][0]}/{chapters[-1][1]:03d}')

        fixed, errors = validate_batch(chapters)
        if fixed:
            print(f'  Fixed {fixed} JSON(s)')
        if errors:
            print(f'  ERRORS: {errors}')
            continue

        ship_batch(chapters)


if __name__ == '__main__':
    main()
