import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("AI 오피스 첫 화면을 서버에서 렌더링한다", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /AI Office/);
  assert.match(html, /오늘 업무 시작하기/);
  assert.match(html, /라이브 오피스/);
  assert.match(html, /대표 할 일/);
});

test("회사 설정과 화면 코드가 연결돼 있다", async () => {
  const [config, page, layout] = await Promise.all([
    readFile(new URL("../company.config.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  ]);

  assert.match(config, /export const COMPANY/);
  assert.match(page, /COMPANY/);
  assert.match(layout, /COMPANY\.pageTitle/);
  assert.match(layout, /lang="ko"/);
});
