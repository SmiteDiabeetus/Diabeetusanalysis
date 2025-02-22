import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, ttk
from datetime import datetime

# Conversion factor: 1 mmol/L = 18 mg/dL
CONVERSION_FACTOR = 18

class DiabetesAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Diabetes Data Analyzer")
        self.root.geometry("400x300")

        # Variables
        self.cgm_file = None
        self.insulin_file = None
        self.unit_var = tk.StringVar(value="mg/dL")  # Default unit

        # UI Elements
        tk.Label(root, text="Diabetes Data Analyzer", font=("Arial", 14)).pack(pady=10)

        tk.Button(root, text="Import CGM Data", command=self.import_cgm).pack(pady=5)
        self.cgm_label = tk.Label(root, text="No CGM file selected")
        self.cgm_label.pack()

        tk.Button(root, text="Import Insulin Data", command=self.import_insulin).pack(pady=5)
        self.insulin_label = tk.Label(root, text="No insulin file selected")
        self.insulin_label.pack()

        tk.Label(root, text="Select Units:").pack(pady=5)
        unit_menu = ttk.Combobox(root, textvariable=self.unit_var, values=["mg/dL", "mmol/L"], state="readonly")
        unit_menu.pack()

        tk.Button(root, text="Analyze Data", command=self.analyze_data).pack(pady=20)

    def import_cgm(self):
        self.cgm_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if self.cgm_file:
            self.cgm_label.config(text=f"CGM File: {self.cgm_file.split('/')[-1]}")

    def import_insulin(self):
        self.insulin_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if self.insulin_file:
            self.insulin_label.config(text=f"Insulin File: {self.insulin_file.split('/')[-1]}")

    def analyze_data(self):
        if not self.cgm_file or not self.insulin_file:
            tk.messagebox.showerror("Error", "Please import both CGM and insulin data files.")
            return

        # Load data
        cgm_data = pd.read_csv(self.cgm_file, parse_dates=["Timestamp"])
        insulin_data = pd.read_csv(self.insulin_file, parse_dates=["Timestamp"])

        # Clean and merge
        cgm_data = cgm_data.dropna(subset=["Glucose (mg/dL)"])
        insulin_data = insulin_data.dropna(subset=["Dose (units)"])
        merged_data = pd.merge_asof(
            cgm_data.sort_values("Timestamp"),
            insulin_data.sort_values("Timestamp"),
            on="Timestamp",
            direction="nearest",
            tolerance=pd.Timedelta("15 minutes")
        )

        # Convert units if needed
        unit = self.unit_var.get()
        if unit == "mmol/L":
            merged_data["Glucose"] = merged_data["Glucose (mg/dL)"] / CONVERSION_FACTOR
            target_low, target_high = 3.9, 10.0  # mmol/L range
        else:
            merged_data["Glucose"] = merged_data["Glucose (mg/dL)"]
            target_low, target_high = 70, 180  # mg/dL range

        # Analysis
        avg_glucose = merged_data["Glucose"].mean()
        time_in_range = merged_data[
            (merged_data["Glucose"] >= target_low) & (merged_data["Glucose"] <= target_high)
        ].shape[0] / merged_data.shape[0] * 100

        # Print results
        print(f"Average Glucose: {avg_glucose:.1f} {unit}")
        print(f"Time in Range ({target_low}-{target_high} {unit}): {time_in_range:.1f}%")

        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(merged_data["Timestamp"], merged_data["Glucose"], label="Glucose", color="blue")
        plt.scatter(
            merged_data["Timestamp"],
            merged_data["Dose (units)"].fillna(0) * (10 if unit == "mg/dL" else 0.5),  # Scale for visibility
            label="Insulin Dose (scaled)",
            color="red",
            marker="o"
        )
        plt.axhline(y=target_low, color="green", linestyle="--", label="Target Range")
        plt.axhline(y=target_high, color="green", linestyle="--")
        plt.xlabel("Time")
        plt.ylabel(f"Glucose ({unit})")
        plt.title("Glucose Levels and Insulin Doses")
        plt.legend()
        plt.show()

        # Pattern detection
        high_threshold = 11.1 if unit == "mmol/L" else 200
        high_after_insulin = merged_data[
            (merged_data["Dose (units)"].notna()) & (merged_data["Glucose"].shift(-6) > high_threshold)
        ]
        if not high_after_insulin.empty:
            tk.messagebox.showinfo("Pattern Detected", 
                f"High glucose (> {high_threshold} {unit}) detected 30 mins after some insulin doses.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DiabetesAnalyzer(root)
    root.mainloop()