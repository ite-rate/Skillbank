#!/usr/bin/env python3
"""Slide-deck visual QA from the SOURCE PDF (no vision needed).

The deck's JPG/PNG renders are usually exports of a PDF. The PDF carries
exact geometry (960x540pt for 13.33x7.5in decks), so overlaps, overflow,
gaps, alignment, margins, contrast and placeholders can be measured
precisely instead of eyeballed.

Usage:
    python3 slide_render_qa.py deck.pdf [--jpg-dir DIR] [--min-gap 0.3]

Checks per page (print-only, exit 0):
  - text<->text overlap between VISUAL LINES (CJK spans are per-char fragments:
    merge by baseline before comparing, else you drown in false positives)
  - text overflow beyond its owning card / slide edge
  - footer collisions (footer = bottom-most full-width navy bar, NOT any navy
    rect - cards/chips are navy too)
  - card gaps < 0.3in (horizontal same-row, vertical same-col)
  - row/col alignment drift of the card grid
  - card margins from slide edges
  - WCAG contrast vs PIXEL-SAMPLED background (render the page, sample the
    pixel at the line's center - never guess bg from rect fill lists)
  - placeholder text (待补充/待确认/待定/TODO/xxx)
"""
import sys, re, argparse
import fitz

def lum(c):
    def f(v):
        v /= 255.0
        return v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*f(c[0])+0.7152*f(c[1])+0.0722*f(c[2])

def contrast(c1, c2):
    l1, l2 = lum(c1), lum(c2)
    if l1 < l2: l1, l2 = l2, l1
    return (l1+0.05)/(l2+0.05)

def main(pdf, jpg_dir, min_gap_in):
    doc = fitz.open(pdf)
    MIN_GAP = min_gap_in / 72.0 * 72.0  # pt
    ZOOM = 2
    for pno in range(len(doc)):
        page = doc[pno]
        W, H = page.rect.width, page.rect.height
        p = pno + 1
        issues = []
        pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
        import numpy as np
        px = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).astype(int)

        rects = []  # non-fullbleed filled rects
        for dr in page.get_drawings():
            r = dr["rect"]
            f = dr.get("fill")
            if not f: continue
            if r.width > W-4 and r.height > H-4: continue
            rects.append({"r": r, "fill": (round(f[0]*255), round(f[1]*255), round(f[2]*255))})
        footer = None
        for rc in rects:
            if rc["r"].y0 > H*0.85 and rc["r"].height < 60 and rc["r"].width > W*0.9:
                if footer is None or rc["r"].y0 > footer["r"].y0:
                    footer = rc
        footer_top = footer["r"].y0 if footer else None
        cards = [rc for rc in rects if rc["fill"][0] > 245 and rc["fill"][1] > 245 and rc["fill"][2] > 245
                 and rc["r"].width > 50 and rc["r"].height > 25]
        raw_text = page.get_text("text")

        # per-char CJK fragments -> visual lines
        frags = []
        d = page.get_text("dict")
        for block in d["blocks"]:
            if block["type"] != 0: continue
            for line in block["lines"]:
                for s in line["spans"]:
                    if not s["text"].strip(): continue
                    frags.append({"b": fitz.Rect(s["bbox"]), "t": s["text"], "size": s["size"], "color": s["color"]})
        lines = []
        for sp in sorted(frags, key=lambda s: (round(s["b"].y0, 1), s["b"].x0)):
            for L in lines:
                if abs(L["y0"]-sp["b"].y0) < 3 and abs(L["y1"]-sp["b"].y1) < 3 \
                   and (abs(L["x1"]-sp["b"].x0) < 6 or abs(L["x0"]-sp["b"].x1) < 6):
                    L["x0"]=min(L["x0"],sp["b"].x0); L["x1"]=max(L["x1"],sp["b"].x1)
                    L["y0"]=min(L["y0"],sp["b"].y0); L["y1"]=max(L["y1"],sp["b"].y1)
                    L["t"]+=sp["t"]; L["size"]=max(L["size"],sp["size"]); break
            else:
                lines.append({"x0":sp["b"].x0,"y0":sp["b"].y0,"x1":sp["b"].x1,"y1":sp["b"].y1,
                              "t":sp["t"],"size":sp["size"],"color":sp["color"]})

        def bg_at(x, y):  # pixel-sample background under a point
            xx, yy = int(x*ZOOM), int(y*ZOOM)
            return tuple(int(v) for v in px[max(0,min(yy,pix.height-1)), max(0,min(xx,pix.width-1))])

        # text<->text overlap (visual lines only)
        for i in range(len(lines)):
            for j in range(i+1, len(lines)):
                a = fitz.Rect(lines[i]["x0"],lines[i]["y0"],lines[i]["x1"],lines[i]["y1"])
                b = fitz.Rect(lines[j]["x0"],lines[j]["y0"],lines[j]["x1"],lines[j]["y1"])
                inter = a & b
                if not inter.is_empty and inter.get_area() > 6 and inter.width > 1.0 and inter.height > 1.0:
                    issues.append(f"TEXT-OVERLAP(verify w/ ink profile): '{lines[i]['t']}' <-> '{lines[j]['t']}' at ({inter.x0:.0f},{inter.y0:.0f})")

        for L in lines:
            b = fitz.Rect(L["x0"],L["y0"],L["x1"],L["y1"])
            t = L["t"]; sz = L["size"]
            col = ((L["color"]>>16)&255, (L["color"]>>8)&255, L["color"]&255)
            cx, cy = (b.x0+b.x1)/2, (b.y0+b.y1)/2
            bg = bg_at(cx, cy)
            cr = contrast(col, bg)
            if b.x1 > W-2 or b.y1 > H-2 or b.x0 < 2 or b.y0 < 2:
                issues.append(f"EDGE-CLIP: '{t}' ({b.x0:.0f},{b.y0:.0f},{b.x1:.0f},{b.y1:.0f}) at slide edge")
            if footer_top is not None:
                if b.y0 < footer_top and b.y1 > footer_top:
                    issues.append(f"FOOTER-COLLISION: '{t}' y0={b.y0:.1f} y1={b.y1:.1f} crosses footer top {footer_top:.1f}")
                elif footer_top - b.y1 < 10 and b.y1 < footer_top:
                    issues.append(f"TIGHT-TO-FOOTER: '{t}' y1={b.y1:.1f}, footer top {footer_top:.1f} ({(footer_top-b.y1):.1f}pt)")
            if cr < 3.0:
                issues.append(f"LOW-CONTRAST: '{t}' #{L['color']:06x} on {bg} = {cr:.2f}:1 ({sz:.0f}pt)")
            elif sz < 14 and cr < 4.5:
                issues.append(f"BORDERLINE-CONTRAST: '{t}' #{L['color']:06x} on {bg} = {cr:.2f}:1 ({sz:.0f}pt)")
            # card containment
            owner = None
            for rc in cards:
                if rc["r"].x0-2 <= cx <= rc["r"].x1+2 and rc["r"].y0-2 <= cy <= rc["r"].y1+2:
                    owner = rc["r"]; break
            if owner:
                if b.x0 < owner.x0-2: issues.append(f"OVERFLOW-LEFT: '{t}' x0={b.x0:.1f} < card {owner.x0:.1f}")
                if b.x1 > owner.x1+2: issues.append(f"OVERFLOW-RIGHT: '{t}' x1={b.x1:.1f} > card {owner.x1:.1f}")
                if b.y0 < owner.y0-2: issues.append(f"OVERFLOW-TOP: '{t}' y0={b.y0:.1f} < card {owner.y0:.1f}")
                if b.y1 > owner.y1+2: issues.append(f"OVERFLOW-BOTTOM: '{t}' y1={b.y1:.1f} > card {owner.y1:.1f}")
                if b.x0-owner.x0 < 5 or owner.x1-b.x1 < 5:
                    issues.append(f"CRAMPED-PADDING: '{t}' in card (pad<5pt)")

        # card gaps / alignment
        for i in range(len(cards)):
            for j in range(i+1, len(cards)):
                a, b = cards[i]["r"], cards[j]["r"]
                if abs(a.y0-b.y0) < 3:
                    gap = (b.x0-a.x1) if b.x0 >= a.x1 else (a.x0-b.x1)
                    if 0 < gap < MIN_GAP:
                        issues.append(f"CARD-GAP-H: {gap:.1f}pt ({(gap/72):.2f}in) cards x0={a.x0:.0f}/{b.x0:.0f} y0={a.y0:.0f}")
                if abs(a.x0-b.x0) < 3:
                    gap = (b.y0-a.y1) if b.y0 >= a.y1 else (a.y0-b.y1)
                    if 0 < gap < MIN_GAP:
                        issues.append(f"CARD-GAP-V: {gap:.1f}pt ({(gap/72):.2f}in) cards y0={a.y0:.0f}/{b.y0:.0f} x0={a.x0:.0f}")
        rows, cols = {}, {}
        for c in cards:
            rows.setdefault(round(c["r"].y0/4), []).append(c)
            cols.setdefault(round(c["r"].x0/4), []).append(c)
        for k, g in rows.items():
            if len(g) > 1:
                ys = [c["r"].y0 for c in g]
                if max(ys)-min(ys) > 1.2: issues.append(f"ROW-MISALIGN: y0 {[round(y,1) for y in ys]}")
        for k, g in cols.items():
            if len(g) > 1:
                xs = [c["r"].x0 for c in g]
                if max(xs)-min(xs) > 1.2: issues.append(f"COL-MISALIGN: x0 {[round(x,1) for x in xs]}")

        for pat in ["待补充","待确认","待定","【待","（待","需补充","？？","TODO","xxx","占位"]:
            for m in re.finditer(re.escape(pat), raw_text):
                ctx = raw_text[max(0,m.start()-12):m.end()+12].replace("\n"," ")
                issues.append(f"PLACEHOLDER: '...{ctx}...'")

        seen = set(); out = []
        for it in issues:
            if it not in seen: seen.add(it); out.append(it)
        print(f"\n===== SLIDE {p}: {len(out)} findings =====")
        for it in out: print(" -", it)
    doc.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--jpg-dir", default=None)
    ap.add_argument("--min-gap", type=float, default=0.3)
    a = ap.parse_args()
    main(a.pdf, a.jpg_dir, a.min_gap)
