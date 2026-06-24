import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import os
import threading
import queue
from recognition_system import recognize_part

# =====================================
# WINDOW CONFIGURATION
# =====================================
root = tk.Tk()
root.title("HCA Spare Part Recognition System")
root.geometry("1200x700")
root.resizable(False, False)

# Thread-safe queue for UI updates from worker threads
gui_queue = queue.Queue()

def process_gui_queue():
    """Polls the queue and processes callbacks on the main GUI thread."""
    try:
        while True:
            callback = gui_queue.get_nowait()
            callback()
    except queue.Empty:
        pass
    root.after(100, process_gui_queue)

# =====================================
# NON-BLOCKING BACKGROUND TRANSITIONS
# =====================================
backgrounds = [
    "assets/bg1.jpg",
    "assets/bg2.png",
    "assets/bg3.png"
]
bg_images = []

for file in backgrounds:
    try:
        if os.path.exists(file):
            img = Image.open(file)
            img = img.resize((1200, 700))
            bg_images.append(img)
        else:
            print(f"Background image not found: {file}")
    except Exception as e:
        print(f"Error loading background {file}: {e}")

# Fallback in case no background images are loaded
if not bg_images:
    for color in ["#111827", "#1F2937", "#374151"]:
        bg_images.append(Image.new("RGB", (1200, 700), color))

bg_label = tk.Label(root)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

current_bg = 0
bg_photo = ImageTk.PhotoImage(bg_images[0], master=root)
bg_label.config(image=bg_photo)

def fade_transition(alpha=0, current_idx=0):
    """Performs a smooth, non-blocking fade transition between backgrounds."""
    global bg_photo, current_bg
    next_idx = (current_idx + 1) % len(bg_images)
    
    try:
        blended = Image.blend(
            bg_images[current_idx],
            bg_images[next_idx],
            alpha / 100.0
        )
        bg_photo = ImageTk.PhotoImage(blended, master=root)
        bg_label.config(image=bg_photo)
    except Exception as e:
        print(f"Error during fade transition: {e}")
        
    if alpha < 100:
        root.after(25, lambda: fade_transition(alpha + 5, current_idx))
    else:
        current_bg = next_idx
        root.after(4000, lambda: fade_transition(0, next_idx))

# Start background transition loop after 2 seconds
root.after(2000, lambda: fade_transition(0, 0))

# =====================================
# MODERN THEME STYLES
# =====================================
style = ttk.Style()
style.theme_use('default')
style.configure(
    "Sleek.Horizontal.TProgressbar",
    troughcolor='#111827',
    background='#10B981',
    thickness=20,
    borderwidth=0
)

# =====================================
# HEADER
# =====================================
header_frame = tk.Frame(root, bg="#111827", bd=0, highlightthickness=0)
header_frame.place(x=0, y=0, width=1200, height=110)

# Logo image display with graceful fallback
logo_img = None
logo_path = "assets/logo.png"
if os.path.exists(logo_path):
    try:
        logo = Image.open(logo_path)
        logo.thumbnail((80, 80))
        logo_img = ImageTk.PhotoImage(logo, master=root)
        logo_label = tk.Label(header_frame, image=logo_img, bg="#111827", bd=0)
        logo_label.place(x=20, y=15)
    except Exception as e:
        print(f"Error loading logo: {e}")
        logo_img = None

if logo_img is None:
    logo_label = tk.Label(
        header_frame,
        text="HCA",
        font=("Segoe UI", 24, "bold"),
        fg="#10B981",
        bg="#111827"
    )
    logo_label.place(x=25, y=30)

# Title & Subtitle labels
title = tk.Label(
    header_frame,
    text="SPARE PART RECOGNITION SYSTEM",
    font=("Segoe UI", 22, "bold"),
    fg="#F3F4F6",
    bg="#111827"
)
title.place(x=120, y=20)

subtitle = tk.Label(
    header_frame,
    text="Hari Chand Anand & Co. | Fast & Accurate Computer Vision Engine",
    font=("Segoe UI", 11, "italic"),
    fg="#9CA3AF",
    bg="#111827"
)
subtitle.place(x=120, y=65)

# Status Badge
status_label = tk.Label(
    header_frame,
    text="READY",
    font=("Segoe UI", 11, "bold"),
    bg="#10B981",
    fg="white",
    padx=15,
    pady=6
)
status_label.place(x=1020, y=35)

# =====================================
# MAIN PANELS
# =====================================

# Left Panel: Preview image
preview_frame = tk.LabelFrame(
    root,
    text=" Preview Image ",
    font=("Segoe UI", 12, "bold"),
    bg="#1F2937",
    fg="#F3F4F6",
    bd=1,
    relief="solid",
    highlightthickness=0
)
preview_frame.place(x=50, y=140, width=520, height=420)

image_label = tk.Label(
    preview_frame,
    text="No Image Selected\n\nUse buttons below to browse or capture a photo",
    font=("Segoe UI", 11, "italic"),
    bg="#111827",
    fg="#9CA3AF",
    bd=0,
    justify="center"
)
image_label.place(x=15, y=15, width=488, height=360)

# Right Panel: Results
result_frame = tk.LabelFrame(
    root,
    text=" Recognition Results ",
    font=("Segoe UI", 12, "bold"),
    bg="#1F2937",
    fg="#F3F4F6",
    bd=1,
    relief="solid",
    highlightthickness=0
)
result_frame.place(x=630, y=140, width=520, height=420)

result_text = tk.Text(
    result_frame,
    font=("Segoe UI", 11),
    bg="#111827",
    fg="#F9FAFB",
    bd=0,
    padx=12,
    pady=12,
    wrap="word"
)
result_text.place(x=15, y=15, width=488, height=270)

# Setup text styling tags
result_text.tag_configure("header", font=("Segoe UI", 13, "bold"), foreground="#10B981")
result_text.tag_configure("label", font=("Segoe UI", 11, "bold"), foreground="#9CA3AF")
result_text.tag_configure("value", font=("Segoe UI", 11), foreground="#F9FAFB")
result_text.tag_configure("accent", font=("Segoe UI", 11, "bold"), foreground="#FBBF24")
result_text.tag_configure("info", font=("Segoe UI", 11, "italic"), foreground="#9CA3AF")

result_text.insert(tk.END, "Upload or capture an image to begin matching...\n\nThe computer vision engine will extract features and query the local repository.", "info")
result_text.config(state="disabled")

# Confidence gauge and bar (No Overlapping!)
confidence_label = tk.Label(
    result_frame,
    text="Confidence: 0%",
    font=("Segoe UI", 11, "bold"),
    bg="#1F2937",
    fg="#F3F4F6"
)
confidence_label.place(x=15, y=305)

confidence_bar = ttk.Progressbar(
    result_frame,
    length=488,
    mode="determinate",
    style="Sleek.Horizontal.TProgressbar"
)
confidence_bar.place(x=15, y=340, width=488, height=20)

# Reference cache to prevent Image garbage collection
image_references = {}

# =====================================
# CORE FUNCTIONS
# =====================================

def update_preview_display(file_path):
    """Loads and updates the image label display in the preview card."""
    try:
        img = Image.open(file_path)
        img.thumbnail((480, 350))
        photo = ImageTk.PhotoImage(img, master=root)
        image_label.config(image=photo, text="")
        image_references["preview"] = photo
    except Exception as e:
        print(f"Error displaying preview: {e}")
        image_label.config(image="", text=f"Error displaying image:\n{e}")

def process_image(file_path):
    """Triggers recognition in a background thread and manages loading states."""
    # Show preview image immediately
    update_preview_display(file_path)
    
    # Set UI loading state
    status_label.config(text="PROCESSING...", bg="#D97706") # Amber/Orange
    confidence_label.config(text="Confidence: Analyzing...")
    confidence_bar.config(mode="indeterminate")
    confidence_bar.start(10)
    
    result_text.config(state="normal")
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, "Running computer vision algorithms...\nSearching dataset and computing ORB descriptors.", "info")
    result_text.config(state="disabled")
    
    # Disable controls to prevent user spamming/concurrency issues
    browse_btn.config(state="disabled")
    camera_btn.config(state="disabled")
    clear_btn.config(state="disabled")
    
    def worker():
        try:
            result = recognize_part(file_path)
            gui_queue.put(lambda: on_recognition_success(result))
        except Exception as e:
            gui_queue.put(lambda: on_recognition_error(str(e)))
            
    threading.Thread(target=worker, daemon=True).start()

def on_recognition_success(result):
    """Updates the GUI with the matching results. Called on the main GUI thread."""
    browse_btn.config(state="normal")
    camera_btn.config(state="normal")
    clear_btn.config(state="normal")
    
    confidence_bar.stop()
    confidence_bar.config(mode="determinate")
    
    confidence = result["confidence"]
    confidence_bar["value"] = confidence
    confidence_label.config(text=f"Confidence: {confidence}%")
    
    # Check if no part was identified
    if result["part"] == "Unknown":
        status_label.config(text="NOT FOUND", bg="#DC2626") # Red
        
        result_text.config(state="normal")
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "❌ Part info not found\n\n", "accent")
        
        fields = [
            ("Status", "Unidentified", "value"),
            ("Confidence", "0%", "value"),
            ("Match Count", f"{result['matches']} features (below threshold of 40)", "info")
        ]
        
        for name, value, tag in fields:
            result_text.insert(tk.END, f"{name.ljust(15)}: ", "label")
            result_text.insert(tk.END, f"{value}\n", tag)
            
        result_text.insert(tk.END, "\nSuggestions:\n", "header")
        result_text.insert(tk.END, "- Ensure the spare part is centered and clearly visible in frame\n", "info")
        result_text.insert(tk.END, "- Avoid extreme glare, shadows, or blurry camera focus\n", "info")
        result_text.insert(tk.END, "- Place the part against a contrasting background\n", "info")
        
        result_text.config(state="disabled")
        
        confidence_bar["value"] = 0
        confidence_label.config(text="Confidence: 0%")
        return

    status_label.config(text="PART IDENTIFIED", bg="#10B981") # Emerald Green
    
    result_text.config(state="normal")
    result_text.delete("1.0", tk.END)
    
    details = result["details"]
    if details:
        result_text.insert(tk.END, "✓ PART IDENTIFIED SUCCESSFULLY\n\n", "header")
        
        # Grid details display using custom tags
        fields = [
            ("Part Name", result['part'], "value"),
            ("Part Code", details.get('Part Code', 'N/A'), "accent"),
            ("Category", details.get('Category', 'N/A'), "value"),
            ("Machine Used", details.get('Machine Used In', 'N/A'), "value"),
            ("Rack Location", details.get('Rack Location', 'N/A'), "accent"),
            ("Bin Number", details.get('Bin Number', 'N/A'), "accent"),
            ("Commonly Sold", details.get('Commonly Sold', 'N/A'), "value"),
            ("Confidence", f"{confidence}%", "value"),
            ("Match Count", f"{result['matches']} features", "value")
        ]
        
        for name, value, tag in fields:
            result_text.insert(tk.END, f"{name.ljust(15)}: ", "label")
            result_text.insert(tk.END, f"{value}\n", tag)
    else:
        result_text.insert(tk.END, "⚠ PART RECOGNIZED (NO DATABASE RECORD)\n\n", "accent")
        
        fields = [
            ("Part Name", result['part'], "value"),
            ("Confidence", f"{confidence}%", "value"),
            ("Match Count", f"{result['matches']} features", "value")
        ]
        
        for name, value, tag in fields:
            result_text.insert(tk.END, f"{name.ljust(15)}: ", "label")
            result_text.insert(tk.END, f"{value}\n", tag)
            
        result_text.insert(tk.END, "\n(Notice: Details are missing in parts_info.csv metadata)", "info")
        
    result_text.config(state="disabled")

def on_recognition_error(err):
    """Updates the GUI on recognition failure. Called on the main GUI thread."""
    browse_btn.config(state="normal")
    camera_btn.config(state="normal")
    clear_btn.config(state="normal")
    
    confidence_bar.stop()
    confidence_bar.config(mode="determinate")
    confidence_bar["value"] = 0
    confidence_label.config(text="Confidence: 0%")
    
    status_label.config(text="ERROR", bg="#DC2626") # Red
    
    result_text.config(state="normal")
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, f"❌ RECOGNITION FAIL\n\nError details:\n{err}", "accent")
    result_text.config(state="disabled")
    
    messagebox.showerror("Error", f"Recognition failed:\n{err}")

# =====================================
# ACTION HANDLERS
# =====================================

def browse_image():
    """Opens a file dialog to select a local image file and processes it."""
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Image Files", "*.jpg *.jpeg *.png")
        ]
    )
    if not file_path:
        return
    process_image(file_path)

def capture_image():
    """Opens a custom Tkinter window displaying live camera feed with a GUI Capture button."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Webcam Error", "Failed to access the camera. Make sure it is connected and not in use by another application.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Create modal-like TopLevel window
    camera_win = tk.Toplevel(root)
    camera_win.title("Camera - Capture Part")
    camera_win.configure(bg="#111827")
    camera_win.resizable(False, False)
    
    # Center window relative to root GUI
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    
    win_w = 680
    win_h = 580
    pos_x = root_x + (root_w - win_w) // 2
    pos_y = root_y + (root_h - win_h) // 2
    camera_win.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
    
    # Make modal
    camera_win.transient(root)
    camera_win.grab_set()
    
    # Header label in window
    header = tk.Label(
        camera_win,
        text="Align Spare Part In Frame",
        font=("Segoe UI", 12, "bold"),
        fg="#10B981",
        bg="#111827"
    )
    header.pack(pady=10)
    
    # Video preview label
    video_label = tk.Label(camera_win, bg="#1F2937", bd=1, relief="solid")
    video_label.pack(padx=20, pady=5, fill="both", expand=True)
    
    # Footer instructions
    inst_label = tk.Label(
        camera_win,
        text="Press Space to Capture, ESC to Cancel",
        font=("Segoe UI", 9, "italic"),
        fg="#9CA3AF",
        bg="#111827"
    )
    inst_label.pack(pady=5)
    
    # Bottom Button Frame
    btn_frame = tk.Frame(camera_win, bg="#111827")
    btn_frame.pack(side="bottom", fill="x", pady=15)
    
    current_frame = [None]
    running = [True]
    
    def update_frame():
        if not running[0]:
            return
        ret, frame = cap.read()
        if ret:
            current_frame[0] = frame
            # Process OpenCV BGR frame to RGB PIL image for Tkinter
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_img)
            img.thumbnail((640, 480))
            
            photo = ImageTk.PhotoImage(image=img, master=camera_win)
            video_label.config(image=photo)
            video_label.image = photo  # Keep reference
            
        camera_win.after(15, update_frame)
        
    def close_camera():
        running[0] = False
        cap.release()
        camera_win.destroy()
        
    def capture():
        if current_frame[0] is not None:
            os.makedirs("test_images", exist_ok=True)
            file_path = "test_images/camera_capture.jpg"
            try:
                cv2.imwrite(file_path, current_frame[0])
                close_camera()
                process_image(file_path)
            except Exception as e:
                messagebox.showerror("File Error", f"Failed to save captured image: {e}")
        else:
            messagebox.showwarning("Capture Error", "Camera feed is starting. Please wait.")
            
    # Button widgets matching header/main styling
    capture_btn = tk.Button(
        btn_frame,
        text="📷 Capture",
        command=capture,
        font=("Segoe UI", 11, "bold"),
        bg="#10B981", # Emerald Green
        fg="white",
        activebackground="#059669",
        activeforeground="white",
        bd=0,
        cursor="hand2",
        relief="flat"
    )
    capture_btn.pack(side="left", padx=30, expand=True, fill="x", ipady=8)
    
    cancel_btn = tk.Button(
        btn_frame,
        text="❌ Cancel",
        command=close_camera,
        font=("Segoe UI", 11, "bold"),
        bg="#4B5563", # Gray
        fg="white",
        activebackground="#374151",
        activeforeground="white",
        bd=0,
        cursor="hand2",
        relief="flat"
    )
    cancel_btn.pack(side="right", padx=30, expand=True, fill="x", ipady=8)
    
    # Key bindings
    camera_win.bind("<space>", lambda event: capture())
    camera_win.bind("<Escape>", lambda event: close_camera())
    camera_win.protocol("WM_DELETE_WINDOW", close_camera)
    
    # Start live feed update
    update_frame()

def reset_ui():
    """Clears the GUI state back to its initial ready state."""
    image_references.clear()
    image_label.config(image="", text="No Image Selected\n\nUse buttons below to browse or capture a photo")
    
    status_label.config(text="READY", bg="#10B981")
    
    result_text.config(state="normal")
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, "Upload or capture an image to begin matching...\n\nThe computer vision engine will extract features and query the local repository.", "info")
    result_text.config(state="disabled")
    
    confidence_label.config(text="Confidence: 0%")
    confidence_bar.config(mode="determinate")
    confidence_bar["value"] = 0

# =====================================
# BUTTONS CONTROLS
# =====================================

browse_btn = tk.Button(
    root,
    text="📂 Browse Image",
    command=browse_image,
    font=("Segoe UI", 12, "bold"),
    bg="#2563EB",
    fg="white",
    activebackground="#1D4ED8",
    activeforeground="white",
    bd=0,
    cursor="hand2",
    relief="flat"
)
browse_btn.place(x=240, y=580, width=200, height=45)

camera_btn = tk.Button(
    root,
    text="📷 Capture Image",
    command=capture_image,
    font=("Segoe UI", 12, "bold"),
    bg="#DC2626",
    fg="white",
    activebackground="#B91C1C",
    activeforeground="white",
    bd=0,
    cursor="hand2",
    relief="flat"
)
camera_btn.place(x=500, y=580, width=200, height=45)

clear_btn = tk.Button(
    root,
    text="🔄 Reset / Clear",
    command=reset_ui,
    font=("Segoe UI", 12, "bold"),
    bg="#4B5563",
    fg="white",
    activebackground="#374151",
    activeforeground="white",
    bd=0,
    cursor="hand2",
    relief="flat"
)
clear_btn.place(x=760, y=580, width=200, height=45)

# =====================================
# FOOTER
# =====================================
footer = tk.Label(
    root,
    text="© Hari Chand Anand & Co. | Spare Part Recognition System",
    font=("Segoe UI", 9),
    bg="#111827",
    fg="#9CA3AF",
    pady=8
)
footer.pack(
    side="bottom",
    fill="x"
)

# Start queue checking and mainloop
process_gui_queue()
root.mainloop()