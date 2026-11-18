/**
 * A quick look at a photo before it is sent: is it blurry, washed out by glare, too dark, or too small
 * to read the small print? Runs in the browser on a downscaled copy (the photo does not leave the phone
 * for this), with plain image statistics, not a model. It only warns; the family can always keep a photo.
 * Thresholds are deliberately cautious and still need checking against the labelled eval photos.
 */
export type PhotoIssue = "blurry" | "glare" | "dark" | "small";

export const LIMITS = {
  side: 480,          // analyse at this long side
  blurVariance: 60,   // variance of the Laplacian below this reads as blurry at that size (a sharp phone photo
                      // scored 563; Gaussian blur radius 2 scored 76, radius 4 scored 13: only clear blur is flagged)
  glareShare: 0.06,   // share of near-white pixels above this reads as glare on foil
  glareLevel: 250,
  darkMean: 55,       // mean brightness below this reads as too dark
  minSide: 700,       // a strip photo smaller than this on its short side loses the small print
};

/** Pure: grey pixels (0–255, row-major) of the downscaled copy + the original size -> issues. */
export function assessPixels(grey: ArrayLike<number>, w: number, h: number, origW: number, origH: number): PhotoIssue[] {
  const issues: PhotoIssue[] = [];
  let sum = 0;
  let bright = 0;
  for (let i = 0; i < grey.length; i++) {
    sum += grey[i];
    if (grey[i] >= LIMITS.glareLevel) bright++;
  }
  const mean = sum / grey.length;
  // variance of the 4-neighbour Laplacian over the interior
  let n = 0;
  let lsum = 0;
  let lsq = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const c = y * w + x;
      const lap = grey[c - 1] + grey[c + 1] + grey[c - w] + grey[c + w] - 4 * grey[c];
      lsum += lap;
      lsq += lap * lap;
      n++;
    }
  }
  const variance = n ? lsq / n - (lsum / n) ** 2 : 0;
  if (mean < LIMITS.darkMean) issues.push("dark");
  else if (variance < LIMITS.blurVariance) issues.push("blurry"); // a dark photo is also flat: say dark only
  if (bright / grey.length > LIMITS.glareShare) issues.push("glare");
  if (Math.min(origW, origH) < LIMITS.minSide) issues.push("small");
  return issues;
}

/** Browser: decode, downscale, convert to grey, assess. Returns [] if the image cannot be decoded. */
export async function assessPhoto(file: File): Promise<PhotoIssue[]> {
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, LIMITS.side / Math.max(bmp.width, bmp.height));
    const w = Math.max(3, Math.round(bmp.width * scale));
    const h = Math.max(3, Math.round(bmp.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return [];
    ctx.drawImage(bmp, 0, 0, w, h);
    const { data } = ctx.getImageData(0, 0, w, h);
    const grey = new Uint8ClampedArray(w * h);
    for (let i = 0, j = 0; i < data.length; i += 4, j++) grey[j] = (data[i] * 299 + data[i + 1] * 587 + data[i + 2] * 114) / 1000;
    const issues = assessPixels(grey, w, h, bmp.width, bmp.height);
    bmp.close();
    return issues;
  } catch {
    return [];
  }
}
