import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { Loader2, MapPin, AlertTriangle } from "lucide-react";
import { api } from "../services/api";
import type { Building } from "../types/building";

// Bekannter Leaflet+Bundler-Stolperstein: Standard-Icon-Pfade greifen mit Vite
// nicht automatisch, daher explizit auf die gebündelten Bild-Assets zeigen.
const buildingIcon = new L.Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
  className: "building-map-marker-building",
});

const authorityIcon = new L.Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
  className: "building-map-marker-authority",
});

interface AuthorityRef {
  authorityId: string;
  label: string;
}

interface Props {
  building: Building;
  authorityRefs?: AuthorityRef[];
}

export function BuildingMap({ building, authorityRefs = [] }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [areaNote, setAreaNote] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        let lat = building.latitude;
        let lng = building.longitude;
        if (lat == null || lng == null) {
          const coords = await api.geocodeBuilding(building.building_id);
          lat = coords.latitude;
          lng = coords.longitude;
        }
        if (cancelled || !containerRef.current) return;

        const map = L.map(containerRef.current).setView([lat, lng], 13);
        mapRef.current = map;

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende',
          maxZoom: 19,
        }).addTo(map);

        L.marker([lat, lng], { icon: buildingIcon })
          .addTo(map)
          .bindPopup(`<strong>${building.street} ${building.house_number}</strong><br/>${building.city}`);

        // Flächengleicher Kreis nur, wenn echte Gemeindeflächendaten vorliegen –
        // sonst würde ein erfundener Radius eine falsche Genauigkeit vortäuschen.
        if (building.ags) {
          try {
            const areaInfo = await api.getAdministrativeUnitArea(building.ags);
            if (!cancelled && areaInfo.approx_radius_meters) {
              L.circle([lat, lng], {
                radius: areaInfo.approx_radius_meters,
                color: "#005C83",
                fillColor: "#005C83",
                fillOpacity: 0.08,
                weight: 1.5,
                dashArray: "4 4",
              })
                .addTo(map)
                .bindPopup(
                  `Flächengleicher Kreis für ${areaInfo.municipality_name} (${areaInfo.area_km2} km²) – <strong>keine echte Amtsbezirksgrenze</strong>, nur eine grobe Orientierung.`
                );
              setAreaNote(
                `Kreis zeigt die Fläche von ${areaInfo.municipality_name} als Näherung, nicht die echte Grenze.`
              );
            } else if (!cancelled) {
              setAreaNote("Für diese Gemeinde liegen keine Flächendaten vor – kein Kreis eingezeichnet.");
            }
          } catch {
            if (!cancelled) setAreaNote("Für diese Gemeinde liegen keine Flächendaten vor – kein Kreis eingezeichnet.");
          }
        }

        // Behörden-Standorte (best effort: einzelne Fehlschläge überspringen,
        // nicht die ganze Karte blockieren)
        if (authorityRefs.length > 0) {
          const authorities = await api.getAuthorities(authorityRefs.map((r) => r.authorityId));
          const authorityById = Object.fromEntries(authorities.map((a) => [a.authority_id, a]));
          const bounds = L.latLngBounds([[lat, lng]]);

          await Promise.all(
            authorityRefs.map(async ({ authorityId, label }) => {
              const authority = authorityById[authorityId];
              if (!authority) return;
              try {
                const loc = await api.getAuthorityLocation(authorityId);
                if (cancelled || !mapRef.current) return;
                L.marker([loc.latitude, loc.longitude], { icon: authorityIcon })
                  .addTo(mapRef.current)
                  .bindPopup(`<strong>${authority.authority_name}</strong><br/>${label}`);
                bounds.extend([loc.latitude, loc.longitude]);
              } catch {
                // Behörde ohne verwertbare Adresse -> einfach nicht einzeichnen
              }
            })
          );

          if (!cancelled && mapRef.current) {
            mapRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
          }
        }
      } catch {
        if (!cancelled) setError("Adresse konnte nicht auf der Karte lokalisiert werden.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [building.building_id]);

  return (
    <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
      <div className="relative h-72 w-full">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-surface text-sm text-ink-faint">
            <Loader2 size={16} className="animate-spin" />
            Standort wird ermittelt…
          </div>
        )}
        {error && (
          <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-surface px-4 text-center text-sm text-status-conflict">
            <AlertTriangle size={16} />
            {error}
          </div>
        )}
        <div ref={containerRef} className="h-full w-full" />
      </div>
      {areaNote && (
        <div className="flex items-start gap-1.5 border-t border-line px-3.5 py-2 text-xs text-ink-faint">
          <MapPin size={13} className="mt-0.5 shrink-0" />
          {areaNote}
        </div>
      )}
    </div>
  );
}
