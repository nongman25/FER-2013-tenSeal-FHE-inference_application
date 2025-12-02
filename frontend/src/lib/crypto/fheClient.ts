import { EmotionCipherText, EmotionKeyPair, FHEClient } from './types';

const KEYPAIR_STORAGE_KEY = 'fhe-emotion-keypair';

function encodeBase64(value: unknown): string {
  return btoa(JSON.stringify(value));
}

function decodeBase64(payload: string): any {
  try {
    return JSON.parse(atob(payload));
  } catch (err) {
    console.warn('Failed to decode ciphertext', err);
    return null;
  }
}

function loadStoredKeyPair(): EmotionKeyPair | null {
  const raw = localStorage.getItem(KEYPAIR_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as EmotionKeyPair;
  } catch (err) {
    console.warn('Failed to parse stored key pair', err);
    return null;
  }
}

function persistKeyPair(pair: EmotionKeyPair) {
  localStorage.setItem(KEYPAIR_STORAGE_KEY, JSON.stringify(pair));
}

function createKeyPair(): EmotionKeyPair {
  const keyId = `key-${crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(16)}`;
  return {
    keyId,
    publicKey: `public-${keyId}`,
    privateKey: `private-${keyId}`,
  };
}

async function loadOrCreateKeyPair(): Promise<EmotionKeyPair> {
  const existing = loadStoredKeyPair();
  if (existing) return existing;
  const created = createKeyPair();
  persistKeyPair(created);
  return created;
}

async function encryptPreprocessedImage(keyPair: EmotionKeyPair, data: number[]): Promise<EmotionCipherText> {
  // TODO: Replace stub serialization with real TenSEAL client-side encryption
  const payload = encodeBase64({ key_id: keyPair.keyId, data, ts: Date.now() });
  return { payload };
}

async function decryptPrediction(
  keyPair: EmotionKeyPair,
  ciphertext: EmotionCipherText,
): Promise<{ label: string; probabilities?: number[] }> {
  const decoded = decodeBase64(ciphertext.payload);
  if (decoded && decoded.prediction) {
    return {
      label: decoded.prediction,
      probabilities: decoded.probabilities,
    };
  }
  // Stub path: if backend echoes encrypted image, we cannot decrypt; return placeholder
  return { label: 'encrypted', probabilities: undefined };
}

async function decryptHistoryReport(keyPair: EmotionKeyPair, ciphertext: EmotionCipherText): Promise<unknown> {
  return decodeBase64(ciphertext.payload);
}

function exportKeyPair(keyPair: EmotionKeyPair): string {
  return encodeBase64(keyPair);
}

function importKeyPair(serialized: string): EmotionKeyPair {
  const parsed = decodeBase64(serialized) as EmotionKeyPair;
  if (!parsed?.keyId) {
    throw new Error('Invalid key pair payload');
  }
  persistKeyPair(parsed);
  return parsed;
}

export const fheClient: FHEClient = {
  loadOrCreateKeyPair,
  encryptPreprocessedImage,
  decryptPrediction,
  decryptHistoryReport,
  exportKeyPair,
  importKeyPair,
};
