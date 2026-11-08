// node shoot.mjs <page.html> <outprefix> [WxH ...] : one PNG per slide per viewport, plus console errors
import { createRequire } from "module";
import { homedir } from "os";
const req = createRequire(homedir() + "/.cache/hairline-look/");
const { chromium } = req("playwright-core");
const [, , file, prefix, ...sizes] = process.argv;
const vps = (sizes.length ? sizes : ["1600x900", "390x844"]).map((s) => s.split("x").map(Number));
const browser = await chromium.launch({ channel: "chrome" }).catch(() => chromium.launch());
for (const [w, h] of vps) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: w < 600 ? 2 : 1 });
  const errs = [];
  page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") errs.push(m.text()); });
  page.on("pageerror", (e) => errs.push(String(e)));
  await page.goto("file://" + file + (process.env.Q || ""));
  await page.waitForTimeout(1500);
  for (let k = 0; k < Number(process.env.KEYS || 0); k++) await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(300);
  const n = await page.evaluate(() => document.querySelectorAll(".slide").length);
  if (w < 600 || n === 0) {
    await page.screenshot({ path: `${prefix}-${w}-full.png`, fullPage: true });
  } else {
    for (let i = 0; i < n; i++) {
      await page.evaluate((i) => { document.documentElement.style.scrollBehavior = "auto"; scrollTo(0, document.querySelectorAll(".slide")[i].offsetTop); }, i);
      await page.waitForTimeout(1600);
      await page.screenshot({ path: `${prefix}-${w}-${String(i + 1).padStart(2, "0")}.png` });
    }
  }
  const over = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  console.log(`${w}x${h}: ${n} slides, horizontal overflow ${over}px, console: ${errs.length ? errs.join(" | ") : "clean"}`);
  await page.close();
}
await browser.close();
