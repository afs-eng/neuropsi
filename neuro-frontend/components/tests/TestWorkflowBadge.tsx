import { cn } from "@/lib/utils"
import { getTestWorkflowMeta } from "@/lib/test-report"

export function TestWorkflowBadge({ status, statusDisplay }: { status?: string | null; statusDisplay?: string | null }) {
  const meta = getTestWorkflowMeta(status)
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-widest", meta.className)}>
      {statusDisplay || meta.label}
    </span>
  )
}
