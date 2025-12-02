export interface EncryptedImageRequest {
  ciphertext: string;
  key_id: string;
  metadata?: Record<string, unknown>;
}

export interface EncryptedPredictionResponse {
  ciphertext: string;
  date: string;
}

export interface EncryptedNDayAnalysisResponse {
  ciphertext: string;
}

export interface PredictionView {
  label: string;
  probabilities?: number[];
  date?: string;
}
