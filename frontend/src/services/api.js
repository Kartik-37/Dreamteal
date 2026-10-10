/**
 * DreamTeal Central API Client
 *
 * Handles HTTP requests, Django Session Authentication, CSRF token management,
 * and normalized error responses for all frontend feature modules.
 */

const BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || '';

/**
 * Normalized API Error class providing structured error information.
 */
export class ApiError extends Error {
  constructor(message, { status = 0, data = null, isNetwork = false } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.isNetwork = isNetwork;
    this.isAuthError = status === 401 || status === 403;
    this.isNotFound = status === 404;
    this.isConflict = status === 409;
    this.isValidationError = status === 400;
  }
}

/**
 * Extract CSRF token from document.cookie if available.
 */
export function getCsrfFromCookie() {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[2]) : null;
}

// In-memory cached CSRF token
let cachedCsrfToken = null;

/**
 * Set or update the cached CSRF token.
 */
export function setCachedCsrfToken(token) {
  cachedCsrfToken = token;
}

/**
 * Fetch a fresh CSRF token from Django backend if needed.
 */
export async function ensureCsrfToken() {
  // Check cookie first
  const cookieToken = getCsrfFromCookie();
  if (cookieToken) {
    cachedCsrfToken = cookieToken;
    return cookieToken;
  }

  if (cachedCsrfToken) {
    return cachedCsrfToken;
  }

  try {
    const res = await fetch(`${BASE_URL}/api/v1/users/csrf/`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });

    if (res.ok) {
      const data = await res.json();
      if (data && data.csrftoken) {
        cachedCsrfToken = data.csrftoken;
        return data.csrftoken;
      }
    }
  } catch (err) {
    // Graceful fallback; will let unsafe request attempt or surface error
    console.warn('Unable to pre-fetch CSRF token:', err.message);
  }

  // Fallback to cookie check again in case response set the cookie
  const refreshedCookie = getCsrfFromCookie();
  if (refreshedCookie) {
    cachedCsrfToken = refreshedCookie;
  }
  return cachedCsrfToken;
}

/**
 * Core request wrapper
 *
 * @param {string} endpoint - Path relative to base URL (e.g. '/api/v1/media/')
 * @param {object} options - Fetch options (method, headers, body, params)
 * @returns {Promise<any>}
 */
export async function apiClient(endpoint, options = {}) {
  const {
    method = 'GET',
    headers = {},
    body = null,
    params = null,
    ...rest
  } = options;

  // Build full URL with query parameters
  let url = `${BASE_URL}${endpoint}`;
  if (params && typeof params === 'object') {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        searchParams.append(key, val);
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const upperMethod = method.toUpperCase();
  const isUnsafe = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(upperMethod);

  const requestHeaders = {
    Accept: 'application/json',
    ...headers,
  };

  if (body && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  // Attach CSRF token for unsafe methods
  if (isUnsafe) {
    let csrfToken = getCsrfFromCookie() || cachedCsrfToken;
    if (!csrfToken) {
      csrfToken = await ensureCsrfToken();
    }
    if (csrfToken) {
      requestHeaders['X-CSRFToken'] = csrfToken;
    }
  }

  const fetchOptions = {
    method: upperMethod,
    headers: requestHeaders,
    credentials: 'include', // Mandatory for Django session cookies
    ...rest,
  };

  if (body) {
    fetchOptions.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, fetchOptions);
  } catch (networkError) {
    throw new ApiError(
      networkError.message || 'Network error: Failed to reach DreamTeal server.',
      { isNetwork: true }
    );
  }

  // Check for updated CSRF cookie after request
  const updatedCookie = getCsrfFromCookie();
  if (updatedCookie) {
    cachedCsrfToken = updatedCookie;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  // Parse response body safely
  let responseData = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      responseData = await response.json();
    } catch {
      responseData = null;
    }
  } else {
    try {
      responseData = await response.text();
    } catch {
      responseData = null;
    }
  }

  if (!response.ok) {
    // Construct meaningful error message
    let errorMessage = `HTTP ${response.status} ${response.statusText}`;
    if (responseData && typeof responseData === 'object') {
      if (responseData.detail) {
        errorMessage = responseData.detail;
      } else if (responseData.message) {
        errorMessage = responseData.message;
      } else if (responseData.non_field_errors) {
        errorMessage = Array.isArray(responseData.non_field_errors)
          ? responseData.non_field_errors.join(' ')
          : String(responseData.non_field_errors);
      } else {
        // Validation errors per field
        const firstFieldKey = Object.keys(responseData)[0];
        if (firstFieldKey && Array.isArray(responseData[firstFieldKey])) {
          errorMessage = `${firstFieldKey}: ${responseData[firstFieldKey][0]}`;
        }
      }
    } else if (typeof responseData === 'string' && responseData.length > 0) {
      errorMessage = responseData.slice(0, 100);
    }

    throw new ApiError(errorMessage, {
      status: response.status,
      data: responseData,
    });
  }

  return responseData;
}
