import cv2
import numpy as np
import time
import os
import subprocess
import mss
from PIL import Image
from collections import deque

# --- Configuration ---
HISTORY_SIZE = 10
CAPTURE_TARGET = 'left_monitor'
OUTPUT_FILENAME = 'screen_recording_dashboard.mp4' # Changed filename for clarity
FPS = 10.0

# --- Helper function to get monitor geometry ---
def get_leftmost_monitor_region():
    """Uses mss to find the geometry of the leftmost monitor."""
    with mss.mss() as sct:
        if len(sct.monitors) <= 2:
            return sct.monitors[1] # Return primary if only one
        return min(sct.monitors[1:], key=lambda m: m['left'])

# --- The main screen capture function ---
def capture_screen(target='desktop', region=None):
    """Captures the screen and returns a NumPy array (OpenCV format)."""
    temp_filepath = "temp_live_capture.png"
    if target == 'left_monitor' and region:
        subprocess.run(['scrot', '--pointer', '--overwrite', '--file', temp_filepath], check=True)
        img = Image.open(temp_filepath)
        crop_box = (
            region['left'], 
            region['top'], 
            region['left'] + region['width'], 
            region['top'] + region['height']
        )
        cropped_img = img.crop(crop_box)
        os.remove(temp_filepath)
        return cv2.cvtColor(np.array(cropped_img), cv2.COLOR_RGB2BGR)
    else: # Fallback to full desktop capture
        subprocess.run(['scrot', '--pointer', '--overwrite', '--file', temp_filepath], check=True)
        img = cv2.imread(temp_filepath)
        os.remove(temp_filepath)
        return img

def main():
    frames_deque = deque(maxlen=HISTORY_SIZE)
    diffs_deque = deque(maxlen=HISTORY_SIZE - 1)

    capture_region = None
    if CAPTURE_TARGET == 'left_monitor':
        print("Detecting left monitor...")
        capture_region = get_leftmost_monitor_region()
        if capture_region:
            print(f"Targeting region: {capture_region}")
        else:
            print("Could not detect left monitor, will capture full desktop.")
            # Fallback dimensions if detection fails
            capture_region = {'width': 1920, 'height': 1080}
            
    # --- MODIFIED: Set Video Writer dimensions for the combined view ---
    frame_width = capture_region['width']
    frame_height = capture_region['height']
    
    # The output video will be twice as wide to hold both views
    output_width = frame_width * 2
    output_height = frame_height
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, (output_width, output_height))
    print(f"Recording COMBINED view to '{OUTPUT_FILENAME}' at {FPS} FPS.")
    # -------------------------------------------------------------------
    
    print("Starting live capture... Press 'q' in the OpenCV window to quit.")
    
    while True:
        try:
            live_view = capture_screen(target=CAPTURE_TARGET, region=capture_region)
            if live_view is None: continue
            
            # Ensure the captured frame matches the expected dimensions for concatenation
            live_view = cv2.resize(live_view, (frame_width, frame_height))

            frames_deque.append(live_view)

            if len(frames_deque) > 1:
                prev_frame = frames_deque[-2]
                diff = cv2.absdiff(prev_frame, live_view)
                gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                _, thresh_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
                diffs_deque.append(thresh_diff)

            if diffs_deque:
                composite_diff = np.zeros_like(diffs_deque[0], dtype=np.uint8)
                for diff_mask in diffs_deque:
                    composite_diff = cv2.bitwise_or(composite_diff, diff_mask)
                diff_view = cv2.cvtColor(composite_diff, cv2.COLOR_GRAY2BGR)
            else:
                diff_view = np.zeros_like(live_view)
            
            # --- MODIFIED: Re-create the dashboard view ---
            dashboard = cv2.hconcat([live_view, diff_view])
            
            # Add text labels to the dashboard
            cv2.putText(dashboard, 'Live View', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(dashboard, 'Change History (last 10 frames)', (frame_width + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # --- MODIFIED: Write the COMBINED dashboard to the video file ---
            video_writer.write(dashboard)
            
            # --- MODIFIED: Show the COMBINED dashboard in the window ---
            cv2.imshow('Live Dashboard (Recording...)', dashboard)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except KeyboardInterrupt:
            print("Interrupted by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(2)

    # --- Cleanup ---
    if video_writer:
        video_writer.release()
        print(f"Video saved successfully to '{OUTPUT_FILENAME}'")
    cv2.destroyAllWindows()
    print("Stream stopped.")

if __name__ == "__main__":
    main()