// Convierte los SVG de docs/final/diagramas en PNG (para la PPT). Uso: node tools/diagramas/render_png.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const dir = path.join(__dirname, '..', '..', 'docs', 'final', 'diagramas');
  const browser = await chromium.launch();
  for (const file of fs.readdirSync(dir).filter((f) => f.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(dir, file), 'utf8');
    const [, w, h] = svg.match(/width="(\d+)" height="(\d+)"/);
    const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) }, deviceScaleFactor: 2 });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.screenshot({ path: path.join(dir, file.replace('.svg', '.png')) });
    await page.close();
    console.log('PNG', file.replace('.svg', '.png'));
  }
  await browser.close();
})();
