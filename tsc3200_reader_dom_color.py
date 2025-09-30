#!/usr/bin/env python3
import time
from periphery import GPIO

# Luckfox Pico Mini A pinout assignments:
S0_GPIO = 43   # GPIO1_B3 (pin 5)
S1_GPIO = 50  # GPIO1_C2 (pin 8)
S2_GPIO = 51  # GPIO1_C3 (pin 9)
S3_GPIO = 52  # GPIO1_C4 (pin 10)
OUT_GPIO = 57 # GPIO1_D1 (pin 13)

def set_scaling(s0, s1, scaling):
    # Podesava izlaznu frekvenciju senzora (2%, 20%, 100%)
    if scaling == 2:
        s0.write(False); s1.write(True)
    elif scaling == 20:
        s0.write(True);  s1.write(False)
    elif scaling == 100:
        s0.write(True);  s1.write(True)
    else:
        raise ValueError("SCALING must be 2, 20, or 100")

def set_filter(s2, s3, mode):
    # Aktivira filter za crvenu, zelenu, plavu ili clear (bez filtera)
    if mode == "red":
        s2.write(False); s3.write(False)
    elif mode == "blue":
        s2.write(False); s3.write(True)
    elif mode == "clear":
        s2.write(True);  s3.write(False)
    elif mode == "green":
        s2.write(True);  s3.write(True)
    else:
        raise ValueError("Unknown filter mode")

def measure_frequency(in_gpio, edge_count=50):
    # Merenje frekvencije na izlazu senzora
    in_gpio.edge = "rising"
    try:
        while in_gpio.poll(0):
            in_gpio.read()
    except Exception:
        pass
    if not in_gpio.poll(0.5):
        return 0.0
    in_gpio.read()
    t_start = time.perf_counter()
    edges = 0
    while edges < edge_count:
        if not in_gpio.poll(0.2):
            break
        in_gpio.read()
        edges += 1
    elapsed = time.perf_counter() - t_start
    if edges == 0 or elapsed <= 0:
        return 0.0
    return edges / elapsed

def detect_dominant_color(readings, threshold=0.15):
    # Detektuje dominantnu boju na osnovu očitanih frekvencija (ako je bar 15% veća od sledeće)
    sorted_colors = sorted(readings.items(), key=lambda x: x[1], reverse=True)
    top_color, top_freq = sorted_colors[0]
    second_color, second_freq = sorted_colors[1]
    if top_freq > 0 and (top_freq - second_freq) / top_freq > threshold:
        return top_color.upper()
    return "UNCERTAIN"

def main():
    # Inicijalizacija GPIO pinova
    s0 = GPIO(S0_GPIO, "out")
    s1 = GPIO(S1_GPIO, "out")
    s2 = GPIO(S2_GPIO, "out")
    s3 = GPIO(S3_GPIO, "out")
    out = GPIO(OUT_GPIO, "in")
    try:
        set_scaling(s0, s1, 20)  # 20% scaling za stabilnost
        while True:
            readings = {}
            for color in ("red", "green", "blue"):
                set_filter(s2, s3, color)
                time.sleep(0.02)
                hz = measure_frequency(out, edge_count=50)
                readings[color] = hz
            dom = detect_dominant_color(readings, threshold=0.15)
            print(f"Freqs (Hz): R={readings['red']:.0f} G={readings['green']:.0f} B={readings['blue']:.0f} => Dominant: {dom}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        # Zatvaranje GPIO pinova
        out.close()
        s3.close()
        s2.close()
        s1.close()
        s0.close()

if __name__ == "__main__":
    main()