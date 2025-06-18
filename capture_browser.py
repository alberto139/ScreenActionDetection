import subprocess
import time
from PIL import Image, ImageChops
import os
import mss

# --- Helper function for BROWSER targeting ---
def find_and_focus_browser_window():
    """Uses xdotool to find a visible browser window and bring it to the front."""
    try:
        browser_pattern = "firefox|chrome|brave|chromium|edge"
        cmd_search = ['xdotool', 'search', '--onlyvisible', '--name', browser_pattern]
        search_result = subprocess.check_output(cmd_search, text=True).strip()
        if not search_result: return False
        window_id = search_result.split('\n')[0]
        subprocess.run(['xdotool', 'windowactivate', window_id], check=True)
        time.sleep(0.3)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

# --- Helper function for MONITOR targeting ---
def get_leftmost_monitor_region():
    """Uses mss to find the geometry of the leftmost monitor."""
    with mss.mss() as sct:
        if len(sct.monitors) <= 2:
            print("Only one monitor detected.")
            return None
        # Return the entire monitor dictionary, skipping the 'all-in-one' monitor 0
        return min(sct.monitors[1:], key=lambda m: m['left'])

def capture_sequence(target='desktop', num_images=10, duration_seconds=5, output_dir="captures"):
    """Captures a sequence using the 'Capture and Crop' method for maximum reliability."""
    try:
        subprocess.run(['which', 'scrot'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FATAL ERROR: `scrot` is not installed. Please run 'sudo apt-get install scrot'.")
        return None

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    captured_images = []
    interval = duration_seconds / num_images
    print(f"Starting {target.upper()} capture: {num_images} images over {duration_seconds} seconds...")

    for i in range(num_images):
        print(f"  Capturing image {i+1}/{num_images}...")
        final_filepath = os.path.join(output_dir, f"capture_{i:02d}.png")
        
        try:
            # This block uses the 'Capture and Crop' method and does NOT use --area
            if target == 'left_monitor':
                region = get_leftmost_monitor_region()
                if not region:
                    print("Could not get left monitor region. Capturing full desktop.")
                    subprocess.run(['scrot', '--pointer', '--file', final_filepath], check=True)
                else:
                    # 1. Capture the ENTIRE screen to a temporary file
                    temp_filepath = os.path.join(output_dir, "temp_full_capture.png")
                    subprocess.run(['scrot', '--pointer', '--overwrite', '--file', temp_filepath], check=True)
                    
                    # 2. Open the full screenshot with Pillow
                    img = Image.open(temp_filepath)
                    
                    # 3. Define the crop box from the region dictionary
                    crop_box = (
                        region['left'], 
                        region['top'], 
                        region['left'] + region['width'], 
                        region['top'] + region['height']
                    )
                    
                    # 4. Crop the image and save it to the final destination
                    cropped_img = img.crop(crop_box)
                    cropped_img.save(final_filepath)
                    os.remove(temp_filepath)

            elif target == 'browser':
                if not find_and_focus_browser_window():
                    print("Could not find browser window. Aborting.")
                    return None
                subprocess.run(['scrot', '--focused', '--pointer', '--file', final_filepath], check=True)

            else: # 'desktop'
                subprocess.run(['scrot', '--pointer', '--file', final_filepath], check=True)

            captured_images.append(final_filepath)

        except Exception as e:
            print(f"Error during capture: {e}")
            return None
        
        time.sleep(interval)
            
    print("Capture sequence finished.")
    return captured_images

def compare_images(image_path1, image_path2, output_dir="diffs"):
    """Compares two images and returns a difference score and a difference image."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    img1 = Image.open(image_path1).convert("RGB")
    img2 = Image.open(image_path2).convert("RGB")
    diff_img = ImageChops.difference(img1, img2)
    bbox = diff_img.getbbox()
    
    if bbox is None:
        difference_score = 0
    else:
        (x1, y1, x2, y2) = bbox
        difference_score = (x2 - x1) * (y2 - y1)

    base1 = os.path.basename(image_path1).split('.')[0]
    base2 = os.path.basename(image_path2).split('.')[0]
    diff_filepath = os.path.join(output_dir, f"diff_{base1}_vs_{base2}.png")
    diff_img.save(diff_filepath)
    
    return difference_score, diff_filepath

# --- Main execution block ---
if __name__ == "__main__":
    
    # --- CHOOSE YOUR CAPTURE TARGET ---
    # Target: The leftmost monitor
    image_files = capture_sequence(target='left_monitor', num_images=10, duration_seconds=10)
    
    # Target: The entire desktop (all monitors)
    # image_files = capture_sequence(target='desktop', num_images=10, duration_seconds=5)

    # Target: The active browser window
    # image_files = capture_sequence(target='browser', num_images=10, duration_seconds=5)
    
    # --- The rest of the script performs the comparison ---
    if image_files:
        print("\n--- Starting Pair-wise Comparison ---")
        
        individual_diff_paths = []
        total_difference_score = 0

        for i in range(len(image_files) - 1):
            img1_path = image_files[i]
            img2_path = image_files[i+1]
            
            score, diff_path = compare_images(img1_path, img2_path)
            individual_diff_paths.append(diff_path)
            total_difference_score += score
            
            print(f"  - Comparing {os.path.basename(img1_path)} and {os.path.basename(img2_path)}: Score={score}")
        
        print("\n--- Creating Overall Sequence Comparison ---")

        if not individual_diff_paths:
            print("No differences to combine.")
        else:
            composite_image = Image.open(individual_diff_paths[0])
            for path in individual_diff_paths[1:]:
                next_diff = Image.open(path)
                composite_image = ImageChops.lighter(composite_image, next_diff)
            
            composite_path = os.path.join("diffs", "total_sequence_diff.png")
            composite_image.save(composite_path)
            
            print(f"Total Difference Score for the sequence: {total_difference_score}")
            print(f"Composite 'heatmap' of all changes saved to: {composite_path}")

        print("\nComparison finished.")