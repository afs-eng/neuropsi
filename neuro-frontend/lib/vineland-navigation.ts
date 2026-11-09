export function vinelandQuestionnaireUrl(evaluationId: number, applicationId?: number) {
  const query = new URLSearchParams({ evaluation_id: String(evaluationId), entry: 'items' })
  if (applicationId !== undefined) query.set('application_id', String(applicationId))
  return `/dashboard/tests/vineland?${query}`
}
