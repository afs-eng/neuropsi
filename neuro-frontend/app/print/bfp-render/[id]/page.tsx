import { BFPReportContent, type BFPApplicationData } from "@/components/tests/BFPReportContent";

interface BFPRenderPageProps {
  params: {
    id: string;
  };
  searchParams?: {
    token?: string;
  };
}

function getApiBaseUrl() {
  return process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://backend:8000";
}

async function getApplication(applicationId: string, token?: string) {
  const response = await fetch(`${getApiBaseUrl().replace(/\/+$/, "")}/api/tests/applications/${applicationId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Falha ao carregar resultado do BFP (${response.status})`);
  }

  return (await response.json()) as BFPApplicationData;
}

export default async function BFPRenderPage({ params, searchParams }: BFPRenderPageProps) {
  try {
    const application = await getApplication(params.id, searchParams?.token);

    return (
      <div className="report-print-shell bg-white p-0">
        <div className="report-print-card mx-auto max-w-none bg-white p-0 shadow-none">
          <div className="report-print-content bg-white p-0">
            <BFPReportContent
              application={application}
              applicationId={params.id}
              evaluationId={application.evaluation_id ? String(application.evaluation_id) : undefined}
              hideActions
            />
          </div>
        </div>
      </div>
    );
  } catch (error: any) {
    return <div className="flex min-h-screen items-center justify-center bg-white px-6 text-center text-sm text-rose-600">{error?.message || "Resultado do BFP indisponível."}</div>;
  }
}
