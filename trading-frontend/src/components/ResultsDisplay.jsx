const ResultsDisplay = ({ results }) => {
  if (!results) return null;
  
  return (
    <div className="results-card">
      <h3>Analysis Results</h3>
      
      <div className="results-grid">
        <div className="result-item">
          <div className="result-label">Accuracy Rate</div>
          <div className="result-value">{results.accuracy_rate?.toFixed(2)}%</div>
        </div>
        
        <div className="result-item">
          <div className="result-label">Total Signals</div>
          <div className="result-value">{results.total_signals || 0}</div>
        </div>
        
        <div className="result-item">
          <div className="result-label">Accurate Signals</div>
          <div className="result-value">{results.accurate_signals || 0}</div>
        </div>
        
        <div className="result-item">
          <div className="result-label">Long Accuracy</div>
          <div className="result-value">{results.long_accuracy?.toFixed(2)}%</div>
        </div>
        
        <div className="result-item">
          <div className="result-label">Short Accuracy</div>
          <div className="result-value">{results.short_accuracy?.toFixed(2)}%</div>
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;