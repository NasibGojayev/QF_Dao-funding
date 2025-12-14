/**
 * API Client with Automatic Logging
 * Wraps fetch with request/response logging and error handling.
 */

import { logger } from './logger';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
    timeout?: number;
}

interface ApiResponse<T = any> {
    data: T | null;
    error: string | null;
    status: number;
    duration: number;
}

/**
 * Logged fetch wrapper - automatically logs all API requests and responses
 */
export async function apiFetch<T = any>(
    endpoint: string,
    options: FetchOptions = {}
): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    const method = options.method || 'GET';
    const startTime = performance.now();

    // Log the request
    logger.api.request(method, endpoint, options.body);

    try {
        // Add timeout support
        const controller = new AbortController();
        const timeout = options.timeout || 30000;
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        clearTimeout(timeoutId);

        const duration = Math.round(performance.now() - startTime);

        let data: T | null = null;
        const contentType = response.headers.get('content-type');

        if (contentType?.includes('application/json')) {
            try {
                data = await response.json();
            } catch {
                data = null;
            }
        }

        // Log the response
        logger.api.response(method, endpoint, response.status, duration,
            response.status >= 400 ? data : undefined);

        return {
            data,
            error: response.ok ? null : `HTTP ${response.status}`,
            status: response.status,
            duration,
        };
    } catch (error) {
        const duration = Math.round(performance.now() - startTime);

        // Log the error
        logger.api.error(method, endpoint, error);

        return {
            data: null,
            error: error instanceof Error ? error.message : 'Network error',
            status: 0,
            duration,
        };
    }
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
    get: <T = any>(endpoint: string, options?: FetchOptions) =>
        apiFetch<T>(endpoint, { ...options, method: 'GET' }),

    post: <T = any>(endpoint: string, body?: any, options?: FetchOptions) =>
        apiFetch<T>(endpoint, {
            ...options,
            method: 'POST',
            body: body ? JSON.stringify(body) : undefined,
        }),

    put: <T = any>(endpoint: string, body?: any, options?: FetchOptions) =>
        apiFetch<T>(endpoint, {
            ...options,
            method: 'PUT',
            body: body ? JSON.stringify(body) : undefined,
        }),

    patch: <T = any>(endpoint: string, body?: any, options?: FetchOptions) =>
        apiFetch<T>(endpoint, {
            ...options,
            method: 'PATCH',
            body: body ? JSON.stringify(body) : undefined,
        }),

    delete: <T = any>(endpoint: string, options?: FetchOptions) =>
        apiFetch<T>(endpoint, { ...options, method: 'DELETE' }),
};

export default api;
