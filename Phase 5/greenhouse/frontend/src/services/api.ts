const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    }
  );


  if (!response.ok) {

    // FastAPI puts the reason in "detail" - show it instead of only the code
    let detail = "";

    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // response had no JSON body
    }

    throw new Error(
      detail || `API error ${response.status}`
    );
  }


  return response.json();
}



/* =========================
   Health
========================= */

export interface HealthResponse {
  status: string;
  db: string;
}


export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}



/* =========================
   Phase 2 Sensors
========================= */

export interface SensorDto {

  id: string;

  // Phase 2 + Phase 3 compatible fields
  device_type: string;

  role: string;

  device_family: string;

  display_name: string;

  default_config: Record<string, unknown>;

  zone_id: string | null;

  // Phase 5: sampling columns (source of truth, not default_config)
  sampling_interval_seconds: number;

  tracking_enabled: boolean;

}



export function fetchSensors(): Promise<SensorDto[]> {

  return request<SensorDto[]>(
    "/api/sensors"
  );

}



export type SensorAdapter =
  | "simulation"
  | "vendor";


export function createSensor(
  sensorType: "moisture" | "light",
  adapter: SensorAdapter = "simulation"
): Promise<SensorDto> {

  return request<SensorDto>(
    "/api/sensors",
    {
      method: "POST",
      body: JSON.stringify({
        type: sensorType,
        adapter,
      }),
    }
  );

}



/* =========================
   Phase 5 Readings + sampling
========================= */

export type ReadingSource =
  | "simulation"
  | "mqtt"
  | "vendor";


export interface ReadingDto {

  device_id: string;

  value: number;

  unit: string;

  source: ReadingSource;

  recorded_at: string;

}


export interface SamplingDto {

  device_id: string;

  sampling_interval_seconds: number;

  tracking_enabled: boolean;

}


// Runs the sensor adapter, stores the reading and returns it
export function readSensorNow(
  sensorId: string
): Promise<ReadingDto> {

  return request<ReadingDto>(
    `/api/sensors/${sensorId}/read`,
    {
      method: "POST",
    }
  );

}


// Stored readings, newest first
export function fetchReadings(
  sensorId: string,
  limit = 20
): Promise<ReadingDto[]> {

  return request<ReadingDto[]>(
    `/api/sensors/${sensorId}/readings?limit=${limit}`
  );

}


export function updateSampling(
  deviceId: string,
  body: {
    sampling_interval_seconds: number;
    tracking_enabled: boolean;
  }
): Promise<SamplingDto> {

  return request<SamplingDto>(
    `/api/devices/${deviceId}/sampling`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    }
  );

}



/* =========================
   Phase 3 Devices
========================= */


export type DeviceFamily =
  | "simulation"
  | "edge";


export type DeviceRole =
  | "sensor"
  | "actuator";



export interface DeviceDto {

  id: string;

  device_type: string;

  role: DeviceRole;

  device_family: DeviceFamily;

  display_name: string;

  default_config: Record<string, unknown>;

  zone_id?: string | null;

  sampling_interval_seconds?: number;

  tracking_enabled?: boolean;

}




export function fetchDevices(
  params?: {
    family?: DeviceFamily;
    role?: DeviceRole;
  }

): Promise<DeviceDto[]> {


  const query =
    new URLSearchParams();


  if (params?.family) {

    query.append(
      "family",
      params.family
    );

  }


  if (params?.role) {

    query.append(
      "role",
      params.role
    );

  }



  const url =
    query.toString()
      ? `/api/devices?${query.toString()}`
      : "/api/devices";



  return request<DeviceDto[]>(
    url
  );

}




export function provisionDeviceFamily(
  family: DeviceFamily

): Promise<DeviceDto[]> {


  return request<DeviceDto[]>(
    `/api/devices/provision?family=${family}`,
    {
      method: "POST",
    }
  );

}
