export function bearingToCompass(bearing: number): string {
  const dirs = ["B", "ĐB", "Đ", "ĐN", "N", "TN", "T", "TB"]
  const idx = Math.round(bearing / 45) % 8
  return dirs[idx] ?? "—"
}
