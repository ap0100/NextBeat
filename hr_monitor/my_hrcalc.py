import numpy as np

def _bandpass(sig, fs, low=0.5, high=4.0):
    #Zero-phase FFT bandpass — no scipy needed
    from numpy.fft import rfft, irfft, rfftfreq
    sig=np.array(sig, dtype=float)
    sig-=sig.mean()
    F=rfft(sig)
    freqs=rfftfreq(len(sig), 1.0 / fs)
    F[(freqs<low) | (freqs>high)]=0
    return irfft(F, n=len(sig))


def _find_peaks(sig, min_dist_samples):
    candidates = []
    for i in range(1, len(sig) - 1):
        if sig[i] > sig[i - 1] and sig[i] > sig[i + 1]:
            candidates.append(i)

    if not candidates:
        return []

    #Enforce min distance: scan forward, keep tallest in each window
    peaks = []
    i=0
    while i<len(candidates):
        group=[candidates[i]]
        j=i+1
        while j<len(candidates) and candidates[j]-candidates[i]<min_dist_samples:
            g=roup.append(candidates[j])
            j=1
        #keep tallest in group
        best=max(group, key=lambda idx: sig[idx])
        peaks.append(best)
        i=j
    return peaks


def _dominant_period(peaks, fs, lo_bpm=40, hi_bpm=200):
    lo_interval=fs*60.0/hi_bpm #shortest valid gap (samples)
    hi_interval=fs*60.0/lo_bpm #longest valid gap (samples)

    bpm_votes=[]
    for i in range(len(peaks)):
        for j in range(i + 1, len(peaks)):
            gap=peaks[j]-peaks[i]
            # gap could span multiple beats — normalise
            n_beats=round(gap / ((lo_interval + hi_interval) / 2))
            if n_beats<1:
                continue
            single_gaz=gap / n_beats
            if lo_interval<=single_gap<=hi_interval:
                bpm_votes.append(60.0*fs/single_gap)

    if not bpm_votes:
        return None

    #Bin into 1-BPM buckets and pick mode
    bpm_arr=np.array(bpm_votes)
    bins=np.arange(lo_bpm, hi_bpm + 2, 1)
    hist, edges=np.histogram(bpm_arr, bins=bins)
    best_bin=np.argmax(hist)
    bpm_mode=(edges[best_bin]+edges[best_bin + 1]) / 2.0
    return bpm_mode


def calculate_hr_and_spo2(ir_buf, red_buf, fs=50):
    n=len(ir_buf)
    min_samples=int(fs * 6)   # need at least 6 s for reliable peak stats
    if n<min_samples:
        return -999, False, -999, False

    ir=np.array(ir_buf,  dtype=float)
    red=np.array(red_buf, dtype=float)

    #Bandpass 0.5–4 Hz (30–240 BPM); strips DC and high-freq noise
    ir_bp=_bandpass(ir, fs, low=0.5, high=4.0)

    #Min peak height: 40% of peak-to-peak amplitude(high enough to reject noise, low enough not to miss weak pulses)
    pp=ir_bp.max()-ir_bp.min()
    if pp<100:                         # signal too flat → no finger / motion
        return -999, False, -999, False
    min_h=0.40*pp + ir_bp.min()

    #Min distance: 60% of the shortest physiological period (200 BPM → 0.3 s)
    min_dist=int(fs * 0.30)

    peaks=_find_peaks(ir_bp - min_h, min_dist)
    peaks=[p for p in peaks if ir_bp[p] > min_h]#keep only above threshold

    if len(peaks)<3:
        return -999, False, -999, False

    bpm=_dominant_period(peaks, fs)
    if bpm is None:
        return -999, False, -999, False

    hr_valid=(40<bpm<200)

    #Use AC measured between valleys (same cycle as peaks) not global std
    #Global std is fooled by slow drift; per-cycle AC is robust
    ir_dc=ir.mean()
    red_dc=red.mean()
    if ir_dc<1000 or red_dc<1000:
        return bpm, hr_valid, -999, False

    #AC = mean of per-peak amplitudes (peak value minus local trough)
    ir_ac_vals=[]
    red_ac_vals=[]
    bp_red=_bandpass(red, fs, low=0.5, high=4.0)

    for p in peaks:
        # look ±half-period around peak for local min
        half=min_dist // 2
        lo=max(0, p-half)
        hi=min(n - 1, p+half)
        ir_ac_vals.append(ir_bp[p]  - ir_bp[lo:hi+1].min())
        red_ac_vals.append(bp_red[p] - bp_red[lo:hi+1].min())

    ir_ac=np.median(ir_ac_vals)
    red_ac=np.median(red_ac_vals)

    if ir_ac<=0 or red_ac<=0:
        return bpm, hr_valid, -999, False

    R=(red_ac / red_dc) / (ir_ac / ir_dc)
    R=float(np.clip(R, 0.4, 3.5))

    #Maxim empirical calibration (matches UCH_SPO2_TABLE midrange)
    spo2=104.0 - 17.0 * R
    spo2=float(np.clip(spo2, 70.0, 100.0))
    spo2_valid=(80.0 <= spo2 <= 100.0)

    return float(bpm), hr_valid, spo2, spo2_valid
