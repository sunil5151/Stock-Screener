const API_URL = 'http://localhost:8000'; // Adjust if your backend runs on a different port

const api = {
  // Auth endpoints
  register: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    return response.json();
  },
  
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    return response.json();
  },
  
  logout: async () => {
    const response = await fetch(`${API_URL}/logout`, {
      method: 'POST',
      credentials: 'include'
    });
    return response.json();
  },
  
  getUser: async () => {
    const response = await fetch(`${API_URL}/me`, {
      credentials: 'include'
    });
    return response.json();
  },
  
  // CSV processing endpoints
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/upload-csv`, {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    return response.json();
  },
  
  processCSV: async () => {
    const response = await fetch(`${API_URL}/process-csv`, {
      method: 'POST',
      credentials: 'include'
    });
    return response.json();
  },
  
  getResults: async () => {
    const response = await fetch(`${API_URL}/results`, {
      credentials: 'include'
    });
    return response.json();
  },
  
  getSignals: async () => {
    const response = await fetch(`${API_URL}/signals`, {
      credentials: 'include'
    });
    return response.json();
  },
  
  // Chart and history endpoints
  getChart: (format = 'html') => {
    return `${API_URL}/generate-chart?format=${format}`;
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
    
    const response = await fetch(url, {
      credentials: 'include'
    });
    return response.json();
  },
  
  checkChartStatus: async (uploadId = null) => {
    const url = uploadId 
      ? `${API_URL}/chart-status?upload_id=${uploadId}` 
      : `${API_URL}/chart-status`;
    
    const response = await fetch(url, {
      credentials: 'include'
    });
    return response.json();
  },
  
  getHistory: async () => {
    const response = await fetch(`${API_URL}/history`, {
      credentials: 'include'
    });
    return response.json();
  },
  
  getHistoryDetail: async (uploadId) => {
    const response = await fetch(`${API_URL}/history/${uploadId}`, {
      credentials: 'include'
    });
    return response.json();
  },
  
  exportSignals: () => {
    return `${API_URL}/export-signals`;
  }
};

export default api;