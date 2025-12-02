import { useState } from 'react';
import { fheClient } from '../../../lib/crypto/fheClient';
import { preprocessImage, PreprocessedImage } from '../../../lib/crypto/preprocessing';
import { EmotionKeyPair } from '../../../lib/crypto/types';
import { emotionApi } from '../api/emotionApi';
import { PredictionView } from '../../../types';

interface AnalyzeResult {
  prediction: PredictionView;
  keyPair: EmotionKeyPair;
  preprocessed: PreprocessedImage;
}

export function useEmotionFlow() {
  const [lastPrediction, setLastPrediction] = useState<PredictionView | null>(null);
  const [preprocessed, setPreprocessed] = useState<PreprocessedImage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeFile = async (file: File): Promise<AnalyzeResult> => {
    setLoading(true);
    setError(null);
    const keyPair = await fheClient.loadOrCreateKeyPair();
    try {
      const prep = await preprocessImage(file);
      setPreprocessed(prep);
      const encrypted = await fheClient.encryptPreprocessedImage(keyPair, prep.normalized);
      const response = await emotionApi.analyzeToday({ ciphertext: encrypted.payload, key_id: keyPair.keyId });
      const decrypted = await fheClient.decryptPrediction(keyPair, { payload: response.ciphertext });
      const prediction: PredictionView = {
        label: decrypted.label,
        probabilities: decrypted.probabilities,
        date: response.date,
      };
      setLastPrediction(prediction);
      return { prediction, keyPair, preprocessed: prep };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (days?: number) => {
    setLoading(true);
    setError(null);
    const keyPair = await fheClient.loadOrCreateKeyPair();
    try {
      const response = await emotionApi.fetchHistory(days);
      const decrypted = await fheClient.decryptHistoryReport(keyPair, { payload: response.ciphertext });
      return { data: decrypted, keyPair };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch history');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { lastPrediction, preprocessed, loading, error, analyzeFile, fetchHistory };
}
