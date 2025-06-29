import { useState, useEffect } from 'react';
import sectorApi from '../services/sectorApi';

const SectorPerformance = () => {
  const [period, setPeriod] = useState('1d');
  const [sectorData, setSectorData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData(period);
  }, [period]);

  const fetchData = async (selectedPeriod) => {
    setLoading(true);
    setError('');
    try {
      const [dataResponse, summaryResponse] = await Promise.all([
        sectorApi.fetchSectorData(selectedPeriod),
        sectorApi.fetchSectorSummary(selectedPeriod)
      ]);
      
      if (dataResponse.success) {
        setSectorData(dataResponse.data);
      }
      
      if (summaryResponse) {
        setSummary(summaryResponse);
      }
    } catch (err) {
      setError('Failed to fetch sector data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodChange = (e) => {
    setPeriod(e.target.value);
  };

  // Helper function to determine bar color based on performance
  const getBarColor = (performance) => {
    return performance >= 0 ? '#4caf50' : '#f44336';
  };

  // Calculate max absolute performance for scaling
  const maxPerformance = sectorData.length > 0 
    ? Math.max(...sectorData.map(item => Math.abs(item.performance)))
    : 5; // Default scale if no data

  return (
    <div className="sector-performance-card">
      <div className="sector-header">
        <h3>Sector Performance</h3>
        <select 
          value={period} 
          onChange={handlePeriodChange}
          className="period-selector"
        >
          <option value="1d">Daily</option>
          <option value="7d">Weekly</option>
          <option value="30d">Monthly</option>
          <option value="90d">Quarterly</option>
          <option value="52w">Yearly</option>
        </select>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {loading ? (
        <div className="loading">Loading sector data...</div>
      ) : (
        <>
          {summary && (
            <div className="summary-stats">
              <div className="summary-item">
                <span className="summary-label">Average</span>
                <span className="summary-value" style={{ color: summary.average_performance >= 0 ? '#4caf50' : '#f44336' }}>
                  {summary.average_performance}%
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Positive</span>
                <span className="summary-value positive">{summary.positive_sectors}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Negative</span>
                <span className="summary-value negative">{summary.negative_sectors}</span>
              </div>
            </div>
          )}
          
          <div className="sector-bars">
            {sectorData.map((sector, index) => (
              <div key={index} className="sector-bar-item">
                <div className="sector-name">{sector.sector}</div>
                <div className="bar-container">
                  <div 
                    className="performance-bar"
                    style={{
                      width: `${Math.min(Math.abs(sector.performance) / maxPerformance * 100, 100)}%`,
                      backgroundColor: getBarColor(sector.performance),
                      marginLeft: sector.performance < 0 ? 'auto' : '0'
                    }}
                  />
                </div>
                <div className="performance-value" style={{ color: getBarColor(sector.performance) }}>
                  {sector.performance}%
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default SectorPerformance;