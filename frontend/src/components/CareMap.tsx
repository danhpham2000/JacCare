import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { MapPinned } from "lucide-react";
import type { CarePlan } from "../types/care";

type Props = {
  plan: CarePlan;
};

type MapPoint = {
  id: string;
  latitude: number;
  longitude: number;
  title: string;
  subtitle: string;
  accentClass: string;
};

const userIcon = L.divIcon({
  className: "careroute-map-marker",
  html: '<span class="careroute-map-marker__dot careroute-map-marker__dot--user"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const clinicIcon = L.divIcon({
  className: "careroute-map-marker",
  html: '<span class="careroute-map-marker__dot careroute-map-marker__dot--clinic"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const backupIcon = L.divIcon({
  className: "careroute-map-marker",
  html: '<span class="careroute-map-marker__dot careroute-map-marker__dot--backup"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const pharmacyIcon = L.divIcon({
  className: "careroute-map-marker",
  html: '<span class="careroute-map-marker__dot careroute-map-marker__dot--pharmacy"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

export function CareMap({ plan }: Props) {
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerLayerRef = useRef<L.LayerGroup | null>(null);

  const points = useMemo<MapPoint[]>(() => {
    const nextPoints: MapPoint[] = [
      {
        id: plan.user.user_id,
        latitude: plan.user.latitude,
        longitude: plan.user.longitude,
        title: "Current location",
        subtitle: `${plan.user.zip_code} • ${plan.user.transport_mode.replace("_", " ")}`,
        accentClass: "user",
      },
      {
        id: plan.recommended_clinic.id,
        latitude: plan.recommended_clinic.latitude,
        longitude: plan.recommended_clinic.longitude,
        title: plan.recommended_clinic.name,
        subtitle: `${plan.recommended_clinic.estimated_cost} • ${plan.recommended_clinic.distance}`,
        accentClass: "clinic",
      },
    ];

    if (plan.backup_clinic) {
      nextPoints.push({
        id: plan.backup_clinic.id,
        latitude: plan.backup_clinic.latitude,
        longitude: plan.backup_clinic.longitude,
        title: plan.backup_clinic.name,
        subtitle: `${plan.backup_clinic.estimated_cost} • ${plan.backup_clinic.distance}`,
        accentClass: "backup",
      });
    }

    if (plan.prescription_savings) {
      nextPoints.push({
        id: plan.prescription_savings.id,
        latitude: plan.prescription_savings.latitude,
        longitude: plan.prescription_savings.longitude,
        title: plan.prescription_savings.name,
        subtitle: plan.prescription_savings.distance,
        accentClass: "pharmacy",
      });
    }

    return nextPoints;
  }, [plan]);

  useEffect(() => {
    if (!mapElementRef.current || mapRef.current) {
      return;
    }

    const map = L.map(mapElementRef.current, {
      zoomControl: true,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    markerLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      markerLayerRef.current?.clearLayers();
      markerLayerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const markerLayer = markerLayerRef.current;
    if (!map || !markerLayer) {
      return;
    }

    markerLayer.clearLayers();

    const bounds = L.latLngBounds(points.map((point) => [point.latitude, point.longitude] as [number, number]));

    points.forEach((point) => {
      const marker = L.marker([point.latitude, point.longitude], { icon: iconForPoint(point.accentClass) });
      marker.bindPopup(
        `<div class="careroute-map-popup">
          <div class="careroute-map-popup__title">${escapeHtml(point.title)}</div>
          <div class="careroute-map-popup__subtitle">${escapeHtml(point.subtitle)}</div>
        </div>`,
      );
      markerLayer.addLayer(marker);
    });

    map.fitBounds(bounds, { padding: [42, 42], maxZoom: 13 });
  }, [points]);

  return (
    <section className="rounded-[28px] border border-[#E6DDD1] bg-white p-5 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#ECE4D9] bg-[#FFF7ED] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#9A4E2D]">
            <MapPinned className="h-3.5 w-3.5" />
            Care map
          </div>
          <h3 className="mt-3 text-xl font-semibold text-slate-900">Live route map</h3>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
            Review the route context before you move to the final action plan.
          </p>
        </div>
        {plan.transportation && (
          <div className="rounded-2xl border border-[#E6DDD1] bg-[#FCFAF7] px-4 py-3 text-sm text-slate-600">
            <p className="font-semibold text-slate-900">{plan.transportation.name}</p>
            <p className="mt-1">{plan.transportation.estimated_time}</p>
          </div>
        )}
      </div>

      <div className="mt-5 overflow-hidden rounded-[24px] border border-[#E6DDD1]">
        <div ref={mapElementRef} className="h-[420px] w-full" />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <LegendItem label="You" dotClass="careroute-map-marker__dot--user" />
        <LegendItem label="Recommended clinic" dotClass="careroute-map-marker__dot--clinic" />
        <LegendItem label="Backup clinic" dotClass="careroute-map-marker__dot--backup" />
        <LegendItem label="Prescription support" dotClass="careroute-map-marker__dot--pharmacy" />
      </div>
    </section>
  );
}

function iconForPoint(accentClass: string) {
  if (accentClass === "user") return userIcon;
  if (accentClass === "backup") return backupIcon;
  if (accentClass === "pharmacy") return pharmacyIcon;
  return clinicIcon;
}

function LegendItem({ label, dotClass }: { label: string; dotClass: string }) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-[#ECE4D9] bg-[#FCFAF7] px-3 py-2 text-sm text-slate-700">
      <span className={`careroute-map-marker__dot ${dotClass}`} />
      <span>{label}</span>
    </div>
  );
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
