"""Tkinter GUI for CImageOptimizer."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from cimageoptimizer.application.services.optimization_service import OptimizationService
from cimageoptimizer.core.enums import ProcessMode
from cimageoptimizer.core.models import OptimizationResult, OptimizationSettings

MODE_ALL_FILES = "All Files (Optimize images, copy others)"
MODE_IMAGES_ONLY = "Images Only (Skip non-images)"


class App:
    def __init__(self, root: tk.Tk, optimization_service: Optional[OptimizationService] = None) -> None:
        self.root = root
        self._optimization_service = optimization_service or OptimizationService()

        self.root.title("CImageOptimizer")
        self.root.geometry("600x400")
        self.root.minsize(500, 350)

        # Configure grid weight
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(6, weight=1)

        self.is_cancelled = False

        # UI Elements
        # --- Source ---
        ttk.Label(root, text="Source Directory:").grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")
        self.source_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.source_var).grid(row=0, column=1, padx=10, pady=(15, 5), sticky="ew")
        ttk.Button(root, text="Browse", command=self.browse_source).grid(row=0, column=2, padx=10, pady=(15, 5))

        # --- Output ---
        ttk.Label(root, text="Output Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.output_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.output_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ttk.Button(root, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=10, pady=5)

        # --- Options ---
        ttk.Label(root, text="Process Mode:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.mode_var = tk.StringVar(value=MODE_ALL_FILES)
        self.mode_cb = ttk.Combobox(
            root,
            textvariable=self.mode_var,
            state="readonly",
            values=[MODE_ALL_FILES, MODE_IMAGES_ONLY],
        )
        self.mode_cb.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- Action ---
        self.action_frame = ttk.Frame(root)
        self.action_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(self.action_frame, text="Start Optimization", command=self.start_optimization)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(self.action_frame, text="Cancel", command=self.cancel_optimization, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # --- Progress ---
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # --- Logs ---
        self.log_text = tk.Text(root, state="disabled", height=10)
        self.log_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def cancel_optimization(self) -> None:
        self.is_cancelled = True
        self.cancel_btn.config(state="disabled")
        self.log("Cancelling... waiting for current file to finish...")

    def browse_source(self) -> None:
        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            self.source_var.set(folder)

    def browse_output(self) -> None:
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_var.set(folder)

    def log(self, message: str) -> None:
        self.root.after(0, self._log_main_thread, message)

    def _log_main_thread(self, message: str) -> None:
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def progress(self, current: int, total: int) -> None:
        if total > 0:
            percentage = (current / total) * 100
            self.root.after(0, self._progress_main_thread, percentage)

    def _progress_main_thread(self, percentage: float) -> None:
        self.progress_var.set(percentage)

    def start_optimization(self) -> None:
        source = self.source_var.get().strip()
        output = self.output_var.get().strip()
        images_only = self.mode_var.get() == MODE_IMAGES_ONLY

        if not source or not output:
            messagebox.showerror("Error", "Please select both Source and Output directories.")
            return

        self.start_btn.config(state="disabled")
        self.progress_var.set(0)

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        self.log("Starting Optimization Process...")

        self.is_cancelled = False

        # Run in thread to prevent UI freezing
        thread = threading.Thread(target=self.run_task, args=(source, output, images_only))
        thread.daemon = True
        thread.start()

    def run_task(self, source: str, output: str, images_only: bool) -> None:
        self.root.after(0, lambda: self.cancel_btn.config(state="normal"))
        try:
            settings = OptimizationSettings(
                source_dir=Path(source),
                output_dir=Path(output),
                process_mode=ProcessMode.IMAGES_ONLY if images_only else ProcessMode.ALL_FILES,
            )
            result: OptimizationResult = self._optimization_service.run(
                settings,
                progress_callback=self.progress,
                log_callback=self.log,
                check_cancel_callback=lambda: self.is_cancelled,
            )
            if result.cancelled:
                self.log("Process Cancelled!")
                self.root.after(0, lambda: messagebox.showinfo("Cancelled", "Optimization was cancelled."))
            else:
                self.log("Process Completed Successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", "Optimization Completed!"))
        except Exception as exc:
            self.log(f"Error: {exc}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(exc)))
        finally:
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.cancel_btn.config(state="disabled"))
