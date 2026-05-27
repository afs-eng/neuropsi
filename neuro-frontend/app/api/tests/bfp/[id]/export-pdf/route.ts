import { NextRequest } from "next/server";
import { createRequire } from "module";
import { existsSync } from "fs";
import { join } from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function loadPlaywright() {
  const require = createRequire(import.meta.url);
  const moduleCandidates = [
    process.env.PLAYWRIGHT_NODE_PATH,
    join(process.cwd(), ".playwright-runner", "node_modules", "playwright"),
    join(process.cwd(), "neuro-frontend", ".playwright-runner", "node_modules", "playwright"),
    "/home/andre/software/neuro-system/neuro-frontend/.playwright-runner/node_modules/playwright",
  ].filter(Boolean) as string[];

  const browserCandidates = [
    process.env.PLAYWRIGHT_BROWSERS_PATH,
    join(process.cwd(), ".playwright-runner", "ms-playwright"),
    join(process.cwd(), "neuro-frontend", ".playwright-runner", "ms-playwright"),
    "/home/andre/software/neuro-system/neuro-frontend/.playwright-runner/ms-playwright",
  ].filter(Boolean) as string[];

  const modulePath = moduleCandidates.find((candidate) => existsSync(join(candidate, "package.json")));
  const browsersPath = browserCandidates.find((candidate) => existsSync(candidate));

  if (!modulePath) {
    throw new Error(`Playwright não encontrado. Caminhos tentados: ${moduleCandidates.join(", ")}`);
  }

  if (browsersPath) {
    process.env.PLAYWRIGHT_BROWSERS_PATH = browsersPath;
  }

  return require(modulePath) as { chromium: { launch: (options: Record<string, unknown>) => Promise<any> } };
}

function buildFilename(applicationId: string) {
  return `BFP-${applicationId}.pdf`;
}

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  const applicationId = params.id;
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
    const printUrl = new URL(`/print/bfp/${applicationId}`, request.url).toString();

    await page.goto(printUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForFunction(
      () => {
        if (document.querySelector(".a4-print-page")) return true;
        const text = document.body?.innerText || "";
        return text.includes("Resultado do BFP indisponível") || text.includes("Não foi possível carregar");
      },
      undefined,
      { timeout: 30000 }
    );

    const hasPages = await page.locator(".a4-print-page").count();
    if (!hasPages) {
      const pageText = await page.locator("body").innerText().catch(() => "");
      return Response.json(
        { message: pageText || "Não foi possível renderizar o layout do BFP para PDF." },
        { status: 500 }
      );
    }

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
        "Content-Disposition": `inline; filename="${buildFilename(applicationId)}"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return Response.json(
      { message: error instanceof Error ? error.message : "Não foi possível gerar o PDF do BFP." },
      { status: 500 }
    );
  } finally {
    await browser?.close();
  }
}
