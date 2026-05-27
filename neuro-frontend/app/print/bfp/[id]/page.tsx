import BFPPrintPageClient from "./BFPPrintPageClient";

interface BFPPrintPageProps {
  params: {
    id: string;
  };
  searchParams?: {
    autoprint?: string;
    render?: string;
  };
}

export default function BFPPrintPage({ params, searchParams }: BFPPrintPageProps) {
  return (
    <BFPPrintPageClient
      applicationId={params.id}
      autoprint={searchParams?.autoprint === "1"}
      apiMode={searchParams?.render === "pdf" ? "proxy" : "direct"}
    />
  );
}
