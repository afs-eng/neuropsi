import { redirect } from 'next/navigation'

export default function THCPEditPage({ params }: { params: { id: string } }) {
  redirect(`/dashboard/tests/thcp?application_id=${encodeURIComponent(params.id)}&edit=true`)
}
