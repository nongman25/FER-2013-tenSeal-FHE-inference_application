import { ChangeEvent, useState } from 'react';
import { preprocessImage, PreprocessedImage } from '../../../lib/crypto/preprocessing';
import { useEmotionFlow } from '../hooks/useEmotionFlow';

const EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise'];

export default function UploadAndAnalyzeForm() {
  const { analyzeFile, lastPrediction, preprocessed, loading, error } = useEmotionFlow();
  const [localPreview, setLocalPreview] = useState<PreprocessedImage | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    const prep = await preprocessImage(file);
    setLocalPreview(prep);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    try {
      await analyzeFile(selectedFile);
    } catch (err) {
      console.error(err);
    }
  };

  const preview = preprocessed || localPreview;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <div>
          <h2 style={{ margin: '0 0 6px' }}>Encrypt and analyze</h2>
          <p className="notice" style={{ margin: 0 }}>
            Upload a face image, it will be resized to 48×48 grayscale, encrypted, and sent to the backend.
          </p>
        </div>
      </div>

      <div className="grid" style={{ gap: 16, marginTop: 16 }}>
        <label className="input-group">
          <span>Image</span>
          <input type="file" accept="image/*" onChange={handleFileChange} />
        </label>

        {preview ? (
          <div className="preview">
            <div>
              <div className="notice">Original</div>
              <img src={preview.originalUrl} alt="original" />
            </div>
            <div>
              <div className="notice">48×48 grayscale preview</div>
              <img src={preview.grayscaleDataUrl} alt="grayscale preview" />
            </div>
          </div>
        ) : null}

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button className="button" onClick={handleAnalyze} disabled={!selectedFile || loading}>
            {loading ? 'Processing…' : 'Encrypt and Analyze Today'}
          </button>
        </div>

        {error ? <div className="notice">{error}</div> : null}

        {lastPrediction ? (
          <div className="card" style={{ background: 'transparent', border: '1px solid var(--panel-strong)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div className="notice">Prediction</div>
                <h3 style={{ margin: '4px 0' }}>{lastPrediction.label}</h3>
                {lastPrediction.date ? <div className="notice">{lastPrediction.date}</div> : null}
              </div>
              <span className="tag">Encrypted</span>
            </div>
            {lastPrediction.probabilities ? (
              <div className="grid" style={{ marginTop: 12 }}>
                {lastPrediction.probabilities.map((p, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                      <span>{EMOTION_LABELS[idx] ?? `class-${idx}`}</span>
                      <span>{(p * 100).toFixed(1)}%</span>
                    </div>
                    <div className="progress">
                      <span style={{ width: `${Math.min(100, Math.max(0, p * 100))}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="notice" style={{ marginTop: 8 }}>
                Probabilities hidden – ciphertext stays opaque to the server.
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
