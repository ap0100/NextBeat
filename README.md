# NextBeat: AI-Powered ECG Reconstruction from PPG <img width="27" height="27" alt="logo" src="design/images/logo.png" />

A portable, AI-driven medical prototype that reads optical blood volume (PPG) from a fingertip and uses a custom neural network to reconstruct and display a synthetic ECG waveform in real-time.

Here's the current look of the project, with one image of it working:
<div>
  <img src="design/images/nextbeat_box_front_side.jpg" width="200"/>
  <img src="design/images/nextbeat_box_back_side.jpg" width="200"/>
  <img src="design/images/nextbeat_box_fron_side_working" width="200"/>
</div>
*(Note: The AI successfully predicts the timing of the QRS spikes, though the morphology is slightly stylized due to the mechanical nature of PPG signals vs. electrical ECG signals).*

---

## 🧠 How It Works
The MAX30102 sensor shines red and infrared light into your finger to measure blood volume changes (PPG). The heart pumps blood mechanically, but an ECG measures the *electrical* signal that causes the pump.

We trained a **1D U-Net Convolutional Encoder-Decoder** in TensorFlow to translate the mechanical PPG wave into an electrical ECG wave.
- **Inputs:** 10 seconds of raw PPG data (1000 samples) + Patient Demographics (Age, Gender, Height, Weight, SBP, DBP).
- **Output:** 10 seconds of reconstructed ECG waveform.
- **Dataset:** Trained on 30 patients from the public Mendeley ECG+PPG dataset.
- **Deployment:** Exported to `TensorFlow Lite` to run smoothly on the Raspberry Pi 4.

---

## 📊 The Dataset
To train the AI, we used the public **Mendeley ECG+PPG Dataset** (148 subjects, simultaneous 1-lead ECG and dual-wavelength PPG).

Because training on all 148 patients (444 files) would instantly crash Google Colab's RAM, we strategically used a subset:
*   **Training Subset:** 30 patients (3 different states each = 90 CSV files).
*   **Preprocessing:** The original data was recorded at 250 Hz. We applied `scipy.signal.resample` to downsample it to **100 Hz** (so a 10-second window = 1000 samples). This reduces the Pi's CPU load while keeping the sharp ECG spikes intact.
*   **Windowing:** The signals were sliced into 10-second windows with a 50% overlap, resulting in exactly **3,060 training windows**.
*   **Demographics:** We merged `information.csv` with the signal data. The model is conditioned on Age, Gender, Height, Weight, SBP, and DBP to correct for physiological biases.
*   **Normalization:** Every window was normalized between `[0, 1]` so the network learns the shape, not the raw voltage.

---

## 🧰 Components
**Brains**
- `Raspberry Pi 4 Model B` (4GB RAM)
- `MAX30102` Pulse Oximeter and Heart-Rate Sensor (I2C)
- `GC9A01` 1.28" 240x240 Circular TFT Display (SPI)

**Power & Cooling**
- `Mini 5V DC Active Cooler` (because the Pi 4 turns into a space heater during ML inference)
- Powered from the laptop (5V/3A)

**Design**
- Custom hand-painted cardboard enclosure

**Pins Used:**
| Component | Pins |
|---|---|
| MAX30102 (I2C) | SDA (GPIO 3), SCL (GPIO 5), VIN (GPIO 17), GND (GPIO 9) |
| GC9A01 (SPI) | SDA (GPIO 19), SCL (GPIO 23), CS (GPIO 24), DC (GPIO 22), RST (GPIO 13), GND (GPIO 6), VCC (GPIO 1) |

---

## 📊 Analysis: How Accurate is the AI?
We achieved a **Validation Mean Absolute Error (MAE) of 8.8%** during training, but accuracy must be split into two categories:

*   **Timing (Rhythm) Accuracy:** High (~95%). The AI is incredibly accurate at predicting *when* your heart is beating. It places the green spikes at the exact millisecond your pulse hits.
*   **Morphology (Shape) Accuracy:** Low (Approximation). A real ECG has P, QRS, and T waves. Because PPG measures mechanical blood volume and not electrical ions, the AI cannot know what the P and T waves look like. It outputs a stylized, idealized QRS spike.
*   **Visual Sharpening:** We applied a mathematical filter (`norm_val ** 2.5`) to the display code to make the AI's smooth output look more like sharp, clinical spikes.

**Conclusion:** The device is excellent for tracking heart rhythm and timing from light, but it is a prototype approximation, not a replacement for a clinical ECG.

---

## 💻 Setup & Software Stack
**Raspberry Pi OS (64-bit) & Python 3.11:**
1. **Virtual Environment:** We use a Python 3.11 virtual environment (`myenv`). Do **not** use the system Python 3.13, or half the ML libraries won't compile.
2. **Framebuffer Display:** The GC9A01 is driven directly via `/dev/fb0` using the `Pillow` (PIL) library, converting images to RGB565 format on the fly.
3. **Dependencies:** `numpy`, `scipy`, `Pillow`, `smbus2`, `tflite-runtime`.
4. **Signal Processing:** Custom peak-detection algorithm (`my_hrcalc.py`) to calculate real-time Heart Rate (HR) and SpO2.

**To run the project, once you connect the Pi to your laptop:**
```bash
cd ~/hr_monitor
source ~/myenv/bin/activate
python3 main.py

---

## 🛠️ Quick Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'tflite_runtime'` | You are not in the virtual environment. Run `source ~/myenv/bin/activate`. |
| Dimension mismatch: Got 3 but expected 2 | The TFLite model swapped the PPG and Demographic inputs. Swap `PPG_INDEX` and `DEMO_INDEX`. |
| A module compiled using NumPy 1.x cannot be run in NumPy 2.4.6 | Run `pip install "numpy<2"` to downgrade. |
| The ECG wave looks like a square comb | Apply the sharpening math (`** 2.5`) in `write_display()` and decrease the line width to `1`. |
| Screen is completely black / Permission Denied | Run `sudo chmod 777 /dev/fb0` or ensure your user is in the `video` group. |
| The Pi overheats and freezes | Plug in the active cooler. ML inference on a Pi 4 runs hot. |

---

## 👨‍💻 The Creators
[ap0100](https://github.com/ap0100), [lukspuks](https://github.com/lukspuks), [sarakochovska](https://github.com/sarakochovska)
