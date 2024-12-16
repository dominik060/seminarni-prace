import threading
import numpy as np
import serial
from matplotlib import pyplot as plt
from matplotlib.widgets import Button

# Serial port configuration
PORT = "COM4"
BAUD = 9600
ser = serial.Serial(PORT, baudrate=BAUD, bytesize=8, parity="N", stopbits=1, timeout=2)

# Plot configurations
r_max = 250
angles = np.arange(0, 361, 1)
theta = angles * (2 * np.pi / 360.0)
dists_raw = np.zeros(len(angles))
dists_processed = np.zeros(len(angles))

# Setup plot
fig, (ax1, ax2) = plt.subplots(1, 2, subplot_kw={"polar": True}, facecolor="k")
fig.canvas.manager.set_window_title("Radar System")
fig.set_size_inches(12, 6)
fig.subplots_adjust(bottom=0.25)

# Configure Axes 1 (Raw Data)
ax1.set_facecolor("#051F20")
ax1.set_ylim([0, r_max])
ax1.set_theta_offset(np.pi / 2)
ax1.set_theta_direction(-1)
ax1.set_title("Raw Data", color="w", fontsize=14)

(pols_raw,) = ax1.plot(theta, dists_raw, "ro", markersize=3.0, alpha=0.9)
grid_lines_raw = ax1.plot([], [], color="w", linewidth=1.0, alpha=0.5)

# Configure Axes 2 (Processed Data)
ax2.set_facecolor("#051F20")
ax2.set_ylim([0, r_max])
ax2.set_theta_offset(np.pi / 2)
ax2.set_theta_direction(-1)
ax2.set_title("Processed Data", color="w", fontsize=14)

(pols_processed_points,) = ax2.plot(
    theta, dists_processed, "go", markersize=3.0, alpha=0.9
)
(pols_processed_lines,) = ax2.plot([], [], color="lime", linewidth=2, linestyle="-")

grid_lines_processed = ax2.plot([], [], color="w", linewidth=1.0, alpha=0.5)

# Create radial grids
for ax in [ax1, ax2]:
    ax.grid(color="w", alpha=0.4)
    ax.set_rticks(np.linspace(0, r_max, 5))
    ax.set_yticklabels(
        [f"{int(r)} cm" if r != 0 else "" for r in np.linspace(0, r_max, 5)], color="w"
    )
    ax.set_thetagrids(
        np.linspace(0, 360, 12),
        labels=[
            f"{int(angle)}°" if angle != 360 else ""
            for angle in np.linspace(0, 360, 12)
        ],
        color="w",
    )

# UI elements
# Last measurement text
last_value_text = fig.text(
    0.5,
    0.05,
    "Last Angle: 0°, Last Distance: 0 cm",
    ha="center",
    color="w",
    fontsize=12,
)

# Running status text
running_text = fig.text(
    0.25, 0.125, "Running: False", ha="left", fontsize=12, color="w"
)
toggle_running = False

# Running toggle button
toggle_ax = fig.add_axes([0.4, 0.1, 0.2, 0.075])
toggle_button = Button(toggle_ax, "Toggle", color="blue", hovercolor="darkblue")

# Clear data button
clear_ax = fig.add_axes([0.65, 0.1, 0.2, 0.075])
clear_button = Button(clear_ax, "Clear Data", color="red", hovercolor="darkred")


# Functions
# Toggle running function
def toggle_radar(event):
    global toggle_running
    toggle_running = not toggle_running
    ser.write(b"start" if toggle_running else b"stop")
    running_text.set_text(f"Running: {toggle_running}")
    fig.canvas.draw_idle()


toggle_button.on_clicked(toggle_radar)


# Clear data function
def clear_data(event):
    dists_raw.fill(0)
    dists_processed.fill(0)
    pols_raw.set_data(theta, dists_raw)
    pols_processed_points.set_data(theta, dists_processed)
    pols_processed_lines.set_data([], [])
    last_value_text.set_text("Last Angle: 0°, Last Distance: 0 cm")
    fig.canvas.draw_idle()


clear_button.on_clicked(clear_data)


# Data processing functions
def smooth_data(data):
    smoothed_data = data.copy()

    smoothed_data[smoothed_data > r_max] = r_max + 5
    smoothed_data[smoothed_data < 0] = 0

    return smoothed_data


# Interpolate distances
def interpolate_distances(distances):
    valid_indices = np.where(distances > 0)[0]
    if len(valid_indices) == 0:
        return distances

    interpolated = np.interp(
        np.arange(len(distances)),
        valid_indices,
        distances[valid_indices],
        left=0,
        right=0,
    )
    return interpolated


# Update plot function
def update_plot():
    global toggle_running
    while True:
        if toggle_running:
            try:
                data = ser.readline().decode().strip()
                vals = list(map(float, data.split(",")))
                if len(vals) < 3:
                    continue
                angle, dist, _ = vals
                angle = round(angle)

                dists_raw[angle] = dist
                dists_processed[:] = smooth_data(dists_raw)

                # Update UI Texts
                last_value_text.set_text(
                    f"Last Angle: {angle}°, Last Distance: {int(dist)} cm"
                )

                # Update Plots
                pols_raw.set_data(theta, dists_raw)

                pols_processed_points.set_data(theta, dists_processed)

                dists_interpolated_processed = interpolate_distances(dists_processed)
                pols_processed_lines.set_data(theta, dists_interpolated_processed)

                fig.canvas.draw_idle()
                fig.canvas.flush_events()

            except Exception as e:
                print(f"Error: {e}")


# Start the thread
thread = threading.Thread(target=update_plot)
thread.daemon = True
thread.start()

plt.show()
