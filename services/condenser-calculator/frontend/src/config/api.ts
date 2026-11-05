export function resolveApiBaseUrl(configuredUrl?: string): string {
    return configuredUrl?.trim().replace(/\/+$/, "") ?? "";
}
