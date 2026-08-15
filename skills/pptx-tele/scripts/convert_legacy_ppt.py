#!/usr/bin/env python3
"""
Convert legacy PowerPoint (.ppt) files to modern .pptx format.

This script detects whether a file is in the old .ppt format and converts
it to .pptx using LibreOffice if needed.

Usage:
    python convert_legacy_ppt.py input_file [output_file]

Examples:
    python convert_legacy_ppt.py presentation.ppt
    python convert_legacy_ppt.py presentation.ppt output.pptx

Output:
    - Converts .ppt to .pptx format
    - If input is already .pptx, copies it to output (or reports as-is)
    - Returns the path to the .pptx file
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def is_legacy_ppt(file_path):
    """Check if a file is legacy .ppt format (binary format).

    Legacy .ppt files start with specific magic bytes (OLE header).
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # OLE compound document header
            return header[:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
    except Exception:
        return False


def convert_to_pptx(input_path, output_path=None):
    """Convert .ppt file to .pptx using LibreOffice.

    Args:
        input_path: Path to input file (.ppt or .pptx)
        output_path: Optional path for output file

    Returns:
        Path to the .pptx file
    """
    input_path = Path(input_path)

    if output_path:
        output_path = Path(output_path)
    else:
        output_path = input_path.with_suffix('.pptx')

    # Check if input is already .pptx
    if input_path.suffix.lower() == '.pptx':
        print(f"Input is already in .pptx format: {input_path}")
        if output_path != input_path:
            shutil.copy2(input_path, output_path)
            print(f"Copied to: {output_path}")
        return str(output_path)

    # Check if input is .ppt format
    if input_path.suffix.lower() != '.ppt':
        print(f"Warning: Input file doesn't have .ppt extension: {input_path}")

    # Check if it's actually legacy format
    if not is_legacy_ppt(input_path):
        print(f"Error: File doesn't appear to be a valid .ppt file: {input_path}")
        sys.exit(1)

    print(f"Converting: {input_path} -> {output_path}")

    # Create temporary directory for conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Convert using LibreOffice
        print("Running LibreOffice conversion...")
        result = subprocess.run(
            [
                'soffice',
                '--headless',
                '--convert-to', 'pptx',
                '--outdir', str(temp_dir_path),
                str(input_path)
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error during conversion:")
            print(result.stderr)
            sys.exit(1)

        # Find the converted file
        converted_files = list(temp_dir_path.glob('*.pptx'))
        if not converted_files:
            print("Error: No .pptx file generated")
            sys.exit(1)

        converted_file = converted_files[0]

        # Move to final destination
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(converted_file), str(output_path))

    print(f"Successfully converted to: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert legacy PowerPoint .ppt files to .pptx format"
    )
    parser.add_argument(
        "input",
        help="Input file (.ppt or .pptx)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output file (default: input with .pptx extension)"
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Convert
    try:
        result_path = convert_to_pptx(input_path, args.output)
        print(f"\nResult: {result_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
