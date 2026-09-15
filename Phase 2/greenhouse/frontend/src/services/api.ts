/**
 * Single place where the frontend talks to the Smart Greenhouse API.
 * Pages and components must not call fetch() directly.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type HealthResponse = {
  status: string
  db: 'ok' | 'fail'
}

export type SensorDto = {
  id: string
  device_type: string
  display_name: string
  default_config: Record<string, unknown>
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`)
  }

  return (await response.json()) as T
}

async function postJson<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let detail = `Request to ${path} failed with status ${response.status}`
    try {
      const data = (await response.json()) as { detail?: string }
      if (data.detail) detail = data.detail
    } catch {
      // The fallback message above is enough if the response is not JSON.
    }
    throw new Error(detail)
  }

  return (await response.json()) as T
}

export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>('/health')
}

export function fetchSensors(): Promise<SensorDto[]> {
  return getJson<SensorDto[]>('/api/sensors')
}

export function createSensor(
  type: 'moisture' | 'light',
  displayName?: string,
): Promise<SensorDto> {
  return postJson<SensorDto>('/api/sensors', {
    type,
    display_name: displayName?.trim() || null,
  })
}
