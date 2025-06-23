const API_URL = 'http://localhost:8000'; // Adjust if your backend runs on a different port

// Helper function to handle API responses
const handleResponse = async (response) => {
  const contentType = response.headers.get('content-type');
  
  if (!response.ok) {
    // Check if response is HTML (error page)
    if (contentType && contentType.includes('text/html')) {
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }
    
    // Try to parse JSON error
    try {
      const errorData = await response.json();
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
    } catch {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }
  
  // Ensure response is JSON for endpoints that should return JSON
  if (contentType && !contentType.includes('application/json')) {
    // For some endpoints, non-JSON might be expected, so we'll be more lenient
    console.warn('Non-JSON response received:', contentType);
  }
  
  try {
    return await response.json();
  } catch (jsonError) {
    // If JSON parsing fails, return the text content
    const text = await response.text();
    throw new Error(`Invalid JSON response: ${text.substring(0, 100)}...`);
  }
};

const api = {
  // Auth endpoints
  register: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Register error:', error);
      throw error;
    }
  },
  
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },
  
  logout: async () => {
    try {
      const response = await fetch(`${API_URL}/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  },
  
  getUser: async () => {
    try {
      const response = await fetch(`${API_URL}/me`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Get user error:', error);
      throw error;
    }
  },
  
  // CSV processing endpoints
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_URL}/upload-csv`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Upload CSV error:', error);
      throw error;
    }
  },
  
  processCSV: async () => {
    try {
      const response = await fetch(`${API_URL}/process-csv`, {
        method: 'POST',
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Process CSV error:', error);
      throw error;
    }
  },
  
  getResults: async () => {
    try {
      const response = await fetch(`${API_URL}/results`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Get results error:', error);
      throw error;
    }
  },
  
  getSignals: async () => {
    try {
      const response = await fetch(`${API_URL}/signals`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Get signals error:', error);
      throw error;
    }
  },
  
  // Chart and history endpoints
  getChart: (format = 'html', uploadId = null) => {
    const baseUrl = `${API_URL}/generate-chart?format=${format}`;
    return uploadId ? `${baseUrl}&upload_id=${uploadId}` : baseUrl;
  },
  
  // Add these new methods
  getChartIframe: (uploadId = null) => {
    return uploadId 
      ? `${API_URL}/chart-iframe?upload_id=${uploadId}` 
      : `${API_URL}/chart-iframe`;
  },
  
  getChartHtml: async (uploadId = null) => {
    const url = uploadId 
      ? `${API_URL}/chart-html?upload_id=${uploadId}` 
      : `${API_URL}/chart-html`;
    
    try {
      const response = await fetch(url, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Get chart HTML error:', error);
      throw error;
    }
  },
  
  checkChartStatus: async (uploadId = null) => {
    const url = uploadId 
      ? `${API_URL}/chart-status?upload_id=${uploadId}` 
      : `${API_URL}/chart-status`;
    
    try {
      const response = await fetch(url, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Check chart status error:', error);
      throw error;
    }
  },
  
  getHistory: async () => {
    try {
      const response = await fetch(`${API_URL}/history`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Get history error:', error);
      throw error;
    }
  },
  
  getHistoryDetail: async (uploadId) => {
    try {
      const response = await fetch(`${API_URL}/history/${uploadId}`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Get history detail error:', error);
      throw error;
    }
  },
  
  exportSignals: () => {
    return `${API_URL}/export-signals`;
  }
};

export default api;
