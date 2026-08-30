import {
  AlertTriangle,
  Bell,
  Bug,
  Crosshair,
  Droplets,
  ExternalLink,
  FileDown,
  LocateFixed,
  MapPin,
  MessageCircle,
  RefreshCw,
  Search,
  Satellite,
  Send,
  ShieldCheck,
  Thermometer,
  Layers,
  FlaskConical,
  X
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DiseaseChart } from "../components/DiseaseChart";
import { MapPanel } from "../components/MapPanel";
import { MetricCard } from "../components/MetricCard";
import { RiskBadge } from "../components/RiskBadge";
import {
  api,
  AdminRolesResponse,
  AnalyticsResponse,
  Detection,
  LocationCatalog,
  ModuleStatus,
  StateRiskResponse,
  Summary,
  SatelliteDownloadResponse,
  SatelliteProcessResponse,
  SatelliteSearchResponse
  ,ValidationStatus
} from "../lib/api";

const emptySummary: Summary = {
  water_bodies: 0,
  high_risk_zones: 0,
  alerts_sent: 0,
  ai_confidence: 0,
  disease_index: 0
};

const diseaseLabels: Record<string, string> = {
  malaria: "Malaria",
  dengue: "Dengue",
  chikungunya: "Chikungunya",
  japanese_encephalitis: "Japanese Encephalitis",
  diarrhea: "Diarrhea",
  cholera: "Cholera",
  typhoid: "Typhoid"
};

export function App() {
  const [summary, setSummary] = useState<Summary>(emptySummary);
  const [catalog, setCatalog] = useState<LocationCatalog>({ states: [] });
  const [detections, setDetections] = useState<Detection[]>([]);
  const [selected, setSelected] = useState<Detection | undefined>();
  const [stateName, setStateName] = useState("All");
  const [district, setDistrict] = useState("All");
  const [village, setVillage] = useState("All");
  const [minimumRisk, setMinimumRisk] = useState("Low");
  const [placeQuery, setPlaceQuery] = useState("");
  const [spotName, setSpotName] = useState("Selected spot");
  const [latitude, setLatitude] = useState("17.3850");
  const [longitude, setLongitude] = useState("78.4867");
  const [whatsappNumber, setWhatsappNumber] = useState("");
  const [note, setNote] = useState("Loading AP and Telangana risk map...");
  const [status, setStatus] = useState("Starting surveillance dashboard...");
  const [stateStats, setStateStats] = useState<StateRiskResponse["summary"]>({ total_points: 0, red_zones: 0, yellow_zones: 0, green_zones: 0, updated_at: "" });
  const [clock, setClock] = useState(new Date());
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | undefined>();
  const [nearby, setNearby] = useState<Detection[]>([]);
  const [satelliteDownload, setSatelliteDownload] =
  useState<SatelliteDownloadResponse | null>(null);

const [satelliteLoading,setSatelliteLoading] =
useState(false);


const [satelliteProcessing,setSatelliteProcessing] =
useState(false);


  const [satelliteOutput,setSatelliteOutput] =
useState<SatelliteProcessResponse | null>(null);
  const [satelliteSearch, setSatelliteSearch] = useState<SatelliteSearchResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [modules, setModules] = useState<ModuleStatus[]>([]);
  const [adminRoles, setAdminRoles] = useState<AdminRolesResponse | null>(null);
  const [validation, setValidation] = useState<ValidationStatus | null>(null);
  const [showSatellitePopup, setShowSatellitePopup] = useState(false);
  const [activeNav, setActiveNav] = useState("state-risk");
  const watchId = useRef<number | null>(null);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const districtOptions = useMemo(() => {
    if (stateName === "All") return catalog.states.flatMap((state) => state.districts.map((item) => item.name));
    return catalog.states.find((state) => state.name === stateName)?.districts.map((item) => item.name) ?? [];
  }, [catalog, stateName]);

  const villageOptions = useMemo(() => {
    const districts = catalog.states.flatMap((state) => state.districts);
    if (district === "All") return districts.flatMap((item) => item.villages);
    return districts.find((item) => item.name === district)?.villages ?? [];
  }, [catalog, district]);

  const loadStateRisk = useCallback(async (override?: Partial<{ state: string; district: string; village: string; q: string; minimum: string }>) => {
    const activeState = override?.state ?? stateName;
    const activeDistrict = override?.district ?? district;
    const activeVillage = override?.village ?? village;
    const activeQuery = override?.q ?? placeQuery;
    const activeMinimum = override?.minimum ?? minimumRisk;
    setStatus("Updating statewide risk dots...");
    try {
      const riskQuery = activeQuery.trim();
      const result = await api.stateRisk({
        state: activeState,
        district: activeDistrict,
        village: activeVillage,
        q: riskQuery,
        minimum: activeMinimum
      });
      let nextResults = result.results;
      let selectedResult: Detection | undefined = result.results.find((item) => item.zoom_to_place) ?? result.results[0];
      if (activeQuery.trim()) {
        setStatus("Finding exact place coordinates...");
        const geocode = await api.geocodePlace(activeQuery.trim(), activeState, activeDistrict);
        if (geocode.found) {
          nextResults = [geocode.detection, ...result.results.filter((item) => item.id !== geocode.detection.id && !item.zoom_to_place)];
          selectedResult = geocode.detection;
          setLatitude(String(geocode.detection.latitude));
          setLongitude(String(geocode.detection.longitude));
          setSpotName(geocode.detection.name);
          setStatus((geocode.detection.approximate_place ? "Approximate search marker shown for: " : "Zoomed to exact place: ") + geocode.detection.name + ".");
        } else {
          nextResults = [];
          selectedResult = undefined;
          setStatus("Exact place not found. Add district/state or enter latitude and longitude. No random location was shown.");
        }
      } else {
        setStatus("Map updated with " + result.results.length + " risk points.");
      }
      setDetections(nextResults);
      setStateStats({
        ...result.summary,
        total_points: nextResults.length,
        red_zones: nextResults.filter((item) => item.risk_level === "High" || item.risk_level === "Critical").length,
        yellow_zones: nextResults.filter((item) => item.risk_level === "Medium").length,
        green_zones: nextResults.filter((item) => item.risk_level === "Low").length
      });
      setNote(result.note);
      setSelected(selectedResult);
    } catch {
      setStatus("Backend unavailable or online place lookup failed. Try latitude and longitude.");
    }
  }, [district, minimumRisk, placeQuery, stateName, village]);

  useEffect(() => {
    Promise.all([api.summary(), api.locations(), api.stateRisk({ state: "All", district: "All", village: "All", q: "", minimum: "Low" })])
      .then(([summaryData, locationData, riskData]) => {
        setSummary(summaryData);
        setCatalog(locationData);
        setDetections(riskData.results);
        setStateStats(riskData.summary);
        setNote(riskData.note);
        setSelected(riskData.results[0]);
        setStatus("Map updated with " + riskData.results.length + " risk points.");
      })
      .catch(() => setStatus("Backend unavailable. Start the Flask service or Docker stack."));
  }, []);

  useEffect(() => {
    api.advancedModules()
      .then((data) => setModules(data.modules))
      .catch(() => setModules([]));
    api.analytics()
      .then(setAnalytics)
      .catch(() => setAnalytics(null));
    api.adminRoles()
      .then(setAdminRoles)
      .catch(() => setAdminRoles(null));
    api.validationStatus()
      .then(setValidation)
      .catch(() => setValidation(null));
  }, []);

  const ranked = useMemo(
    () => [...detections].sort((a, b) => (b.mosquito_risk_score ?? b.risk_score) - (a.mosquito_risk_score ?? a.risk_score)),
    [detections]
  );

  const runSpotAnalysis = useCallback(async (latValue?: number, lonValue?: number, nameValue?: string) => {
    const lat = latValue ?? Number(latitude);
    const lon = lonValue ?? Number(longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      setStatus("Enter valid latitude and longitude values.");
      return;
    }
    setStatus("Predicting risk for selected spot...");
    try {
      const result = await api.analyzeSpot(lat, lon, nameValue ?? spotName);
      setDetections((current) => [result.detection, ...current.filter((item) => item.id !== result.detection.id && !item.id.startsWith("SPOT-"))]);
      setSelected(result.detection);
      setStatus(result.detection.name + " predicted as " + result.detection.risk_level + " risk.");
    } catch {
      setStatus("Spot analysis failed. Check that the backend is running.");
    }
  }, [latitude, longitude, spotName]);

  const handleSpotPick = useCallback((lat: number, lon: number) => {
    const fixedLat = Number(lat.toFixed(5));
    const fixedLon = Number(lon.toFixed(5));
    setLatitude(String(fixedLat));
    setLongitude(String(fixedLon));
    runSpotAnalysis(fixedLat, fixedLon, "Clicked map spot");
  }, [runSpotAnalysis]);

  const startTracking = () => {
    if (!navigator.geolocation) {
      setStatus("Location tracking is not supported in this browser.");
      return;
    }
    if (!window.isSecureContext && window.location.hostname !== "localhost") {
      setStatus("Live tracking requires HTTPS or localhost.");
      return;
    }
    if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current);
    setStatus("Requesting live location permission. Choose Allow in the browser prompt...");
    const locationError = (error: GeolocationPositionError) => {
      const messages: Record<number, string> = {
        1: "Location permission was denied. Allow location for localhost in browser Site permissions, then click Track Me again.",
        2: "Your device could not determine its location. Turn on Windows Location Services and Wi-Fi/GPS.",
        3: "Location request timed out. Move near a window or retry with device location enabled."
      };
      setStatus(messages[error.code] || "Location tracking is unavailable.");
    };
    navigator.geolocation.getCurrentPosition(
      (position) => setUserLocation({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
      locationError,
      { enableHighAccuracy: true, maximumAge: 0, timeout: 20000 }
    );
    watchId.current = navigator.geolocation.watchPosition(
      async (position) => {
        const lat = Number(position.coords.latitude.toFixed(5));
        const lon = Number(position.coords.longitude.toFixed(5));
        setUserLocation({ latitude: lat, longitude: lon });
        setLatitude(String(lat));
        setLongitude(String(lon));
        try {
          const result = await api.nearbyRisk(lat, lon, 3000);
          setNearby(result.nearby);
          setSelected(result.current_spot);
          setDetections((current) => [result.current_spot, ...result.nearby, ...current.filter((item) => !item.id.startsWith("SPOT-") && !result.nearby.some((near) => near.id === item.id)).slice(0, 80)]);
          setStatus("Tracking nearby risk zones. Updated " + result.updated_at + ".");
        } catch {
          setStatus("Could not update nearby risk from backend.");
        }
      },
      locationError,
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 15000 }
    );
  };

  const stopTracking = () => {
    if (watchId.current !== null) {
      navigator.geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
    setStatus("Walking tracking stopped.");
  };

  const navigateToModule = (module: string, targetId: string) => {
    setActiveNav(module);
    document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const focusWaterBodies = () => {
    setActiveNav("water-bodies");
    const waterbodies = detections
      .filter((item) => item.is_waterbody !== false)
      .sort((a, b) => (b.mosquito_risk_score ?? b.risk_score) - (a.mosquito_risk_score ?? a.risk_score));
    if (waterbodies[0]) {
      setSelected(waterbodies[0]);
      setLatitude(String(waterbodies[0].latitude));
      setLongitude(String(waterbodies[0].longitude));
      setSpotName(waterbodies[0].name);
      setStatus(`Focused waterbody: ${waterbodies[0].name}. Select any dot or click another map area.`);
    }
    document.getElementById("mosquito-risk")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const sendAlert = async (channel: "whatsapp" | "telegram") => {
    if (!selected) return;
    if (selected.is_waterbody === false) {
      setStatus("Alert blocked: this searched location has no probable waterbody evidence.");
      return;
    }
    setStatus("Preparing authority alert...");
    try {
      const result = await api.sendAlert(selected, whatsappNumber.replace(/[^0-9]/g, ""));
      if (channel === "telegram") {
        if (result.telegram_url) window.open(result.telegram_url, "_blank");
        setStatus(result.telegram?.sent ? "Telegram alert sent to configured authority chat." : "Telegram message opened. Choose the panchayat chat and send it.");
        return;
      }
      if (result.whatsapp_url) window.open(result.whatsapp_url, "_blank");
      setStatus("WhatsApp alert message prepared for " + selected.authority_name + ".");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Alert could not be sent.");
    }
  };
 const downloadSentinel = async () => {

    setSatelliteLoading(true);

    setStatus(
      "Downloading latest Sentinel-2 satellite image..."
    );

    try{

      const result =
      await api.downloadSatellite(selected?.latitude ?? Number(latitude), selected?.longitude ?? Number(longitude));


      setSatelliteDownload(result);


      setStatus(
        "Sentinel-2 image downloaded successfully."
      );


    }
    catch(error){

      setStatus(
        "Sentinel download failed."
      );

    }

    finally{

      setSatelliteLoading(false);

    }

};
const searchSentinel = async () => {
  setSatelliteLoading(true);
  setStatus("Searching Copernicus and AWS Sentinel-2 STAC catalogs...");
  try {
    const result = await api.searchSatellite(selected?.latitude ?? Number(latitude), selected?.longitude ?? Number(longitude));
    setSatelliteSearch(result);
    setStatus(
      result.online
        ? "Latest Sentinel-2 scene found from " + result.source + "."
        : "Online satellite search unavailable; demo Sentinel scene loaded."
    );
  } catch {
    setStatus("Satellite scene search failed.");
  } finally {
    setSatelliteLoading(false);
  }
};
const processSentinel = async()=>{


 setSatelliteProcessing(true);


 setStatus(
   "Running cloud masking, band extraction and NDWI pipeline..."
 );


 try{


 const result =await api.processSatellite(selected?.latitude ?? Number(latitude), selected?.longitude ?? Number(longitude));


 setSatelliteOutput(result);
 setStatus(
  "Satellite processing completed. RGB, NDWI and water mask generated."
 );


 }

 catch(error){


 setStatus(
 "Satellite processing failed."
 );


 }

 finally{

 setSatelliteProcessing(false);

 }


};

  const satellitePreviewUrl = useMemo(() => {
    const processedPreview = satelliteOutput?.download_urls?.preview;
    if (processedPreview) return processedPreview;
    if (!selected) return "";
    const pad = 0.025;
    const bbox = [selected.longitude - pad, selected.latitude - pad, selected.longitude + pad, selected.latitude + pad].join(",");
    return "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export" +
      "?bbox=" + encodeURIComponent(bbox) +
      "&bboxSR=4326&imageSR=4326&size=900,560&format=jpg&f=image";
  }, [satelliteOutput, selected]);

  const copernicusUrl = useMemo(() => {
    if (!selected) return "https://browser.dataspace.copernicus.eu/";
    const params = new URLSearchParams({
      zoom: "13",
      lat: String(selected.latitude),
      lng: String(selected.longitude),
      cloudCoverage: "30"
    });
    return "https://browser.dataspace.copernicus.eu/?" + params.toString();
  }, [selected]);

  const selectMapRisk = useCallback(async (detection: Detection) => {
    setSelected(detection);
    setLatitude(String(detection.latitude));
    setLongitude(String(detection.longitude));
    setSpotName(detection.name);
    if (detection.is_waterbody === false) return;
    setShowSatellitePopup(true);
    setSatelliteLoading(true);
    try {
      const scene = await api.searchSatellite(detection.latitude, detection.longitude);
      setSatelliteSearch(scene);
    } catch {
      setStatus("Satellite preview opened, but Sentinel-2 scene metadata could not be loaded.");
    } finally {
      setSatelliteLoading(false);
    }
  }, []);

  const chooseState = (value: string) => {
    setStateName(value);
    setDistrict("All");
    setVillage("All");
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Satellite size={30} />
          <div>
            <h1>MozzieSpot AI</h1>
            <p>AP + Telangana risk map</p>
          </div>
        </div>
        <nav aria-label="Dashboard modules">
          <button className={activeNav === "state-risk" ? "active" : ""} onClick={() => navigateToModule("state-risk", "state-risk")}><MapPin size={18} /> State Risk</button>
          <button className={activeNav === "water-bodies" ? "active" : ""} onClick={focusWaterBodies}><Droplets size={18} /> Water Bodies</button>
          <button className={activeNav === "mosquito-risk" ? "active" : ""} onClick={() => navigateToModule("mosquito-risk", "mosquito-risk")}><Bug size={18} /> Mosquito Risk</button>
          <button className={activeNav === "alerts" ? "active" : ""} onClick={() => navigateToModule("alerts", "alerts")}><Bell size={18} /> Alerts</button>
          <button className={activeNav === "tracking" ? "active" : ""} onClick={() => navigateToModule("tracking", "tracking")}><LocateFixed size={18} /> Tracking</button>
          <button className={activeNav === "validation" ? "active" : ""} onClick={() => navigateToModule("validation", "validation")}><FlaskConical size={18} /> Research Lab</button>
        </nav>
        <div className="system-status">
          <ShieldCheck size={18} />
          <span>{status}</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar" id="state-risk">
          <div>
            <p className="eyebrow">Public Health Command Center</p>
            <h2>Probable mosquito breeding waterbody risk map</h2>
            <p className="subtle">Live clock: {clock.toLocaleString()} | Last map update: {stateStats.updated_at || "waiting"}</p>
          </div>
          <a className="download" href="/api/reports/weekly">
            <FileDown size={18} /> PDF Report
          </a>
        </header>

        <section className="metrics-grid">
          <MetricCard label="Map points" value={stateStats.total_points || summary.water_bodies} icon={Droplets} />
          <MetricCard label="Red risk" value={stateStats.red_zones} icon={AlertTriangle} tone="danger" />
          <MetricCard label="Yellow risk" value={stateStats.yellow_zones} icon={Thermometer} tone="warning" />
          <MetricCard label="Green risk" value={stateStats.green_zones} icon={ShieldCheck} />
          <MetricCard label="Nearby zones" value={nearby.length} icon={LocateFixed} tone="warning" />
        </section>

        <section className="state-controls">
          <div>
            <p className="eyebrow">Search Whole Map</p>
            <h3>State, District, Village, Place Name</h3>
          </div>
          <label>State<select value={stateName} onChange={(event) => chooseState(event.target.value)}><option>All</option>{catalog.states.map((item) => <option key={item.name}>{item.name}</option>)}</select></label>
          <label>District<select value={district} onChange={(event) => { setDistrict(event.target.value); setVillage("All"); }}><option>All</option>{districtOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>Village/Ward<select value={village} onChange={(event) => setVillage(event.target.value)}><option>All</option>{villageOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>Minimum<select value={minimumRisk} onChange={(event) => setMinimumRisk(event.target.value)}><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></label>
          <label>Place name<input value={placeQuery} onChange={(event) => setPlaceQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") loadStateRisk(); }} placeholder="Any village/town: Mandadam, VIT-AP, Tullur..." /></label>
          <button className="primary-action" onClick={() => loadStateRisk()}><Search size={18} /> Search</button>
          <button className="secondary-action" onClick={() => loadStateRisk()}><RefreshCw size={18} /> Refresh Map</button>
          <button className="secondary-action" onClick={() => { setStateName("All"); setDistrict("All"); setVillage("All"); setPlaceQuery(""); setMinimumRisk("Low"); loadStateRisk({ state: "All", district: "All", village: "All", q: "", minimum: "Low" }); }}><RefreshCw size={18} /> Show All</button>
          <p className="science-note">{note}</p>
        </section>

        <section className="spot-tool advanced-spot" id="tracking">
          <div>
            <p className="eyebrow">Latitude / Longitude Prediction</p>
            <h3>Click Map or Enter Coordinates</h3>
          </div>
          <label>Name<input value={spotName} onChange={(event) => setSpotName(event.target.value)} /></label>
          <label>Latitude<input value={latitude} onChange={(event) => setLatitude(event.target.value)} inputMode="decimal" /></label>
          <label>Longitude<input value={longitude} onChange={(event) => setLongitude(event.target.value)} inputMode="decimal" /></label>
          <button className="primary-action" onClick={() => runSpotAnalysis()}><span aria-hidden="true">{"\u{1F3AF}"}</span> Predict Spot</button>
          <button className="secondary-action" onClick={startTracking}><span aria-hidden="true">{"\u{1F6B6}"}</span> Track Me</button>
          <button className="secondary-action" onClick={stopTracking}><RefreshCw size={18} /> Stop</button>
        </section>
        <section className="satellite-panel" id="water-bodies">


<div>

<p className="eyebrow">
Sentinel-2 AI Processing
</p>

<h3>
Real Satellite Image Pipeline
</h3>


<p>
Automatic download → Cloud masking → Band extraction →
NDWI → Water detection
</p>

</div>



<div className="satellite-actions">


<button
className="secondary-action"
onClick={searchSentinel}
disabled={satelliteLoading}
>

<Search size={18}/>

Search Latest Scene

</button>


<button
className="primary-action"
onClick={downloadSentinel}
disabled={satelliteLoading}
>

<Satellite size={18}/>

{
satelliteLoading
?
"Downloading..."
:
"Download Sentinel-2"
}

</button>



<button
className="secondary-action"
onClick={processSentinel}
disabled={satelliteProcessing}
>

<Layers size={18}/>


{
satelliteProcessing
?
"Processing..."
:
"Run AI Processing"
}


</button>


</div>



{
satelliteDownload &&

<div className="satellite-result">

<h4>
Download Complete
</h4>


<p>
Folder:
{satelliteDownload.folder}
</p>

{satelliteDownload.selected_scene && <p>Scene: {satelliteDownload.selected_scene.id}</p>}
{satelliteDownload.message && <p>{satelliteDownload.message}</p>}


</div>

}


{
satelliteSearch &&

<div className="satellite-result satellite-scenes">

<h4>Latest Sentinel-2 Scene</h4>

<p>Source: {satelliteSearch.source} | Date window: {satelliteSearch.date_window.start_date} to {satelliteSearch.date_window.end_date}</p>

<div className="scene-list">
{satelliteSearch.scenes.slice(0, 4).map((scene) => (
  <div key={scene.id}>
    <strong>{scene.id}</strong>
    <span>{scene.datetime || "Date unavailable"}</span>
    <span>{scene.cloud_cover ?? 0}% cloud</span>
  </div>
))}
</div>

</div>

}



{
satelliteOutput &&

<div className="satellite-result">


<h4>
Generated Outputs
</h4>


<p>
🛰 RGB:
{satelliteOutput.outputs.rgb}
</p>


<p>
🌊 NDWI:
{satelliteOutput.outputs.ndwi}
</p>

{satelliteOutput.outputs.mndwi && <p>MNDWI: {satelliteOutput.outputs.mndwi}</p>}
{satelliteOutput.outputs.ndvi && <p>NDVI: {satelliteOutput.outputs.ndvi}</p>}

<p>
💧 Water Mask:
{satelliteOutput.outputs.water}
</p>

{satelliteOutput.indices && (
  <div className="formula-list">
    {Object.entries(satelliteOutput.indices).map(([name, formula]) => (
      <span key={name}>{name}: {formula}</span>
    ))}
  </div>
)}

{satelliteOutput.mode === "raster" && satelliteOutput.download_urls && (
  <>
    <div className="output-downloads">
      {Object.entries(satelliteOutput.download_urls).map(([name, url]) => (
        <a key={name} className="secondary-action" href={url}><FileDown size={16} /> {name.toUpperCase()}</a>
      ))}
      {satelliteOutput.waterbody_download_url && (
        <a className="primary-action" href={satelliteOutput.waterbody_download_url}><FileDown size={16} /> Waterbodies GeoJSON</a>
      )}
    </div>
    {satelliteOutput.statistics && (
      <p className="pipeline-statistics">
        Clear pixels: {satelliteOutput.statistics.clear_pixels.toLocaleString()} | Water: {satelliteOutput.statistics.probable_water_percent}% | Waterbodies: {satelliteOutput.statistics.probable_waterbodies}
      </p>
    )}
  </>
)}

</div>

}


</section>

        <section className="advanced-dashboard">
          <div className="section-title">
            <div>
              <p className="eyebrow">Analytics Dashboard</p>
              <h3>Waterbody, disease and monthly trends</h3>
            </div>
            <div className="export-actions">
              <a className="secondary-action" href="/api/export/csv"><FileDown size={18} /> CSV</a>
              <a className="secondary-action" href="/api/export/excel"><FileDown size={18} /> Excel</a>
              <a className="secondary-action" href="/api/export/geojson"><FileDown size={18} /> GeoJSON</a>
              <a className="secondary-action" href="/api/export/shapefile"><FileDown size={18} /> Shapefile</a>
              <a className="primary-action" href="/api/reports/daily"><FileDown size={18} /> Daily PDF</a>
            </div>
          </div>
          <div className="analytics-grid">
            <div><span>Total water bodies</span><strong>{analytics?.total_water_bodies ?? stateStats.total_points}</strong></div>
            <div><span>Stagnant water</span><strong>{analytics?.total_stagnant_water ?? 0}</strong></div>
            <div><span>High-risk villages</span><strong>{analytics?.high_risk_villages ?? 0}</strong></div>
            <div><span>Severe zones</span><strong>{analytics?.severe_zones ?? 0}</strong></div>
          </div>
          <div className="trend-layout">
            <div>
              <h4>Disease trend</h4>
              <div className="mini-bars">
                {(analytics?.disease_trend ?? []).map((item) => (
                  <div key={item.disease}>
                    <span>{diseaseLabels[item.disease] ?? item.disease}</span>
                    <meter min={0} max={100} value={item.average} />
                    <strong>{item.average}%</strong>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4>Monthly water trend</h4>
              <div className="month-bars">
                {(analytics?.monthly_trend ?? []).map((item) => (
                  <div key={item.month}>
                    <span style={{ height: Math.max(8, item.water_bodies / 2) }} />
                    <small>{item.month}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="module-dashboard">
          <div>
            <p className="eyebrow">Advanced Modules</p>
            <h3>Implemented project coverage</h3>
          </div>
          <div className="module-grid">
            {modules.map((module) => (
              <article key={module.name}>
                <strong>{module.name}</strong>
                <span>{module.status}</span>
                <p>{module.items.slice(0, 4).join(", ")}</p>
              </article>
            ))}
          </div>
          {adminRoles && (
            <div className="role-strip">
              {adminRoles.roles.map((role) => (
                <span key={role.role}>{role.role}: {role.dashboard}</span>
              ))}
            </div>
          )}
        </section>

        <section className="validation-dashboard" id="validation">
          <div className="section-title">
            <div>
              <p className="eyebrow">Experimental Validation Plan</p>
              <h3>Deep-learning readiness and scientific evidence</h3>
            </div>
            <span className={validation?.validated_model_inference ? "readiness ready" : "readiness pending"}>
              {validation?.validated_model_inference ? "Weights detected" : "Awaiting trained weights"}
            </span>
          </div>
          <p className="science-note">
            Operational map: {validation?.operational_map_source ?? "loading"}. Neural-network metrics are displayed only after labelled masks and predictions are supplied.
          </p>
          <div className="model-readiness-grid">
            {(validation?.models ?? []).map((model) => (
              <article key={model.name}>
                <strong>{model.name}</strong>
                <span className={model.trained_weights ? "status-ok" : "status-missing"}>
                  {model.trained_weights ? "Trained weights found" : "Architecture scaffold only"}
                </span>
                <small>{model.required_files.length ? model.required_files.join(", ") : "Requires all three trained models"}</small>
              </article>
            ))}
          </div>
          <div className="validation-columns">
            <div>
              <h4>Evaluation engine available</h4>
              <ul>{(validation?.available_when_data_supplied ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
            <div>
              <h4>Not claimed by this prototype</h4>
              <ul>{(validation?.not_claimed ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          </div>
          {validation?.experiment && (
            <div className="experiment-results">
              <div>
                <h4>Measured test results</h4>
                <p>{validation.experiment.dataset} | {validation.experiment.split_strategy} | {validation.experiment.device}</p>
              </div>
              <div className="metrics-table">
                <strong>Model</strong><strong>Precision</strong><strong>Recall</strong><strong>F1</strong><strong>IoU</strong><strong>Dice</strong>
                {Object.entries(validation.experiment.models).map(([name, result]) => (
                  <div className="metrics-row" key={name}>
                    <span>{name}</span>
                    <span>{result.test.metrics.precision == null ? "NA" : (result.test.metrics.precision * 100).toFixed(2) + "%"}</span>
                    <span>{result.test.metrics.recall == null ? "NA" : (result.test.metrics.recall * 100).toFixed(2) + "%"}</span>
                    <span>{result.test.metrics.f1 == null ? "NA" : (result.test.metrics.f1 * 100).toFixed(2) + "%"}</span>
                    <span>{result.test.metrics.iou == null ? "NA" : (result.test.metrics.iou * 100).toFixed(2) + "%"}</span>
                    <span>{result.test.metrics.dice == null ? "NA" : (result.test.metrics.dice * 100).toFixed(2) + "%"}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <p className="dataset-path">Ground-truth status: <strong>{validation?.ground_truth_ready ? "ready" : "not supplied"}</strong> | Expected dataset: {validation?.dataset_path ?? "loading"}</p>
        </section>

        <section className="analysis-layout" id="mosquito-risk">
          <MapPanel detections={detections} selected={selected} userLocation={userLocation} onSelect={selectMapRisk} onSpotPick={handleSpotPick} />

          <aside className="inspector" id="alerts">
            {selected ? (
              <>
                <div className="inspector-head">
                  <div>
                    <p className="eyebrow">Selected Risk Zone</p>
                    <h3>{selected.name}</h3>
                  </div>
                  <RiskBadge level={selected.risk_level} />
                  {selected.mosquito_risk_level && <span className={"mosquito-risk-pill mosquito-risk-" + selected.mosquito_risk_level.toLowerCase().replace(" ", "-")}>{selected.mosquito_risk_level}</span>}
                </div>
                <p className="habitat-type">{selected.water_type ? selected.water_type + " | " : ""}{selected.habitat_type}</p>
                {selected.is_waterbody === false && <p className="approx-note">No probable waterbody evidence is available at this point. It is shown only as a searched/tracked location and is not a mosquito-risk dot.</p>}
                {satelliteSearch && selected.is_waterbody !== false && (
                  <section className="satellite-evidence">
                    <strong>Sentinel-2 scene for selected waterbody</strong>
                    <span>{satelliteSearch.selected_scene.id}</span>
                    <span>{satelliteSearch.source} | {satelliteSearch.selected_scene.datetime || "date unavailable"} | {satelliteSearch.selected_scene.cloud_cover ?? 0}% cloud</span>
                    <a href={copernicusUrl} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Copernicus source</a>
                  </section>
                )}
                {selected.approximate_place && <p className="approx-note">Approximate search location: exact village coordinates were not in the offline gazetteer. Use latitude and longitude for exact spot prediction.</p>}
                <dl className="details">
                  <div><dt>State</dt><dd>{selected.state}</dd></div>
                  <div><dt>District</dt><dd>{selected.district}</dd></div>
                  <div><dt>Village/Ward</dt><dd>{selected.village}</dd></div>
                  <div><dt>Authority</dt><dd>{selected.authority_name}</dd></div>
                  <div><dt>Risk score</dt><dd>{selected.risk_score}</dd></div>
                  <div><dt>Mosquito risk</dt><dd>{selected.mosquito_risk_score ?? selected.risk_score}</dd></div>
                  <div><dt>Confidence</dt><dd>{Math.round(selected.confidence * 100)}%</dd></div>
                  <div><dt>NDWI</dt><dd>{selected.ndwi}</dd></div>
                  <div><dt>Rainfall</dt><dd>{selected.advanced_factors?.rainfall ?? "NA"} mm</dd></div>
                  <div><dt>Humidity</dt><dd>{selected.advanced_factors?.humidity ?? "NA"}%</dd></div>
                  <div><dt>Water persistence</dt><dd>{selected.days_persistent} days</dd></div>
                  <div><dt>Breeding likelihood</dt><dd>{selected.breeding_likelihood}%</dd></div>
                  <div><dt>Mosquito activity</dt><dd>{selected.mosquito_activity_index}%</dd></div>
                </dl>
                <section className="disease-grid">
                  {Object.entries(selected.advanced_disease_index ?? selected.disease_index).map(([key, value]) => (
                    <div key={key}><span>{diseaseLabels[key] ?? key}</span><strong>{value}%</strong></div>
                  ))}
                </section>
                <section className="explain">
                  <h4>Explainable AI</h4>
                  <ul>{selected.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
                  {selected.explainability && (
                    <div className="factor-bars">
                      {selected.explainability.top_factors.map(([factor, value]) => (
                        <div key={factor}>
                          <span>{factor.replace(/_/g, " ")}</span>
                          <meter min={0} max={24} value={value} />
                          <strong>{value}</strong>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
                <section className="chart-box">
                  <h4>Disease Suitability</h4>
                  <DiseaseChart detection={selected} />
                </section>
                <p className="recommendation">{selected.recommendation}</p>
                <label className="whatsapp-label">WhatsApp number with country code<input value={whatsappNumber} onChange={(event) => setWhatsappNumber(event.target.value)} placeholder="919999999999" /></label>
                <div className="alert-actions">
                  <button className="secondary-action" disabled={selected.is_waterbody === false || satelliteLoading} onClick={() => selectMapRisk(selected)}><Satellite size={18} /> Waterbody Scene</button>
                  <a className="secondary-action" href={"https://www.google.com/maps?q=" + selected.latitude + "," + selected.longitude} target="_blank" rel="noreferrer"><ExternalLink size={18} /> Google Maps</a>
                  <button className="primary-action" disabled={selected.is_waterbody === false} onClick={() => sendAlert("whatsapp")}><MessageCircle size={18} /> WhatsApp Alert</button>
                  <button className="secondary-action" disabled={selected.is_waterbody === false} onClick={() => sendAlert("telegram")}><Send size={18} /> Telegram Alert</button>
                </div>
              </>
            ) : <p>Select a dot or click on the map to predict risk.</p>}
          </aside>
        </section>

        <section className="table-section">
          <h3>Risk Priority List</h3>
          <div className="legend"><span className="dot red" /> Severe/High <span className="dot yellow" /> Moderate <span className="dot green" /> Low/Very Low</div>
          <div className="table">
            {ranked.length === 0 ? (
              <div className="empty-state">
                No exact place match found. Try village + district, for example “Velagapudi Guntur”, “Mandadam”, “VIT-AP”, “Tullur”, “Vijayawada”, or enter latitude and longitude for exact spot prediction.
              </div>
            ) : ranked.slice(0, 80).map((detection) => (
              <button key={detection.id} onClick={() => { setSelected(detection); setLatitude(String(detection.latitude)); setLongitude(String(detection.longitude)); setSpotName(detection.name); }} className="row advanced-row">
                <span>{detection.name}</span>
                <span>{detection.state}</span>
                <span>{detection.district}</span>
                <span>{detection.water_type ?? detection.habitat_type}</span>
                <span>{detection.mosquito_risk_score ?? detection.risk_score} score</span>
                <span>{detection.breeding_likelihood}% breeding</span>
                <span>{detection.mosquito_activity_index}% activity</span>
                <RiskBadge level={detection.risk_level} />
              </button>
            ))}
          </div>
        </section>
        {showSatellitePopup && selected && (
          <div className="satellite-modal-backdrop" role="presentation" onMouseDown={() => setShowSatellitePopup(false)}>
            <section className="satellite-modal" role="dialog" aria-modal="true" aria-label="Satellite image of selected waterbody" onMouseDown={(event) => event.stopPropagation()}>
              <header>
                <div>
                  <p className="eyebrow">Selected Waterbody Satellite View</p>
                  <h3>{selected.name}</h3>
                  <span>{selected.latitude.toFixed(5)}, {selected.longitude.toFixed(5)}</span>
                </div>
                <button className="icon-close" title="Close satellite image" onClick={() => setShowSatellitePopup(false)}><X size={20} /></button>
              </header>
              <div className="satellite-image-frame">
                {satellitePreviewUrl ? <img src={satellitePreviewUrl} alt={"Satellite image around " + selected.name} /> : <p>Satellite image is loading...</p>}
                <div className="satellite-target" aria-hidden="true">{"\u{1F4A7}"}</div>
              </div>
              <div className="satellite-modal-meta">
                <strong>{satelliteOutput?.download_urls?.preview ? "Processed Sentinel-2 RGB preview" : "Satellite basemap preview centered on the risk waterbody"}</strong>
                {satelliteLoading && <span>Searching latest Sentinel-2 scene...</span>}
                {satelliteSearch && <span>Sentinel-2: {satelliteSearch.selected_scene.id} | {satelliteSearch.source} | {satelliteSearch.selected_scene.datetime || "date unavailable"} | {satelliteSearch.selected_scene.cloud_cover ?? 0}% cloud</span>}
                <span>Risk: {selected.risk_level} | Breeding {selected.breeding_likelihood}% | Mosquito activity {selected.mosquito_activity_index}% | NDWI {selected.ndwi}</span>
              </div>
              <footer>
                <a className="secondary-action" href={copernicusUrl} target="_blank" rel="noreferrer"><ExternalLink size={16} /> Copernicus Data Space</a>
                <button className="primary-action" disabled={satelliteProcessing} onClick={processSentinel}><Layers size={16} /> Process Real Sentinel Bands</button>
              </footer>
            </section>
          </div>
        )}
      </section>
    </main>
  );
}
