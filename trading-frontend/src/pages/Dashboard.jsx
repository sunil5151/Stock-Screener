import { useState } from 'react';
import api from '../services/api';
import ResultsDisplay from '../components/ResultsDisplay';
import SignalsTable from '../components/SignalsTable';
import SectorPerformance from '../components/SectorPerformance';

const Dashboard = () => {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);
  const [signals, setSignals] = useState(null);
  const [chartUrl, setChartUrl] = useState('');
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
    }
  };
  
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    setError('');
    setUploading(true);
    
    try {
      const result = await api.uploadCSV(file);
      if (result.success) {
        // Proceed to processing
        await handleProcess();
      } else {
        setError(result.message || 'Upload failed');
      }
    } catch (err) {
      setError('An error occurred during upload');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };
  
  const handleProcess = async () => {
    setProcessing(true);
    setError('');
    
    try {
      const result = await api.processCSV();
      if (result.success) {
        // Fetch results and signals
        const resultsData = await api.getResults();
        const signalsData = await api.getSignals();
        
        setResults(resultsData);
        setSignals(signalsData);
        // Use the chart-iframe endpoint instead of generate-chart
        setChartUrl(api.getChartIframe());
      } else {
        setError(result.error || 'Processing failed');
      }
    } catch (err) {
      setError('An error occurred during processing');
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };
  
  const handleExport = () => {
    window.open(api.exportSignals(), '_blank');
  };
  
  return (
    <div className="dashboard-container">
      <h2>Trading Analysis Dashboard</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="dashboard-grid">
        <div className="main-content">
          <div className="upload-section">
            <h3>Upload CSV Data</h3>
            <form onSubmit={handleUpload}>
              <div className="file-input-container">
                <input 
                  type="file" 
                  id="csv-file" 
                  accept=".csv" 
                  onChange={handleFileChange} 
                  disabled={uploading || processing}
                />
                <label htmlFor="csv-file">
                  {fileName || 'Choose CSV file'}
                </label>
              </div>
              
              <button 
                type="submit" 
                disabled={!file || uploading || processing}
              >
                {uploading ? 'Uploading...' : processing ? 'Processing...' : 'Upload & Process'}
              </button>
            </form>
          </div>
          
          {results && (
            <div className="results-section">
              <ResultsDisplay results={results} />
              
              <div className="chart-container">
                <h3>Trading Chart</h3>
                {chartUrl ? (
                  <iframe 
                    src={chartUrl} 
                    title="Trading Chart" 
                    width="100%" 
                    height="600px" 
                    style={{ border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                ) : (
                  <div className="no-chart">
                    No chart data available. Please upload and process a CSV file first.
                  </div>
                )}
              </div>
              
              <div className="signals-section">
                <h3>Trading Signals</h3>
                <SignalsTable signals={signals} />
                <button onClick={handleExport} className="export-btn">
                  Export Signals as CSV
                </button>
              </div>
            </div>
          )}
        </div>
        
        <div className="sidebar">
          <SectorPerformance />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;