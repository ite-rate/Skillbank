// Proven pptxgenjs template for creating a "通识介绍" style deck from scratch.
// Pattern: 16:9 layout, dark-navy/light theme with orange accent, icon-in-card
// layout repeated across slides, footer bar with page numbers.
//
// Usage: NODE_PATH=$(npm root -g) node my_deck.js
// Requires: pptxgenjs, react-icons, react, react-dom, sharp (all global)

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaRobot, FaCode, FaBrain, FaRocket, FaCloud, FaCamera } = require("react-icons/fa");

// === Color palette (modify per topic) ===
const C = {
  navy:   "0F1923",  // dark bg for cover/closing
  dark:   "1A2332",  // slightly lighter dark for cards on dark bg
  orange: "FF6B35",  // accent color
  light:  "F0F2F5",  // light bg for content slides
  white:  "FFFFFF",
  text:   "1A1A2E",  // dark text on light bg
  muted:  "6B7280",  // secondary text
  iceBlue:"E8EDF3",  // alt row in tables
};

const FONT_H = "Calibri";
const FONT_B = "Calibri";
const W = 10, H = 5.625;  // 16:9

// === Icon helper ===
async function iconPng(IconComponent, color = "#FF6B35", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// === Shared elements ===
function addFooter(pres, slide, pageNum, total) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: H - 0.35, w: W, h: 0.35, fill: { color: C.navy }
  });
  slide.addText("Deck Title Here", {
    x: 0.3, y: H - 0.35, w: 4, h: 0.35,
    fontSize: 9, color: C.muted, valign: "middle", margin: 0
  });
  slide.addText(`${pageNum} / ${total}`, {
    x: W - 1.5, y: H - 0.35, w: 1.2, h: 0.35,
    fontSize: 9, color: C.muted, align: "right", valign: "middle", margin: 0
  });
}

function addSectionTag(slide, text) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.35, w: 0.06, h: 0.35, fill: { color: C.orange }
  });
  slide.addText(text, {
    x: 0.68, y: 0.32, w: 4, h: 0.4,
    fontSize: 11, color: C.orange, bold: true, valign: "middle", margin: 0, charSpacing: 3
  });
}

function addTitle(slide, text) {
  slide.addText(text, {
    x: 0.5, y: 0.7, w: 9, h: 0.6,
    fontSize: 32, color: C.text, bold: true, valign: "middle", margin: 0
  });
}

// === Card layout patterns ===
// 2x2 grid of feature cards on light bg
function featureCard2x2(pres, slide, items, startY = 1.55) {
  // items: [{ icon, title, desc }, ...] length 4
  items.forEach((it, i) => {
    const x = 0.5 + (i % 2) * 4.6;
    const y = startY + Math.floor(i / 2) * 1.7;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.3, h: 1.5, fill: { color: C.white },
      shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.08 }
    });
    // Call iconPng async and addImage separately
  });
}

// === Main generation ===
async function generateDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Author";
  pres.title = "Deck Title";

  const TOTAL = 18;

  // Cover slide
  const s1 = pres.addSlide();
  s1.background = { color: C.navy };
  s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 0.08, fill: { color: C.orange } });
  s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: H - 0.08, w: W, h: 0.08, fill: { color: C.orange } });
  const robotIcon = await iconPng(FaRobot);
  s1.addImage({ data: robotIcon, x: 4.25, y: 0.7, w: 1.5, h: 1.5 });
  s1.addText("Title Here", {
    x: 0.5, y: 2.35, w: 9, h: 0.7,
    fontSize: 40, color: C.white, bold: true, align: "center", valign: "middle", margin: 0
  });

  // ... add more slides following the same pattern ...

  await pres.writeFile({ fileName: "output.pptx" });
  console.log("Done: output.pptx");
}

generateDeck().catch(console.error);