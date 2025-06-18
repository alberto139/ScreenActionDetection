# ScreenActionDetection

A Python tool for capturing screen activity as a sequence of frames, detecting visual changes, and generating real-time "change heatmaps." This repository provides the foundational vision component for an AI agent that can perceive and understand on-screen events.

The primary goal of this project is to create a robust visual input pipeline that can be fed into advanced multimodal or video understanding models. By capturing and pre-processing screen activity, this tool can empower an AI to determine what actions occurred on a desktop or in a browser.

---

## Features

- **Multi-Target Screen Capture:**
  - Capture the **entire desktop** across all monitors.
  - Capture a **specific application window** (e.g., a web browser) by name.
  - Isolate and capture a **single monitor** (e.g., only the leftmost one).
- **Reliable Cursor Capture:** Uses a robust method (`scrot`) to ensure the mouse pointer is always included in captures, which is critical for understanding user intent.
- **Live Change Detection:**
  - Runs in a real-time loop to continuously monitor the screen.
  - Generates a "change heatmap" that visualizes all motion and UI changes over the last few frames.
- **Visual Feedback Dashboard:** Displays a live OpenCV window showing the screen feed and the change heatmap side-by-side for immediate analysis.
- **Video Recording:** Saves the combined dashboard (live view + change heatmap) as an `.mp4` video file for later review or for batch processing with a vision model.
- **Linux Focused:** Optimized for Linux environments using a reliable stack of command-line tools (`scrot`, `xdotool`) and Python libraries.

---

## How It Works

The script operates using a **"Capture and Crop"** strategy to ensure reliability and compatibility across different Linux desktop environments, which can be inconsistent.

1.  **Capture:** It calls the `scrot` command-line tool to take a high-fidelity screenshot of the entire desktop. This is a very basic and reliable command.
2.  **Detect & Crop:** The `mss` library is used to detect the precise pixel coordinates of the desired target (e.g., the leftmost monitor). Python's `Pillow` library then crops the full screenshot down to this exact region.
3.  **Analyze & Display:** In the live version, a history of recent frames is maintained. The script compares the newest frame to the previous one to detect differences. These differences are aggregated and displayed as a heatmap in the live dashboard using `OpenCV`.
4.  **Record:** The combined dashboard view is written frame-by-frame to an MP4 video file using `OpenCV's VideoWriter`.

---

## Getting Started

### Prerequisites

This script is designed for a Linux desktop environment (like Ubuntu, Pop!_OS, etc.) with the X11 display server.

1.  **System Tools:** You must have `scrot` and `xdotool` installed.
    ```bash
    sudo apt-get update
    sudo apt-get install scrot xdotool
    ```

2.  **Python Libraries:** You will need `Pillow`, `mss`, `opencv-python`, and `numpy`.
    ```bash
    pip install Pillow mss opencv-python numpy
    ```

### Usage

1.  Clone the repository:
    ```bash
    git clone [https://github.com/your-username/ScreenActionDetection.git](https://github.com/your-username/ScreenActionDetection.git)
    cd ScreenActionDetection
    ```

2.  Open the main Python script (e.g., `live_monitor.py`) in an editor.

3.  At the top of the script, choose your desired `CAPTURE_TARGET`:
    ```python
    # Choose 'left_monitor', 'desktop', or 'browser'
    CAPTURE_TARGET = 'left_monitor'
    ```

4.  Run the script from your terminal:
    ```bash
    python3 live_monitor.py
    ```

5.  A window titled "Live Dashboard" will appear. To stop the script and save the video, make sure the window is active and press the **'q'** key.

---

## Roadmap & Future Goals

This tool provides the crucial "seeing" part of a larger AI agent. The next steps for this project are:

-   [ ] **Integrate a Vision Model:** Feed the recorded video or live frames into a video understanding model (like a Video-LLM or LMM).
-   [ ] **Action Extraction:** Process the model's output to extract a structured list of actions (e.g., `{ "action": "click", "target": "button_submit", "timestamp": "..." }`).
-   [ ] **Agent Logic:** Develop a control loop where the AI's understanding of past actions informs its next decision.
-   [ ] **Cross-Platform Support:** Investigate and implement reliable capture methods for Windows and macOS.

---

## Contributing

Contributions, issues, and feature requests are welcome! Please feel free to check the [issues page](https://github.com/your-username/ScreenActionDetection/issues).