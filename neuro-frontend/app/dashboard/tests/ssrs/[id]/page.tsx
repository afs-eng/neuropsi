import { redirect } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  redirect(`/dashboard/tests/ssrs/${params.id}/result`);
}
