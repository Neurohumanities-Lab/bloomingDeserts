import asyncio
import sys
from bleak import BleakClient
from datetime import datetime
from pathlib import Path
import pandas as pd
import keyboard
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# BLE Configuration
ESP32_MAC = "08:A6:F7:6B:37:C2"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# ADC/GSR Settings
ADC_RESOLUTION = 4095
VCC = 3.3
R_FIXED = 10000

# Impulse Detection Thresholds
THRESHOLD_MIN = 0.1
THRESHOLD_MAX = 0.5

# Global Variables
csv_path = None
saving = False
gsr_window = []
key_s_pressed = False
key_q_pressed = False

# Plotting Buffers
window_size = 100
gsr_values = deque(maxlen=window_size)

# Windows Event Loop Policy
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Conversion Function
def adc_to_microsiemens(adc_value, vcc=VCC, adc_resolution=ADC_RESOLUTION, r_fixed=R_FIXED):
    v_out = adc_value / adc_resolution * vcc
    try:
        r_skin = r_fixed * (v_out / (vcc - v_out))
        microsiemens = (1 / r_skin) * 1e6
    except ZeroDivisionError:
        microsiemens = 0
    return microsiemens

# CSV Functions
def create_csv_file():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"GSR_data_{timestamp}.csv"
    path = Path.cwd() / file_name
    df = pd.DataFrame(columns=["timestamp", "datetime", "ADC", "microsiemens", "impulse"])
    df.to_csv(path, index=False)
    print(f"📝 Saving started: {path}")
    return path

def save_reading(path, ts_unix, ts_human, adc, microsiemens, impulse):
    df = pd.DataFrame([[ts_unix, ts_human, adc, microsiemens, impulse]],
                      columns=["timestamp", "datetime", "ADC", "microsiemens", "impulse"])
    df.to_csv(path, mode='a', header=False, index=False)

# BLE and Acquisition Loop
async def ble_loop():
    global saving, csv_path, gsr_window, key_s_pressed, key_q_pressed

    async with BleakClient(ESP32_MAC) as client:
        print(f"✅ Connected to ESP32_GSR ({ESP32_MAC})")
        print("Press 's' to start saving and 'q' to stop.")

        while True:
            try:
                data = await client.read_gatt_char(CHARACTERISTIC_UUID)
                try:
                    adc = int(data.decode().strip())
                except (ValueError, UnicodeDecodeError):
                    continue  # Ignore corrupted data

                gsr_uS = adc_to_microsiemens(adc)

                # Timestamps
                ts_unix = datetime.now().timestamp()
                ts_human = datetime.now().isoformat(sep=' ', timespec='milliseconds')

                # Moving Average & Impulse Detection
                gsr_window.append(gsr_uS)
                if len(gsr_window) > 10:
                    gsr_window.pop(0)
                moving_avg = sum(gsr_window) / len(gsr_window)
                delta = gsr_uS - moving_avg
                impulse = THRESHOLD_MIN < delta < THRESHOLD_MAX

                # Update Plot Buffer
                gsr_values.append(gsr_uS)

                # Console Output
                print(f"[{ts_unix:.3f}] {ts_human} → ADC: {adc} → {gsr_uS:.2f} µS | Δ={delta:.2f} → Impulse: {impulse}", end="\r")

                # Keyboard Control (Debounced)
                if keyboard.is_pressed('s'):
                    if not key_s_pressed:
                        csv_path = create_csv_file()
                        saving = True
                        key_s_pressed = True
                else:
                    key_s_pressed = False

                if keyboard.is_pressed('q'):
                    if not key_q_pressed:
                        print("\n🛑 Saving stopped.")
                        saving = False
                        key_q_pressed = True
                else:
                    key_q_pressed = False

                if saving:
                    save_reading(csv_path, ts_unix, ts_human, adc, gsr_uS, impulse)

            except Exception as e:
                print(f"\n⚠️ Error: {e}")

            await asyncio.sleep(0.25)

# Plotting Function
def start_plot():
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    ax.set_ylim(0, 20)
    ax.set_xlim(0, window_size)
    ax.set_xlabel('Samples')
    ax.set_ylabel('GSR (µS)')
    ax.set_title('Real-time GSR Signal')

    def update_plot(frame):
        line.set_data(range(len(gsr_values)), gsr_values)
        return line,

    ani = animation.FuncAnimation(fig, update_plot, interval=250, blit=True)
    plt.show()

# Main Execution
async def main():
    task_ble = asyncio.create_task(ble_loop())
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, start_plot)
    await task_ble

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔚 Program terminated.")
