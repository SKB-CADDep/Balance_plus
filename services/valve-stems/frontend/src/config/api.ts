/** API endpoints already contain /api/v1; an empty base uses the current origin. */
export const resolveApiBaseUrl = (value: string | undefined): string =>
    (value ?? "").trim().replace(/\/+$/, "");
