import { useState, useEffect } from 'react';
import api from '../services/api';

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedEntry, setSelectedEntry] = useState(null);
  
  useEffect(() => {
    loadHistory();
  }, []);
  
  const loadHistory = async () => {
    setLoading(true);
    try {
      const result = await api.getHistory();
      if (result.success) {
        setHistory(result.history);
      } else {
        setError('Failed to load history');
      }
    } catch (err) {
      setError('An error occurred while loading history');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleViewDetails = async (uploadId) => {
    try {
      const result = await api.getHistoryDetail(uploadId);
      if (result.success) {
        setSelectedEntry(result.entry);
      }
    } catch (err) {
      console.error('Error loading details:', err);
    }
  };
  
  const handleViewChart = (uploadId, format = 'html') => {
    window.open(`${api.getChart(format)}&upload_id=${uploadId}`, '_blank');
  };
  
  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString();
  };
  
  if (loading) {
    return <div className="loading">Loading history...</div>;
  }
  
  return (
    <div className="history-container">
      <h2>Analysis History</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="history-content">
        <div className="history-list">
          {history.length === 0 ? (
            <p>No analysis history found</p>
          ) : (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>File</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.upload_id}>
                    <td>{formatDate(entry.timestamp)}</td>
                    <td>{entry.original_filename}</td>
                    <td>
                      {entry.processed ? (
                        <span className="status-processed">Processed</span>
                      ) : (
                        <span className="status-pending">Pending</span>
                      )}
                    </td>
                    <td>
                      <button 
                        onClick={() => handleViewDetails(entry.upload_id)}
                        className="action-btn"
                      >
                        Details
                      </button>
                      {entry.processed && (
                        <button 
                          onClick={() => handleViewChart(entry.upload_id)}
                          className="action-btn"
                        >
                          View Chart
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        {selectedEntry && (
          <div className="history-details">
            <h3>Analysis Details</h3>
            <div className="details-card">
              <p><strong>File:</strong> {selectedEntry.original_filename}</p>
              <p><strong>Date:</strong> {formatDate(selectedEntry.timestamp)}</p>
              <p><strong>Status:</strong> {selectedEntry.processed ? 'Processed' : 'Pending'}</p>
              
              {selectedEntry.processed && selectedEntry.results && (
                <div className="results-summary">
                  <h4>Results Summary</h4>
                  <p><strong>Signals:</strong> {selectedEntry.results.signals_count}</p>
                  {selectedEntry.results.accuracy && (
                    <p><strong>Accuracy:</strong> {selectedEntry.results.accuracy.accuracy_rate?.toFixed(2)}%</p>
                  )}
                  
                  <div className="details-actions">
                    <button 
                      onClick={() => handleViewChart(selectedEntry.upload_id, 'html')}
                      className="action-btn"
                    >
                      View HTML Chart
                    </button>
                    <button 
                      onClick={() => handleViewChart(selectedEntry.upload_id, 'png')}
                      className="action-btn"
                    >
                      Download PNG Chart
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;