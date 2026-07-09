import sys
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from PIL import Image

# Rich UI Library
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import configurations and modules
from config import WEIGHTS
from modules.classifier import predict
from modules.metadata import analyze_metadata
from modules.artifacts import perform_ela
from modules.spectral import analyze_frequency

console = Console()

def run_cli(img_path):
    if not os.path.exists(img_path):
        console.print(f"[bold red]Error:[/] Could not find image at {img_path}")
        return

    console.print(f"\n[bold blue]Analyzing Image:[/] [yellow]{img_path}[/]")
    
    try:
        img_pil = Image.open(img_path).convert("RGB")
    except Exception as e:
        console.print(f"[bold red]Error opening image:[/] {e}")
        return

    # Run Analysis with a Progress Spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        progress.add_task(description="Running EfficientNet-B3 Classifier...", total=None)
        pred_label, ai_prob, _, _ = predict(img_pil)
        model_score = ai_prob
        
        progress.add_task(description="Running Metadata Analysis...", total=None)
        meta_score, meta_note = analyze_metadata(img_path)
        
        progress.add_task(description="Running Error Level Analysis (ELA)...", total=None)
        _, ela_score, ela_note = perform_ela(img_pil)
        
        progress.add_task(description="Running Spectral Analysis (FFT)...", total=None)
        _, fft_score, fft_note = analyze_frequency(img_pil)

    # Calculate Final Score
    final_score = (
        (model_score * WEIGHTS["classifier"]) +
        (meta_score  * WEIGHTS["metadata"]) +
        (ela_score   * WEIGHTS["ela"]) +
        (fft_score   * WEIGHTS["fft"])
    )
    
    # Build the Rich Table
    table = Table(title="Handbag Forensic Report", show_header=True, header_style="bold magenta")
    table.add_column("Module", style="cyan")
    table.add_column("Weight", justify="right")
    table.add_column("AI Probability", justify="right", style="green")
    table.add_column("Notes", style="italic")
    
    table.add_row("Core AI Model", "85%", f"{(model_score*100):.1f}%", "")
    table.add_row("EXIF Metadata", "5%", f"{(meta_score*100):.0f}%", meta_note)
    table.add_row("Error Level Analysis", "5%", f"{(ela_score*100):.0f}%", ela_note)
    table.add_row("Spectral FFT", "5%", f"{(fft_score*100):.0f}%", fft_note)
    
    console.print("\n")
    console.print(table)
    
    # Final Verdict Panel
    if final_score >= 0.5:
        verdict_text = Text(f"VERDICT: AI GENERATED\nCONFIDENCE: {(final_score*100):.1f}%", justify="center", style="bold red")
        panel = Panel(verdict_text, border_style="red", padding=(1, 2))
    else:
        verdict_text = Text(f"VERDICT: REAL HANDBAG\nCONFIDENCE: {((1.0 - final_score)*100):.1f}%", justify="center", style="bold green")
        panel = Panel(verdict_text, border_style="green", padding=(1, 2))
        
    console.print(panel)
    console.print("\n")

def select_file():
    """Opens a file dialog safely on the main thread."""
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    
    img_path = filedialog.askopenfilename(
        title="Select a Handbag Image to Analyze",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")]
    )
    
    # Important: Properly destroy the root to release the Tkinter thread
    # This prevents terminal print overlapping glitches in Windows
    root.destroy()
    return img_path

if __name__ == "__main__":
    console.clear()
    console.print(Panel.fit("[bold cyan]Handbag AI Detector CLI[/]", border_style="cyan"))
    
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
    else:
        console.print("[dim]Opening file selection window...[/]")
        img_path = select_file()
        
        if not img_path:
            console.print("[yellow]No file selected. Exiting.[/]")
            sys.exit(0)
            
    run_cli(img_path)
