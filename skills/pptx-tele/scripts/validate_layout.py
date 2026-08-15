#!/usr/bin/env python3
"""
Validate PowerPoint presentation layout using image analysis and text overflow detection.

This script provides two types of validation:
1. Text overflow detection: Uses python-pptx inventory to detect text exceeding shape bounds
2. Image-based analysis: Converts slides to images for visual layout inspection

Usage:
    python validate_layout.py presentation.pptx [--check-text-overflow] [--check-all] [--output report.json]

Examples:
    python validate_layout.py presentation.pptx --check-text-overflow
    python validate_layout.py presentation.pptx --check-all --output report.json

Output:
    - JSON report with detected issues for each slide
    - Console summary of issues found
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional


class TextOverflowDetector:
    """Detect text overflow in PowerPoint shapes using python-pptx inventory."""

    def __init__(self, pptx_path: Path):
        """Initialize detector.

        Args:
            pptx_path: Path to PowerPoint file
        """
        self.pptx_path = pptx_path
        self.issues: Dict[str, List[Dict[str, Any]]] = {}

    def detect(self) -> Dict[str, List[Dict[str, Any]]]:
        """Detect text overflow in all slides.

        Returns:
            Dict mapping slide_key to list of issue dicts.
        """
        try:
            from inventory import extract_text_inventory
            from pptx import Presentation
        except ImportError:
            print("ERROR: Required packages not installed. Run: pip install python-pptx Pillow")
            return self.issues

        try:
            prs = Presentation(str(self.pptx_path))
            inventory = extract_text_inventory(self.pptx_path, prs)
        except Exception as e:
            print(f"ERROR: Failed to read presentation: {e}")
            return self.issues

        total_issues = 0

        for slide_key, shapes in inventory.items():
            slide_issues = []

            for shape_key, shape_data in shapes.items():
                # Check frame overflow (text exceeding shape bounds)
                if shape_data.frame_overflow_bottom is not None and shape_data.frame_overflow_bottom > 0.01:
                    text_preview = ""
                    if shape_data.paragraphs:
                        text_preview = shape_data.paragraphs[0].text
                        if len(text_preview) > 60:
                            text_preview = text_preview[:60] + "..."

                    issue = {
                        "type": "text_overflow",
                        "severity": "HIGH",
                        "description": (
                            f"Text overflows shape by {shape_data.frame_overflow_bottom:.2f}\" "
                            f"(shape: {shape_key}, size: {shape_data.width:.1f}\" x {shape_data.height:.1f}\")"
                        ),
                        "text_preview": text_preview,
                        "shape": shape_key,
                        "overflow_inches": round(shape_data.frame_overflow_bottom, 3),
                        "suggestion": (
                            "Reduce text content, decrease font size, or enlarge the shape. "
                            "For table cells, consider abbreviating the text or using a smaller font."
                        ),
                    }
                    slide_issues.append(issue)
                    total_issues += 1

                # Check for empty shapes that might have lost content
                if shape_data.paragraphs and all(p.text == "" for p in shape_data.paragraphs):
                    # Only warn if shape has a reasonable size (not tiny decorative shapes)
                    if shape_data.width > 0.5 and shape_data.height > 0.3:
                        issue = {
                            "type": "empty_shape",
                            "severity": "LOW",
                            "description": (
                                f"Shape {shape_key} appears empty "
                                f"(size: {shape_data.width:.1f}\" x {shape_data.height:.1f}\")"
                            ),
                            "shape": shape_key,
                            "suggestion": (
                                "This shape may have lost its content during editing. "
                                "Verify it should be empty."
                            ),
                        }
                        slide_issues.append(issue)

                # Check for potential text truncation in small shapes
                if shape_data.paragraphs:
                    for para in shape_data.paragraphs:
                        if para.text and len(para.text) > 3:
                            # Estimate if text might be truncated based on shape size and font
                            font_size = para.font_size or 12.0
                            # Rough estimate: chars per line = width_inches * 72 / font_size
                            chars_per_line = (shape_data.width * 72) / font_size
                            # Lines available = height_inches * 72 / (font_size * 1.2)
                            lines_available = (shape_data.height * 72) / (font_size * 1.2)
                            max_chars = int(chars_per_line * lines_available)

                            # Chinese characters are roughly 1.5x wider than Latin
                            chinese_chars = sum(1 for c in para.text if '\u4e00' <= c <= '\u9fff')
                            latin_chars = len(para.text) - chinese_chars
                            estimated_width = chinese_chars * 1.5 + latin_chars * 0.6

                            if estimated_width > max_chars * 1.1 and shape_data.frame_overflow_bottom is None and shape_data.frame_overflow_bottom != 0:
                                issue = {
                                    "type": "potential_truncation",
                                    "severity": "MEDIUM",
                                    "description": (
                                        f"Text in {shape_key} may be truncated: "
                                        f"\"{para.text[:40]}{'...' if len(para.text) > 40 else ''}\" "
                                        f"(~{int(estimated_width)} chars estimated, ~{max_chars} chars fit)"
                                    ),
                                    "shape": shape_key,
                                    "text_preview": para.text[:80],
                                    "suggestion": (
                                        "Consider shortening the text or enlarging the shape. "
                                        "Current text may overflow or be cut off."
                                    ),
                                }
                                slide_issues.append(issue)

            if slide_issues:
                self.issues[slide_key] = slide_issues

        if total_issues > 0:
            print(f"\nText overflow detection found {total_issues} issue(s) across {len(self.issues)} slide(s)")
        else:
            print("\nText overflow detection: No issues found")

        return self.issues


class LayoutValidator:
    """Validate presentation layout using image analysis."""

    # Common issues to check
    ISSUE_TYPES = {
        "text_cutoff": "Text appears to be cut off at edges",
        "text_overlap": "Text elements may be overlapping",
        "position_issue": "Content too close to slide boundaries",
        "contrast_issue": "Insufficient contrast between text and background",
        "spacing_issue": "Uneven or inappropriate spacing",
        "alignment_issue": "Elements appear misaligned",
        "text_overflow": "Text exceeds shape boundaries",
        "potential_truncation": "Text may be truncated in shape",
        "empty_shape": "Shape appears to have no content",
    }

    def __init__(self, pptx_path: Path, dpi: int = 300):
        """Initialize validator.

        Args:
            pptx_path: Path to PowerPoint file
            dpi: Resolution for image conversion (higher = better analysis)
        """
        self.pptx_path = pptx_path
        self.dpi = dpi
        self.slides: List[Path] = []
        self.issues: Dict[int, List[Dict[str, Any]]] = {}

    def convert_to_images(self, temp_dir: Path) -> List[Path]:
        """Convert PPTX to individual slide images.

        Returns:
            List of image file paths (one per slide)
        """
        print(f"Converting {self.pptx_path} to images at {self.dpi} DPI...")

        # Convert to PDF first
        pdf_path = temp_dir / f"{self.pptx_path.stem}.pdf"
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf",
             "--outdir", str(temp_dir), str(self.pptx_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0 or not pdf_path.exists():
            raise RuntimeError(f"PDF conversion failed: {result.stderr}")

        # Convert PDF to images
        result = subprocess.run(
            ["pdftoppm", "-jpeg", "-r", str(self.dpi), str(pdf_path),
             str(temp_dir / "slide")],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Image conversion failed: {result.stderr}")

        # Get all slide images
        slide_images = sorted(temp_dir.glob("slide-*.jpg"))
        print(f"Generated {len(slide_images)} slide images")

        return slide_images

    def analyze_slide(self, image_path: Path, slide_num: int) -> List[Dict[str, Any]]:
        """Analyze a single slide image for layout issues.

        This is a placeholder for the actual image analysis.
        In production, this would use an MCP image analysis tool.

        Args:
            image_path: Path to slide image
            slide_num: Slide number (1-based)

        Returns:
            List of detected issues
        """
        issues = []

        # Placeholder: In production, use MCP tool to analyze image
        # Example:
        # analysis = mcp_analyze_image(image_path, prompt="检查布局问题...")
        # issues = parse_analysis(analysis)

        # For now, return empty list (tool will be integrated when called)
        return issues

    def validate(self) -> Dict[str, Any]:
        """Run full validation on the presentation.

        Returns:
            Validation report as dictionary
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Convert to images
            self.slides = self.convert_to_images(temp_path)

            # Analyze each slide
            print("Analyzing slides for layout issues...")
            for i, slide_image in enumerate(self.slides, start=1):
                print(f"  Analyzing slide {i}/{len(self.slides)}...", end="\r")
                issues = self.analyze_slide(slide_image, i)
                if issues:
                    self.issues[i] = issues

            print()  # New line after progress

        # Generate report
        report = {
            "presentation": str(self.pptx_path),
            "total_slides": len(self.slides),
            "slides_with_issues": len(self.issues),
            "issues": {
                f"slide_{num}": issues
                for num, issues in self.issues.items()
            },
            "summary": self._generate_summary()
        }

        return report

    def _generate_summary(self) -> Dict[str, int]:
        """Generate summary of issues by type."""
        summary = {issue_type: 0 for issue_type in self.ISSUE_TYPES}

        for slide_issues in self.issues.values():
            for issue in slide_issues:
                issue_type = issue.get("type")
                if issue_type in summary:
                    summary[issue_type] += 1

        return summary

    def print_report(self, report: Dict[str, Any]):
        """Print formatted report to console."""
        print("\n" + "="*60)
        print("LAYOUT VALIDATION REPORT")
        print("="*60)
        print(f"Presentation: {report['presentation']}")
        print(f"Total slides: {report['total_slides']}")
        print(f"Slides with issues: {report['slides_with_issues']}")

        if report['slides_with_issues'] > 0:
            print("\nISSUE SUMMARY:")
            for issue_type, count in report['summary'].items():
                if count > 0:
                    print(f"  - {self.ISSUE_TYPES[issue_type]}: {count} occurrence(s)")

            print("\nDETAILED ISSUES:")
            for slide_id, issues in sorted(report['issues'].items()):
                print(f"\n{slide_id}:")
                for issue in issues:
                    print(f"  [{issue.get('severity', 'MEDIUM')}] {issue.get('description', 'Unknown issue')}")
                    if 'suggestion' in issue:
                        print(f"    Suggestion: {issue['suggestion']}")
        else:
            print("\nNo layout issues detected!")

        print("="*60 + "\n")


def merge_reports(image_report: Dict[str, Any], overflow_report: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Merge image-based and text overflow reports into a unified report.

    Args:
        image_report: Report from LayoutValidator
        overflow_report: Report from TextOverflowDetector (slide_key -> issues)

    Returns:
        Merged report
    """
    merged_issues = {}

    # Add image-based issues (keyed by slide_N)
    for slide_id, issues in image_report.get("issues", {}).items():
        merged_issues[slide_id] = issues

    # Add text overflow issues (keyed by slide-N, convert to slide_N)
    for slide_key, issues in overflow_report.items():
        # Convert "slide-0" to "slide_0" for consistency
        slide_id = slide_key.replace("-", "_")
        if slide_id in merged_issues:
            merged_issues[slide_id].extend(issues)
        else:
            merged_issues[slide_id] = issues

    # Recount
    slides_with_issues = sum(1 for issues in merged_issues.values() if issues)
    summary = {t: 0 for t in LayoutValidator.ISSUE_TYPES}
    for issues in merged_issues.values():
        for issue in issues:
            t = issue.get("type")
            if t in summary:
                summary[t] += 1

    return {
        "presentation": image_report.get("presentation", ""),
        "total_slides": image_report.get("total_slides", 0),
        "slides_with_issues": slides_with_issues,
        "issues": merged_issues,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate PowerPoint presentation layout"
    )
    parser.add_argument(
        "input",
        help="Input PowerPoint file (.pptx)"
    )
    parser.add_argument(
        "--check-text-overflow",
        action="store_true",
        help="Check for text overflow and truncation using python-pptx inventory (no external tools needed)"
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Enable all checks including image analysis and text overflow"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON report file"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Image resolution for analysis (default: 300)"
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists() or input_path.suffix.lower() != ".pptx":
        print(f"Error: Invalid PowerPoint file: {args.input}")
        sys.exit(1)

    # Determine which checks to run
    run_overflow = args.check_text_overflow or args.check_all
    run_image = args.check_all

    # Run text overflow detection
    overflow_report = {}
    if run_overflow:
        print("Running text overflow detection...")
        detector = TextOverflowDetector(input_path)
        overflow_report = detector.detect()

    # Run image-based validation
    image_report = {
        "presentation": str(input_path),
        "total_slides": 0,
        "slides_with_issues": 0,
        "issues": {},
        "summary": {},
    }
    if run_image:
        try:
            validator = LayoutValidator(input_path, args.dpi)
            image_report = validator.validate()
        except Exception as e:
            print(f"Warning: Image-based validation failed: {e}")
            print("Falling back to text overflow detection only.")

    # Merge and output
    if run_overflow and run_image:
        final_report = merge_reports(image_report, overflow_report)
    elif run_overflow:
        # Build report from overflow data only
        total_slides = len(overflow_report)
        slides_with_issues = sum(1 for issues in overflow_report.values() if issues)
        summary = {t: 0 for t in LayoutValidator.ISSUE_TYPES}
        for issues in overflow_report.values():
            for issue in issues:
                t = issue.get("type")
                if t in summary:
                    summary[t] += 1
        final_report = {
            "presentation": str(input_path),
            "total_slides": total_slides,
            "slides_with_issues": slides_with_issues,
            "issues": {k.replace("-", "_"): v for k, v in overflow_report.items()},
            "summary": summary,
        }
    else:
        final_report = image_report

    # Print report
    if run_image:
        LayoutValidator(input_path).print_report(final_report)
    else:
        # Simple print for overflow-only mode
        print("\n" + "="*60)
        print("TEXT OVERFLOW DETECTION REPORT")
        print("="*60)
        print(f"Presentation: {final_report['presentation']}")
        print(f"Slides with issues: {final_report['slides_with_issues']}")

        if final_report['slides_with_issues'] > 0:
            print("\nISSUE SUMMARY:")
            for issue_type, count in final_report['summary'].items():
                if count > 0:
                    desc = LayoutValidator.ISSUE_TYPES.get(issue_type, issue_type)
                    print(f"  - {desc}: {count} occurrence(s)")

            print("\nDETAILED ISSUES:")
            for slide_id, issues in sorted(final_report['issues'].items()):
                print(f"\n{slide_id}:")
                for issue in issues:
                    print(f"  [{issue.get('severity', 'MEDIUM')}] {issue.get('description', 'Unknown issue')}")
                    if 'suggestion' in issue:
                        print(f"    Suggestion: {issue['suggestion']}")
        else:
            print("\nNo text overflow issues detected!")

        print("="*60 + "\n")

    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to: {output_path}")

    # Exit with error code if issues found
    if final_report['slides_with_issues'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
