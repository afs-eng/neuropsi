import QuickTestPageClient from "./QuickTestPageClient";

interface QuickTestPageProps {
  searchParams?: {
    test?: string;
  };
}

export default function QuickTestPage({ searchParams }: QuickTestPageProps) {
  return <QuickTestPageClient initialTest={searchParams?.test || ""} />;
}
