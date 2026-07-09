import tkinter as tk
from tkinter import filedialog
from src.ensemble import WatchBrainEnsemble

def main():
    print("Welcome to Watch Brain V2.0!")
    print("Loading models... (This may take a moment)")
    
    try:
        ensemble = WatchBrainEnsemble(model_path='models/best_watch_detector.pth')
    except Exception as e:
        print(f"\nError loading model: {e}")
        print("Please ensure 'models/best_watch_detector.pth' exists.")
        input("Press Enter to exit...")
        return

    # Setup basic tkinter root window
    root = tk.Tk()
    root.withdraw() # Hide the main window

    print("\nPlease select an image in the popup dialog...")
    
    file_path = filedialog.askopenfilename(
        title="Select Watch Image to Test",
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("All files", "*.*")
        ]
    )

    if not file_path:
        print("No file selected. Exiting.")
        return

    print(f"\nAnalyzing: {file_path}...")
    ensemble.evaluate(file_path)
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
