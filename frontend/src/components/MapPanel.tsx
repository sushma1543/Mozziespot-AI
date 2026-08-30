import L from "leaflet";
import { ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useRef } from "react";
import { Detection } from "../lib/api";

const colors: Record<Detection["risk_level"], string> = {
  Low: "#1f9d65",
  Medium: "#d49b12",
  High: "#ef6c00",
  Critical: "#c62828"
};

type Props = {
  detections: Detection[];
  selected?: Detection;
  userLocation?: { latitude: number; longitude: number };
  onSelect: (detection: Detection) => void;
  onSpotPick: (latitude: number, longitude: number) => void;
};

const emojiIcon = (emoji: string, className = "") => L.divIcon({
  className: "emoji-map-marker " + className,
  html: `<span aria-hidden="true">${emoji}</span>`,
  iconSize: [34, 34],
  iconAnchor: [17, 30]
});

const isSearchPlace = (detection: Detection) => Boolean(
  detection.zoom_to_place || detection.search_match || detection.marker_type === "search" ||
  detection.id.startsWith("PLACE-") || detection.id.startsWith("LIVE-") || detection.id.startsWith("SEARCH-") ||
  detection.id.startsWith("SPOT-")
);

export function MapPanel({ detections, selected, userLocation, onSelect, onSpotPick }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const riskLayerRef = useRef<L.LayerGroup | null>(null);
  const userLayerRef = useRef<L.LayerGroup | null>(null);
  const clickLayerRef = useRef<L.LayerGroup | null>(null);
  const initialFitDoneRef = useRef(false);
  const focusedSearchRef = useRef<string | null>(null);

  const redraw = () => {
    window.setTimeout(() => mapRef.current?.invalidateSize(), 80);
    window.setTimeout(() => mapRef.current?.invalidateSize(), 300);
  };

  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;
    const map = L.map(containerRef.current, { zoomControl: true }).setView([16.8, 80.2], 7);
    const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
    });
    const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, attribution: "Imagery &copy; Esri and providers"
    });
    satellite.addTo(map);
    L.control.layers({ "Satellite imagery": satellite, OpenStreetMap: osm }, {}, { collapsed: false }).addTo(map);
    riskLayerRef.current = L.layerGroup().addTo(map);
    userLayerRef.current = L.layerGroup().addTo(map);
    clickLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    redraw();
  }, []);

  useEffect(() => {
    if (!containerRef.current || !mapRef.current) return;
    const observer = new ResizeObserver(() => mapRef.current?.invalidateSize());
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const click = (event: L.LeafletMouseEvent) => {
      const location = event.latlng;
      clickLayerRef.current?.clearLayers();
      L.circle(location, {
        radius: 120,
        color: "#2563eb",
        weight: 2,
        fillColor: "#2563eb",
        fillOpacity: 0.16
      }).addTo(clickLayerRef.current!).bindTooltip("Clicked area being analysed", { permanent: true, direction: "top" });
      L.marker(location, { icon: emojiIcon("\u{1F3AF}", "clicked-marker") }).addTo(clickLayerRef.current!);
      map.setView(location, Math.max(map.getZoom(), 16), { animate: true });
      onSpotPick(location.lat, location.lng);
    };
    map.on("click", click);
    return () => { map.off("click", click); };
  }, [onSpotPick]);

  useEffect(() => {
    const layer = riskLayerRef.current;
    const map = mapRef.current;
    if (!layer || !map) return;
    layer.clearLayers();
    const visible = detections.filter((item) => isSearchPlace(item) || item.is_waterbody !== false);

    visible.forEach((detection) => {
      const searchPlace = isSearchPlace(detection);
      const color = colors[detection.risk_level] ?? colors.Low;
      if (!searchPlace) {
        if (detection.mosquito_activity_index >= 45 || detection.breeding_likelihood >= 45) {
          L.circle([detection.latitude, detection.longitude], {
            radius: 140 + detection.mosquito_activity_index * 7,
            color, weight: 1, fillColor: color, fillOpacity: 0.13, interactive: false
          }).addTo(layer);
        }
        const marker = L.circleMarker([detection.latitude, detection.longitude], {
          radius: selected?.id === detection.id ? 15 : detection.risk_level === "Low" ? 7 : 10,
          color: "#ffffff", weight: 2, fillColor: color, fillOpacity: 0.9
        });
        marker.bindTooltip(`Waterbody: ${detection.name} - ${detection.risk_level} breeding risk`);
        marker.on("click", (event) => { L.DomEvent.stopPropagation(event); onSelect(detection); });
        marker.addTo(layer);
      }
      if (searchPlace) {
        const pin = L.marker([detection.latitude, detection.longitude], {
          icon: emojiIcon("\u{1F4CD}", selected?.id === detection.id ? "emoji-selected" : "")
        });
        pin.bindTooltip(`${detection.name} - searched location`);
        pin.on("click", (event) => { L.DomEvent.stopPropagation(event); onSelect(detection); });
        pin.addTo(layer);
      }
    });

    const searched = visible.find((item) => isSearchPlace(item));
    if (searched && focusedSearchRef.current !== searched.id) {
      focusedSearchRef.current = searched.id;
      map.setView([searched.latitude, searched.longitude], 15);
    } else if (!initialFitDoneRef.current && visible.length > 1) {
      initialFitDoneRef.current = true;
      map.fitBounds(
      L.latLngBounds(visible.map((item) => [item.latitude, item.longitude] as [number, number])).pad(0.12),
      { maxZoom: 10 }
      );
    }
    redraw();
  }, [detections, selected, onSelect]);

  useEffect(() => {
    const layer = userLayerRef.current;
    if (!layer) return;
    layer.clearLayers();
    if (!userLocation) return;
    L.circle([userLocation.latitude, userLocation.longitude], {
      radius: 250, color: "#2563eb", weight: 2, fillColor: "#2563eb", fillOpacity: 0.18
    }).addTo(layer).bindTooltip("Your live tracking radius");
    L.marker([userLocation.latitude, userLocation.longitude], { icon: emojiIcon("\u{1F6B6}", "walking-marker") })
      .addTo(layer).bindTooltip("Your live walking location");
    mapRef.current?.setView([userLocation.latitude, userLocation.longitude], 15);
    redraw();
  }, [userLocation]);

  useEffect(() => {
    if (!selected || !mapRef.current) return;
    mapRef.current.setView([selected.latitude, selected.longitude], isSearchPlace(selected) ? 15 : 16);
    if (selected.id.startsWith("SPOT-")) {
      clickLayerRef.current?.clearLayers();
      const color = selected.is_waterbody === false ? "#2563eb" : colors[selected.risk_level];
      L.circle([selected.latitude, selected.longitude], {
        radius: selected.is_waterbody === false ? 120 : 220,
        color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.18
      }).addTo(clickLayerRef.current!).bindTooltip(
        selected.is_waterbody === false ? "Analysed point: no mapped waterbody evidence" : `Analysed waterbody: ${selected.risk_level} risk`,
        { permanent: true, direction: "top" }
      );
    }
    redraw();
  }, [selected]);

  return (
    <div className="map-panel-shell">
      <div ref={containerRef} className="map-panel" />
      <div className="map-zoom-tools" aria-label="Map zoom controls">
        <button type="button" title="Zoom in" aria-label="Zoom in" onClick={() => mapRef.current?.zoomIn()}>
          <ZoomIn size={20} />
        </button>
        <button type="button" title="Zoom out" aria-label="Zoom out" onClick={() => mapRef.current?.zoomOut()}>
          <ZoomOut size={20} />
        </button>
      </div>
    </div>
  );
}
