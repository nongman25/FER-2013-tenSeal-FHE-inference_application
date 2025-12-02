export interface PreprocessedImage {
  normalized: number[];
  grayscaleDataUrl: string;
  originalUrl: string;
}

export const TARGET_SIZE = 48;
// TODO: sync with backend normalization_stats.json via API
export const NORMALIZATION_MEAN = 0.507;
export const NORMALIZATION_STD = 0.255;

function normalize(value: number) {
  return (value - NORMALIZATION_MEAN) / Math.max(NORMALIZATION_STD, 1e-6);
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(file); // caller may revoke if needed
  });
}

export async function preprocessImage(file: File): Promise<PreprocessedImage> {
  const img = await loadImage(file);
  const canvas = document.createElement('canvas');
  const previewCanvas = document.createElement('canvas');
  canvas.width = TARGET_SIZE;
  canvas.height = TARGET_SIZE;
  previewCanvas.width = TARGET_SIZE;
  previewCanvas.height = TARGET_SIZE;

  const ctx = canvas.getContext('2d');
  const previewCtx = previewCanvas.getContext('2d');
  if (!ctx || !previewCtx) {
    throw new Error('Unable to access canvas context');
  }

  ctx.drawImage(img, 0, 0, TARGET_SIZE, TARGET_SIZE);
  const imageData = ctx.getImageData(0, 0, TARGET_SIZE, TARGET_SIZE);
  const normalized: number[] = [];
  const grayPixels = new Uint8ClampedArray(imageData.data.length);

  for (let i = 0; i < imageData.data.length; i += 4) {
    const r = imageData.data[i];
    const g = imageData.data[i + 1];
    const b = imageData.data[i + 2];
    const gray = 0.299 * r + 0.587 * g + 0.114 * b;
    const normalizedGray = normalize(gray / 255);
    normalized.push(normalizedGray);
    grayPixels[i] = gray;
    grayPixels[i + 1] = gray;
    grayPixels[i + 2] = gray;
    grayPixels[i + 3] = 255;
  }

  const grayImageData = new ImageData(grayPixels, TARGET_SIZE, TARGET_SIZE);
  previewCtx.putImageData(grayImageData, 0, 0);

  return {
    normalized,
    grayscaleDataUrl: previewCanvas.toDataURL(),
    originalUrl: img.src,
  };
}
