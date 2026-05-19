import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
from pathlib import Path
import optimizer

class App:
    def __init__(self, root):
        self.root = root
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
        self.mode_var = tk.StringVar(value="All Files (Optimize images, copy others)")
        self.mode_cb = ttk.Combobox(root, textvariable=self.mode_var, state="readonly", 
                                    values=["All Files (Optimize images, copy others)", "Images Only (Skip non-images)"])
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
        self.log_text = tk.Text(root, state='disabled', height=10)
        self.log_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def cancel_optimization(self):
        self.is_cancelled = True
        self.cancel_btn.config(state='disabled')
        self.log("Cancelling... waiting for current file to finish...")

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            self.source_var.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_var.set(folder)

    def log(self, message):
        # Schedule update on main thread
        self.root.after(0, self._log_main_thread, message)

    def _log_main_thread(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def progress(self, current, total):
        # Schedule update on main thread
        if total > 0:
            percentage = (current / total) * 100
            self.root.after(0, self._progress_main_thread, percentage)

    def _progress_main_thread(self, percentage):
        self.progress_var.set(percentage)

    def start_optimization(self):
        source = self.source_var.get().strip()
        output = self.output_var.get().strip()
        images_only = "Images Only" in self.mode_var.get()

        if not source or not output:
            messagebox.showerror("Error", "Please select both Source and Output directories.")
            return

        self.start_btn.config(state='disabled')
        self.progress_var.set(0)
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        self.log("Starting Optimization Process...")
        
        self.is_cancelled = False
        
        # Run in thread to prevent UI freezing
        thread = threading.Thread(target=self.run_task, args=(source, output, images_only))
        thread.daemon = True
        thread.start()

    def run_task(self, source, output, images_only):
        self.root.after(0, lambda: self.cancel_btn.config(state='normal'))
        try:
            optimizer.run_optimization(
                source, 
                output, 
                progress_callback=self.progress, 
                log_callback=self.log,
                check_cancel_callback=lambda: self.is_cancelled,
                images_only=images_only
            )
            if self.is_cancelled:
                self.log("Process Cancelled!")
                self.root.after(0, lambda: messagebox.showinfo("Cancelled", "Optimization was cancelled."))
            else:
                self.log("Process Completed Successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", "Optimization Completed!"))
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.start_btn.config(state='normal'))
            self.root.after(0, lambda: self.cancel_btn.config(state='disabled'))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
