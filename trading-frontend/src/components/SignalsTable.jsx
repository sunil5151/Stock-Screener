const SignalsTable = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return <p>No signals found</p>;
  }
  
  // Format date strings
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };
  
  return (
    <div className="signals-table-container">
      <table className="signals-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Cross Time</th>
            <th>Volume Spike</th>
            <th>Big Candle</th>
            <th>Breakout</th>
            <th>S/R Confirmed</th>
            <th>Accurate</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((signal, index) => (
            <tr key={index}>
              <td>{signal.Type === 'LONG' ? '🔼 BUY' : '🔽 SELL'}</td>
              <td>{formatDate(signal.Cross_Time)}</td>
              <td>{signal.Volume_Spike_Time ? '✅' : '❌'}</td>
              <td>{signal.Big_Candle_Time ? '✅' : '❌'}</td>
              <td>{signal.Breakout_Time ? '✅' : '❌'}</td>
              <td>{signal.SR_Confirmed ? '✅' : '❌'}</td>
              <td>{signal.Accuracy === true ? '✅' : signal.Accuracy === false ? '❌' : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SignalsTable;