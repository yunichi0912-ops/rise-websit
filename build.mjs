// 静的デモサイトのビルドスクリプト（依存パッケージなし）
// src/parts/*.html（共通パーツ）と src/pages/*.html（各ページ）を組み立て、ルートに出力します。
// WordPressブロックテーマの parts/ ・ templates/ と同じ考え方の構成です。
//   node build.mjs
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const SRC = "src";
const company = JSON.parse(readFileSync(join(SRC, "data/company.json"), "utf8"));
const part = (name) => readFileSync(join(SRC, "parts", `${name}.html`), "utf8");

// {{company.key}} を置換（display:false の項目は出力しない）
const fillCompany = (html) =>
  html.replace(/\{\{company\.(\w+)\}\}/g, (_, key) => {
    const item = company[key];
    if (!item) throw new Error(`company.${key} is not defined`);
    if (!item.display) return "（非公開）";
    return Array.isArray(item.value) ? item.value.join("／") : item.value;
  });

for (const file of readdirSync(join(SRC, "pages")).filter((f) => f.endsWith(".html"))) {
  let body = readFileSync(join(SRC, "pages", file), "utf8");
  const metaMatch = body.match(/^<!--meta\s+(\{[\s\S]*?\})\s*-->\s*/);
  if (!metaMatch) throw new Error(`${file}: meta comment missing`);
  const meta = JSON.parse(metaMatch[1]);
  body = body.slice(metaMatch[0].length);

  let html = part("layout")
    .replace("{{> head}}", () => part("head"))
    .replace("{{> header}}", () => part("header"))
    .replace("{{> footer}}", () => part("footer"))
    .replace("{{> body}}", () => body)
    .replace(/\{\{> ([\w-]+)\}\}/g, (_, n) => part(n));

  html = html
    .replace(/\{\{title\}\}/g, () => meta.title)
    .replace(/\{\{description\}\}/g, () => meta.description)
    .replace(/\{\{page\}\}/g, meta.page)
    // 現在ページのナビに aria-current を付与
    .replace(new RegExp(`data-nav="${meta.page}"`, "g"), `data-nav="${meta.page}" aria-current="page"`);

  html = fillCompany(html);
  writeFileSync(file, html);
  console.log("built", file);
}
