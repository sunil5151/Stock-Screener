const API_URL = 'http://localhost:8000';

const handleResponse = async (response) => {
  const contentType = response.headers.get('content-type');
  
  if (!response.ok) {
    if (contentType && contentType.includes('text/html')) {
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }
    try {
      const errorData = await response.json();
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
    } catch {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }
  
  if (contentType && !contentType.includes('application/json')) {
    console.warn('Non-JSON response received:', contentType);
  }
  
  try {
    return await response.json();
  } catch (jsonError) {
    const text = await response.text();
    throw new Error(`Invalid JSON response: ${text.substring(0, 100)}...`);
  }
};

const sectorApi = {
  fetchSectorData: async (period) => {
    try {
      const response = await fetch(`${API_URL}/sector-performance/${period}`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error(`Error fetching sector data for ${period}:`, error);
      throw error;
    }
  },

  fetchSectorSummary: async (period) => {
    try {
      const response = await fetch(`${API_URL}/sector-summary/${period}`, {
        credentials: 'include'
      });
      return await handleResponse(response);
    } catch (error) {
      console.error(`Error fetching sector summary for ${period}:`, error);
      throw error;
    }
  },
};

export default sectorApi;