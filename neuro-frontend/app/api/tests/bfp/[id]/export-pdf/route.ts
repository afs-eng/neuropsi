import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function getBackendBaseUrl() {
  return (process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/+$/, "");
}

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  const authorization = request.headers.get("authorization") || "";
  const token = authorization.startsWith("Bearer ") ? authorization.slice(7) : "";

  if (!token) {
    return Response.json({ message: "Token de autenticação ausente." }, { status: 401 });
  }

  const backendBaseUrl = getBackendBaseUrl();
  if (!backendBaseUrl) {
    return Response.json({ message: "URL do backend não configurada." }, { status: 500 });
  }

  const response = await fetch(`${backendBaseUrl}/api/tests/applications/${params.id}/export-pdf`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const body = await response.arrayBuffer();

  return new Response(body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") || "application/pdf",
      "Content-Disposition": response.headers.get("content-disposition") || `inline; filename="BFP-${params.id}.pdf"`,
      "Cache-Control": "no-store",
    },
  });
}
