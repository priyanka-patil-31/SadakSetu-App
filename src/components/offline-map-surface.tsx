/**
 * Clean local vector road grid surface for offline operation.
 * Rendered as a fallback or offline mode background without any external network tile requests.
 */
export function OfflineMapSurface() {
  return (
    <div className="offline-map-surface pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <div className="absolute inset-0 offline-map-road offline-map-road-one" />
      <div className="absolute inset-0 offline-map-road offline-map-road-two" />
      <div className="absolute inset-0 offline-map-road offline-map-road-three" />
      <div className="absolute inset-0 offline-map-road offline-map-road-four" />
    </div>
  )
}
