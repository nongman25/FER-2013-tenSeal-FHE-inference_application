import { useState } from 'react';
import { useEmotionFlow } from '../hooks/useEmotionFlow';

export default function HistoryView() {
  const { fetchHistory, loading, error } = useEmotionFlow();
  const [days, setDays] = useState<number>(10);
  const [report, setReport] = useState<unknown>(null);

  const handleFetch = async () => {
    try {
      const { data } = await fetchHistory(days);
      setReport(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>N-day encrypted analysis</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="number"
            min={1}
            value={days}
            onChange={(e) => setDays(Number(e.target.value) || 1)}
            style={{ width: 90 }}
          />
          <button className="button" onClick={handleFetch} disabled={loading}>
            {loading ? 'Fetching…' : 'Fetch history'}
          </button>
        </div>
      </div>
      {error ? <div className="notice">{error}</div> : null}
      {report ? (
        <div style={{ marginTop: 12 }}>
          <div className="notice">Decrypted summary (stub format)</div>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="notice" style={{ marginTop: 8 }}>
          No report yet. Fetch history to see aggregated ciphertext.
        </div>
      )}
    </div>
  );
}
