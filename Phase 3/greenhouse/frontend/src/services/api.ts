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
    throw new Error(
      `API error ${response.status}`
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

}



export function fetchSensors(): Promise<SensorDto[]> {

  return request<SensorDto[]>(
    "/api/sensors"
  );

}



export function createSensor(
  sensorType: "moisture" | "light"
): Promise<SensorDto> {

  return request<SensorDto>(
    `/api/sensors?type=${sensorType}`,
    {
      method: "POST",
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