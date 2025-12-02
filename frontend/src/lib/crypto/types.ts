export interface EmotionCipherText {
  payload: string;
}

export interface EmotionKeyPair {
  keyId: string;
  publicKey: string;
  privateKey?: string;
}

export interface FHEClient {
  loadOrCreateKeyPair(): Promise<EmotionKeyPair>;
  encryptPreprocessedImage(keyPair: EmotionKeyPair, data: number[]): Promise<EmotionCipherText>;
  decryptPrediction(
    keyPair: EmotionKeyPair,
    ciphertext: EmotionCipherText,
  ): Promise<{ label: string; probabilities?: number[] }>; 
  decryptHistoryReport(keyPair: EmotionKeyPair, ciphertext: EmotionCipherText): Promise<unknown>;
  exportKeyPair(keyPair: EmotionKeyPair): string;
  importKeyPair(serialized: string): EmotionKeyPair;
}
