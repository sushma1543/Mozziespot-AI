export type RiskLevel = "Low" | "Medium" | "High" | "Critical";

export type Detection = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  confidence: number;
  risk_score: number;
  risk_level: RiskLevel;
  days_persistent: number;
  ndwi: number;
  temperature: number;
  population_density: number;
  disease_index: Record<string, number>;
  breeding_likelihood: number;
  mosquito_activity_index: number;
  habitat_type: string;
  reasons: string[];
  recommendation: string;
  state: string;
  district: string;
  village: string;
  authority_type: string;
  authority_name: string;
  last_updated: string;

  distance_m?: number;
  search_match?: boolean;
  exact_place_match?: boolean;
  approximate_place?: boolean;
  zoom_to_place?: boolean;
  geocoded_place?: boolean;
  gazetteer_place?: boolean;
  near_search_area?: boolean;
  is_waterbody?: boolean;
  marker_type?: "search" | "waterbody-risk" | "non-water";
  evidence_status?: string;
  mosquito_risk_score?: number;
  mosquito_risk_level?: "Very Low" | "Low" | "Moderate" | "High" | "Severe";
  water_type?: string;
  advanced_disease_index?: Record<string, number>;
  advanced_factors?: Record<string, number>;
  explainability?: {
    formula: string;
    contributions: Record<string, number>;
    top_factors: Array<[string, number]>;
  };
};

export type Summary = {
  water_bodies: number;
  high_risk_zones: number;
  alerts_sent: number;
  ai_confidence: number;
  disease_index: number;
};

export type LocationCatalog = {
  states: Array<{
    name: string;
    districts: Array<{
      name: string;
      latitude: number;
      longitude: number;
      villages: string[];
    }>;
  }>;
};

export type StateRiskResponse = {
  status: string;
  note: string;
  summary: {
    total_points: number;
    red_zones: number;
    yellow_zones: number;
    green_zones: number;
    updated_at: string;
  };
  results: Detection[];
};

/* ===========================
   SATELLITE TYPES
=========================== */

export type SatelliteDownloadResponse = {
  status: string;
  folder: string;
  manifest?: string;
  message?: string;
  selected_scene?: SatelliteScene;
  real_download_enabled?: boolean;
};

export type SatelliteProcessResponse = {
  status: string;
  folder?: string;
  mode?: string;

  outputs: {
    rgb: string;
    preview?: string;
    ndwi: string;
    mndwi?: string;
    ndvi?: string;
    water: string;
    water_mask?: string;
  };
  indices?: Record<string, string>;
  download_urls?: Record<string, string>;
  waterbody_geojson?: string | null;
  waterbody_download_url?: string | null;
  missing_bands?: string[];
  statistics?: {
    total_pixels: number;
    clear_pixels: number;
    cloud_or_invalid_pixels: number;
    probable_water_pixels: number;
    probable_water_percent: number;
    probable_waterbodies: number;
  } | null;
  water_analysis?: {
    classes: string[];
  };
  message?: string;
};

export type SatelliteScene = {
  id: string;
  source: string;
  datetime?: string;
  cloud_cover?: number;
  bbox?: number[];
  asset_count?: number;
};

export type SatelliteSearchResponse = {
  status: string;
  online: boolean;
  source: string;
  scenes: SatelliteScene[];
  selected_scene: SatelliteScene;
  date_window: {
    start_date: string;
    end_date: string;
  };
};

export type ModuleStatus = {
  name: string;
  status: string;
  items: string[];
};

export type AnalyticsResponse = {
  status: string;
  total_water_bodies: number;
  total_stagnant_water: number;
  high_risk_villages: number;
  severe_zones: number;
  water_type_counts: Record<string, number>;
  disease_trend: Array<{ disease: string; average: number }>;
  monthly_trend: Array<{ month: string; water_bodies: number; severe_risk: number }>;
  top_priority: Detection[];
};
export type SatelliteLayersResponse = {
  status: string;

  layers: {
    rgb: string;
    ndwi: string;
    water_mask: string;
    heatmap: string;
    district_boundary: string;
    mandal_boundary: string;
    village_boundary: string;
  };
};

export type ExportResponse = {
  status: string;
  file: string;
};

export type TelegramStatus = {
  status: string;
  sent: boolean;
  message: string;
};

export type AdminRolesResponse = {
  roles: Array<{ role: string; dashboard: string }>;
  demo_login: { email: string; password: string };
};

export type ValidationStatus = {
  mode: string;
  operational_map_source: string;
  validated_model_inference: boolean;
  ground_truth_ready: boolean;
  dataset_path: string;
  models: Array<{ name: string; trained_weights: boolean; required_files: string[] }>;
  experiment: null | {
    dataset: string;
    created_at: string;
    device: string;
    split_strategy: string;
    samples: Record<string, number>;
    models: Record<string, {
      history: Array<{ epoch: number; training_loss: number; validation_loss: number }>;
      test: {
        loss: number;
        metrics: {
          precision: number | null;
          recall: number | null;
          specificity: number | null;
          accuracy: number | null;
          f1: number | null;
          iou: number | null;
          dice: number | null;
        };
      };
    }>;
  };
  available_when_data_supplied: string[];
  not_claimed: string[];
};

/* ===========================
   JSON HELPER
=========================== */

const json = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }

  return response.json();
};

/* ===========================
   API
=========================== */

export const api = {
  /* Dashboard */

  summary: () =>
    json<Summary>("/api/dashboard"),

  detections: () =>
    json<Detection[]>("/api/detections"),

  locations: () =>
    json<LocationCatalog>("/api/locations"),

  advancedModules: () =>
    json<{ status: string; modules: ModuleStatus[] }>("/api/advanced/modules"),

  analytics: () =>
    json<AnalyticsResponse>("/api/analytics"),

  adminRoles: () =>
    json<AdminRolesResponse>("/api/admin/roles"),

  validationStatus: () =>
    json<ValidationStatus>("/api/validation/status"),

  /* ===========================
     GEOCODING
  =========================== */

  geocodePlace: async (
    query: string,
    state = "All",
    district = "All"
  ) => {

    const response = await fetch("/api/geocode/place", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query,
        state,
        district
      })
    });

    if (!response.ok) {
      return {
        found: false,
        message: "Place not found"
      } as {
        found: false;
        message: string;
      };
    }

    return response.json() as Promise<{
      found: true;
      detection: Detection;
      source: string;
      display_name?: string;
    }>;
  },

  /* ===========================
     STATE RISK
  =========================== */

  stateRisk: (params: {
    state?: string;
    district?: string;
    village?: string;
    q?: string;
    minimum?: string;
  }) => {

    const search = new URLSearchParams({
      state: params.state || "All",
      district: params.district || "All",
      village: params.village || "All",
      q: params.q || "",
      minimum: params.minimum || "Low"
    });

    return json<StateRiskResponse>(
      "/api/state-risk?" + search.toString()
    );
  },

  /* ===========================
     SATELLITE
  =========================== */

  downloadSatellite: async (latitude?: number, longitude?: number) => {
    const response = await fetch("/api/satellite/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latitude, longitude, padding: 0.03 })
    });
    if (!response.ok) throw new Error("Satellite download failed");
    return response.json() as Promise<SatelliteDownloadResponse>;
  },

  searchSatellite: async (latitude?: number, longitude?: number) => {

    const response = await fetch(
      "/api/satellite/search",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ latitude, longitude, padding: 0.03, cloud_cover: 20 })
      }
    );

    if (!response.ok) {
      throw new Error("Satellite search failed");
    }

    return response.json() as Promise<SatelliteSearchResponse>;
  },

  processSatellite: async (latitude?: number, longitude?: number) => {

    const response = await fetch(
      "/api/satellite/process",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude, longitude, padding: 0.03, cloud_cover: 20 })
      }
    );

    if (!response.ok) {
      throw new Error("Satellite processing failed");
    }

    return response.json() as Promise<SatelliteProcessResponse>;
  },
  /* ===========================
   GIS LAYERS
=========================== */

loadSatelliteLayers: () =>
  json<SatelliteLayersResponse>(
    "/api/satellite/layers"
  ),

/* ===========================
   EXPORTS
=========================== */

exportCSV: () =>
  json<ExportResponse>(
    "/api/export/csv"
  ),

exportGeoJSON: () =>
  json<ExportResponse>(
    "/api/export/geojson"
  ),

exportExcel: () =>
  json<ExportResponse>(
    "/api/export/excel"
  ),

exportShapefile: () =>
  json<ExportResponse>(
    "/api/export/shapefile"
  ),

/* ===========================
   TELEGRAM
=========================== */

telegramStatus: () =>
  json<TelegramStatus>(
    "/api/telegram/status"
  ),

  /* ===========================
     SEARCH
  =========================== */

  searchMosquitoHabitats: (
    query = "",
    minimum = "Medium"
  ) => {

    const params = new URLSearchParams({
      q: query,
      minimum
    });

    return json<{
      status: string;
      note: string;
      results: Detection[];
    }>(
      "/api/search/mosquito-habitats?" +
      params.toString()
    );
  },

  /* ===========================
     SPOT ANALYSIS
  =========================== */

  analyzeSpot: async (
    latitude: number,
    longitude: number,
    name?: string
  ) => {

    const response = await fetch(
      "/api/analyze/spot",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          latitude,
          longitude,
          name
        })
      }
    );

    if (!response.ok) {
      throw new Error(
        "Spot analysis failed: " +
        response.status
      );
    }

    return response.json() as Promise<{
      status: string;
      detection: Detection;
    }>;
  },

  /* ===========================
     NEARBY RISK
  =========================== */

  nearbyRisk: async (
    latitude: number,
    longitude: number,
    radius_m = 2500
  ) => {

    const response = await fetch(
      "/api/nearby-risk",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          latitude,
          longitude,
          radius_m
        })
      }
    );

    if (!response.ok) {
      throw new Error(
        "Nearby risk failed: " +
        response.status
      );
    }

    return response.json() as Promise<{
      status: string;
      current_spot: Detection;
      nearby: Detection[];
      radius_m: number;
      updated_at: string;
    }>;
  },

  /* ===========================
     ALERTS
  =========================== */

  sendAlert: async (
    detection: Detection,
    whatsapp_number = ""
  ) => {

    const response = await fetch(
      "/api/alerts/send",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          detection,
          whatsapp_number
        })
      }
    );
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || "Alert could not be sent");
    return payload as {
      telegram: {
        sent?: boolean;
        reason?: string;
      };
      
      email: unknown;
      whatsapp_url: string;
      telegram_url: string;
      message: string;
    };
  }
};
