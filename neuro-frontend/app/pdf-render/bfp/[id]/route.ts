import { NextRequest } from "next/server";
import { existsSync } from "fs";
import { join } from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function loadPlaywright() {
  const runtimeRequire = eval("require") as NodeRequire;
  const moduleCandidates = [
    join(process.cwd(), ".playwright-runner", "node_modules", "playwright"),
    join(process.cwd(), "neuro-frontend", ".playwright-runner", "node_modules", "playwright"),
    "/home/andre/software/neuro-system/neuro-frontend/.playwright-runner/node_modules/playwright",
    process.env.PLAYWRIGHT_NODE_PATH,
  ].filter(Boolean) as string[];
  const browsersPath = [
    join(process.cwd(), ".playwright-runner", "ms-playwright"),
    join(process.cwd(), "neuro-frontend", ".playwright-runner", "ms-playwright"),
    "/home/andre/software/neuro-system/neuro-frontend/.playwright-runner/ms-playwright",
    process.env.PLAYWRIGHT_BROWSERS_PATH,
  ].find((candidate) => Boolean(candidate) && existsSync(candidate as string));
  const modulePath = moduleCandidates.find((candidate) => existsSync(join(candidate, "package.json")));

  if (!modulePath) {
    throw new Error(`Playwright não encontrado. Caminhos tentados: ${moduleCandidates.join(", ")}`);
  }

  if (browsersPath) {
    process.env.PLAYWRIGHT_BROWSERS_PATH = browsersPath as string;
  }

  return runtimeRequire(modulePath) as { chromium: { launch: (options: Record<string, unknown>) => Promise<any> } };
}

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  const authorization = request.headers.get("authorization") || "";
  const token = authorization.startsWith("Bearer ") ? authorization.slice(7) : "";

  if (!token) {
    return Response.json({ message: "Token de autenticação ausente." }, { status: 401 });
  }

  let browser;
  try {
    const { chromium } = loadPlaywright();
    browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
    const context = await browser.newContext({ colorScheme: "light" });
    await context.addInitScript((authToken: string) => {
      window.localStorage.setItem("token", authToken);
    }, token);

    const page = await context.newPage();
    const printUrl = new URL(`/print/bfp-render/${params.id}?token=${encodeURIComponent(token)}`, request.url).toString();
    await page.goto(printUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForFunction(() => document.querySelector(".a4-print-page"), undefined, { timeout: 30000 });
    await page.emulateMedia({ media: "print" });
    const pdf = await page.pdf({
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: false,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    });

    return new Response(pdf, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `inline; filename="BFP-${params.id}.pdf"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return Response.json({ message: error instanceof Error ? error.message : "Erro ao gerar PDF." }, { status: 500 });
  } finally {
    await browser?.close();
  }
}
