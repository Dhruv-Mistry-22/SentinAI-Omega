import numpy as np
from PIL import Image

def analyze_frequency(img_pil):
    """
    Performs Fast Fourier Transform (FFT) on the image.
    Looks for high-frequency patterns typical in some AI generations.
    Returns: (FFT Image, AI Score)
    """
    # Convert to grayscale
    img_gray = img_pil.convert('L')
    f = np.fft.fft2(img_gray)
    fshift = np.fft.fftshift(f)
    
    # Calculate magnitude spectrum
    magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)
    
    # Normalize for visualization
    magnitude_spectrum_vis = np.asarray(magnitude_spectrum, dtype=np.float32)
    magnitude_spectrum_vis = (magnitude_spectrum_vis - np.min(magnitude_spectrum_vis)) / (np.max(magnitude_spectrum_vis) - np.min(magnitude_spectrum_vis))
    magnitude_spectrum_vis = (magnitude_spectrum_vis * 255).astype(np.uint8)
    fft_img = Image.fromarray(magnitude_spectrum_vis)
    
    # Calculate score based on high frequency energy
    # Real images typically decay smoothly. AI can have anomalous spikes.
    # We will do a basic heuristic check of the outer edges.
    h, w = magnitude_spectrum.shape
    center_h, center_w = h // 2, w // 2
    
    # Mask out the low frequencies (center)
    mask = np.ones((h, w))
    r = min(h, w) // 4
    y, x = np.ogrid[-center_h:h-center_h, -center_w:w-center_w]
    mask_area = x*x + y*y <= r*r
    mask[mask_area] = 0
    
    high_freq_energy = np.mean(magnitude_spectrum * mask)
    
    # Heuristic scoring
    if high_freq_energy > 150:  # Arbitrary threshold for demo
        score = 0.6
        note = "High frequency anomalies (AI lean)"
    elif high_freq_energy < 80:
        score = 0.4
        note = "Smooth frequency decay (Real lean)"
    else:
        score = 0.5
        note = "Standard frequency spectrum (Neutral)"
        
    return fft_img, score, note
