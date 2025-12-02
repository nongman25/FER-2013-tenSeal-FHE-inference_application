import { httpClient } from '../../../lib/http/client';
import { EncryptedImageRequest, EncryptedNDayAnalysisResponse, EncryptedPredictionResponse } from '../../../types';

export const emotionApi = {
  analyzeToday(payload: EncryptedImageRequest) {
    return httpClient.post<EncryptedPredictionResponse>('/emotion/analyze-today', payload);
  },
  fetchHistory(days?: number) {
    const query = typeof days === 'number' ? `?days=${days}` : '';
    return httpClient.get<EncryptedNDayAnalysisResponse>(`/emotion/history${query}`);
  },
};
