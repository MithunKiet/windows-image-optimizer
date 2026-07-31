"""Tkinter GUI for CImageOptimizer."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from cimageoptimizer.application.services.optimization_service import OptimizationService
from cimageoptimizer.application.services.report_service import ReportService
from cimageoptimizer.core.enums import OptimizationProfile, ProcessMode
from cimageoptimizer.core.models import OptimizationResult, OptimizationSettings
from cimageoptimizer.infrastructure.config import load_settings, save_settings

MODE_ALL_FILES = "All Files (Optimize images, copy others)"
MODE_IMAGES_ONLY = "Images Only (Skip non-images)"

PROFILE_LABELS = {
    OptimizationProfile.SAFE: "Safe (largest files, best quality)",
    OptimizationProfile.RECOMMENDED: "Recommended (balanced)",
    OptimizationProfile.ADVANCED: "Advanced (smallest files, aggressive compression)",
}
PROFILE_LABELS_BY_TEXT = {label: profile for profile, label in PROFILE_LABELS.items()}


class App:
    def __init__(
        self,
        root: tk.Tk,
        optimization_service: Optional[OptimizationService] = None,
        report_service: Optional[ReportService] = None,
    ) -> None:
        self.root = root
        self._optimization_service = optimization_service or OptimizationService()
        self._report_service = report_service or ReportService()
        self._saved_settings = load_settings()
        self._last_result: Optional[OptimizationResult] = None
        self._selected_files: Optional[list[Path]] = None

        self.root.title("CImageOptimizer")
        self.root.geometry("600x470")
        self.root.minsize(500, 400)

        # Configure grid weight - row 7 holds the log panel, which should
        # absorb all extra vertical space when the window is resized.
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(7, weight=1)

        self.is_cancelled = False

        # UI Elements
        # --- Source ---
        ttk.Label(root, text="Source Directory:").grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")
        self.source_var = tk.StringVar(value=self._saved_settings.get("source_dir", ""))
        self.source_entry = ttk.Entry(root, textvariable=self.source_var)
        self.source_entry.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="ew")
        # Typing directly (or picking a folder) means "use this folder";
        # it overrides any previously selected individual files.
        self.source_entry.bind("<Key>", lambda _event: setattr(self, "_selected_files", None))
        ttk.Button(root, text="Browse Folder", command=self.browse_source).grid(
            row=0, column=2, padx=10, pady=(15, 5)
        )

        ttk.Label(root, text="").grid(row=1, column=0)
        ttk.Button(root, text="Or Select Individual Files...", command=self.select_source_files).grid(
            row=1, column=1, columnspan=2, padx=10, pady=(0, 5), sticky="w"
        )

        # --- Output ---
        ttk.Label(root, text="Output Directory:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.output_var = tk.StringVar(value=self._saved_settings.get("output_dir", ""))
        ttk.Entry(root, textvariable=self.output_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ttk.Button(root, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=10, pady=5)

        # --- Process mode ---
        ttk.Label(root, text="Process Mode:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        saved_mode = self._saved_settings.get("process_mode")
        mode_default = MODE_IMAGES_ONLY if saved_mode == ProcessMode.IMAGES_ONLY.value else MODE_ALL_FILES
        self.mode_var = tk.StringVar(value=mode_default)
        self.mode_cb = ttk.Combobox(
            root,
            textvariable=self.mode_var,
            state="readonly",
            values=[MODE_ALL_FILES, MODE_IMAGES_ONLY],
        )
        self.mode_cb.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- Optimization profile ---
        ttk.Label(root, text="Profile:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        saved_profile = self._saved_settings.get("profile", OptimizationProfile.RECOMMENDED.value)
        try:
            profile_default = PROFILE_LABELS[OptimizationProfile(saved_profile)]
        except ValueError:
            profile_default = PROFILE_LABELS[OptimizationProfile.RECOMMENDED]
        self.profile_var = tk.StringVar(value=profile_default)
        self.profile_cb = ttk.Combobox(
            root,
            textvariable=self.profile_var,
            state="readonly",
            values=list(PROFILE_LABELS.values()),
        )
        self.profile_cb.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- Action ---
        self.action_frame = ttk.Frame(root)
        self.action_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(self.action_frame, text="Start Optimization", command=self.start_optimization)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(self.action_frame, text="Cancel", command=self.cancel_optimization, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = ttk.Button(
            self.action_frame, text="Export Report", command=self.export_report, state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # --- Progress ---
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # --- Logs ---
        self.log_text = tk.Text(root, state="disabled", height=10)
        self.log_text.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def cancel_optimization(self) -> None:
        self.is_cancelled = True
        self.cancel_btn.config(state="disabled")
        self.log("Cancelling... waiting for current file to finish...")

    def export_report(self) -> None:
        if self._last_result is None:
            messagebox.showerror("Error", "Run an optimization first.")
            return

        path_str = filedialog.asksaveasfilename(
            title="Export Optimization Report",
            defaultextension=".json",
            filetypes=[("JSON report", "*.json"), ("CSV report", "*.csv")],
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            if path.suffix.lower() == ".csv":
                self._report_service.export_csv(self._last_result, path)
            else:
                self._report_service.export_json(self._last_result, path)
            self.log(f"Report exported: {path}")
            messagebox.showinfo("Report Exported", f"Report saved to:\n{path}")
        except OSError as exc:
            messagebox.showerror("Error", f"Failed to export report: {exc}")

    def browse_source(self) -> None:
        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            self._selected_files = None
            self.source_var.set(folder)

    def select_source_files(self) -> None:
        files = filedialog.askopenfilenames(title="Select Files to Optimize")
        if not files:
            return
        self._selected_files = [Path(f) for f in files]
        self.source_var.set(f"{len(self._selected_files)} file(s) selected")

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
        output = self.output_var.get().strip()
        process_mode = ProcessMode.IMAGES_ONLY if self.mode_var.get() == MODE_IMAGES_ONLY else ProcessMode.ALL_FILES
        profile = PROFILE_LABELS_BY_TEXT[self.profile_var.get()]

        if not output:
            messagebox.showerror("Error", "Please select an Output directory.")
            return

        if self._selected_files:
            source_files = self._selected_files
            source_dir = source_files[0].parent
        else:
            source = self.source_var.get().strip()
            if not source:
                messagebox.showerror(
                    "Error", "Please select a Source directory, or select individual files."
                )
                return
            source_files = None
            source_dir = Path(source)

        # Individual file selections aren't persisted (the files may not
        # exist next launch); only folder-based settings are remembered.
        if source_files is None:
            save_settings(
                {
                    "source_dir": str(source_dir),
                    "output_dir": output,
                    "process_mode": process_mode.value,
                    "profile": profile.value,
                }
            )

        self.start_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self._last_result = None
        self.progress_var.set(0)

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        self.log("Starting Optimization Process...")

        self.is_cancelled = False

        settings = OptimizationSettings.for_profile(
            profile, source_dir, Path(output), process_mode, source_files=source_files
        )

        # Run in thread to prevent UI freezing
        thread = threading.Thread(target=self.run_task, args=(settings,))
        thread.daemon = True
        thread.start()

    def run_task(self, settings: OptimizationSettings) -> None:
        self.root.after(0, lambda: self.cancel_btn.config(state="normal"))
        try:
            result: OptimizationResult = self._optimization_service.run(
                settings,
                progress_callback=self.progress,
                log_callback=self.log,
                check_cancel_callback=lambda: self.is_cancelled,
            )
            self._last_result = result
            self.root.after(0, lambda: self.export_btn.config(state="normal"))
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
