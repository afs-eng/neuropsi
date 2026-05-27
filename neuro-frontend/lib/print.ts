export function printCurrentPage() {
  if (typeof window === "undefined") {
    return
  }

  window.print()
}

export function openPrintRoute(path: string) {
  if (typeof window === "undefined") {
    return
  }

  window.open(path, "_blank")
}
