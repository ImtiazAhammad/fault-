from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime, timedelta
import customtkinter as ctk
import numpy as np
from matplotlib.dates import DateFormatter

class TrendAnalyzer:
    def __init__(self):
        # Initialize trend data storage
        self.trend_data = {
            "Air Handling Unit": {
                "timestamps": deque(maxlen=100),
                "faults": deque(maxlen=100),
                "fault_counts": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "parameter_history": {}  # For storing parameter values
            },
            "Chiller": {
                "timestamps": deque(maxlen=100),
                "faults": deque(maxlen=100),
                "fault_counts": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "parameter_history": {}
            },
            "Generator": {
                "timestamps": deque(maxlen=100),
                "faults": deque(maxlen=100),
                "fault_counts": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "parameter_history": {}
            }
        }
        
        # Store references to UI elements
        self.machine_frames = {}
        
        # Define fault types
        self.fault_types = {
            "Air Handling Unit": {
                0: "Normal Operation",
                1: "Fan Fault",
                2: "Filter Dirty",
                3: "Coil Fault",
                4: "Damper Fault"
            },
            "Chiller": {
                0: "Normal Operation",
                1: "Low Refrigerant",
                2: "Condenser Fault",
                3: "Flow Switch Fault",
                4: "Pump Failure"
            },
            "Generator": {
                0: "Normal Operation",
                1: "Low Oil Pressure",
                2: "Overheating",
                3: "Voltage Imbalance",
                4: "Fuel System Fault"
            }
        }

        # Define key parameters to track for each machine
        self.tracked_parameters = {
            "Air Handling Unit": ["supply_air_temp", "fan_speed", "filter_dp"],
            "Chiller": ["chill_water_outlet", "condenser_pressure", "differential_pressure"],
            "Generator": ["oil_pressure", "coolant_temp", "frequency"]
        }

    def create_trend_graphs(self, machine_container, machine):
        """Create trend visualization components for a machine"""
        trend_frame = ctk.CTkFrame(machine_container, fg_color="#1B1B1B")
        trend_frame.pack(fill="x", padx=5, pady=5)
        
        # Add trend title
        trend_title = ctk.CTkLabel(trend_frame, text="PARAMETER TRENDS",
                                  font=("Roboto", 16, "bold"),
                                  text_color="#00FF00")
        trend_title.pack(pady=5)
        
        # Create matplotlib figure with subplots
        fig = Figure(figsize=(6, 6), facecolor='#1B1B1B')
        
        # Create subplots for parameters and fault status
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 0.5])
        axes = [fig.add_subplot(gs[i]) for i in range(4)]
        
        # Customize appearance for all subplots
        for ax in axes:
            ax.set_facecolor('#2B2B2B')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
            ax.grid(True, linestyle='--', alpha=0.3)
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=trend_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initialize parameter history
        for param in self.tracked_parameters[machine]:
            self.trend_data[machine]["parameter_history"][param] = deque(maxlen=100)
        
        # Create statistics frame
        stats_frame = ctk.CTkFrame(trend_frame, fg_color="#2B2B2B")
        stats_frame.pack(fill="x", padx=5, pady=5)
        
        stats_title = ctk.CTkLabel(stats_frame, text="Fault Statistics",
                                  font=("Roboto", 14, "bold"),
                                  text_color="#00FF00")
        stats_title.pack(pady=2)
        
        stats_label = ctk.CTkLabel(stats_frame, text="",
                                  font=("Roboto", 12))
        stats_label.pack(pady=2)
        
        # Store references
        if machine not in self.machine_frames:
            self.machine_frames[machine] = {}
            
        self.machine_frames[machine].update({
            "trend_canvas": canvas,
            "trend_axes": axes,
            "stats_label": stats_label
        })
        
        return trend_frame

    def update_trends(self, machine, prediction, data=None, timestamp=None):
        """Update trend data and visualizations for a machine"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Update trend data
        self.trend_data[machine]["timestamps"].append(timestamp)
        self.trend_data[machine]["faults"].append(prediction)
        self.trend_data[machine]["fault_counts"][prediction] += 1
        
        # Update parameter history if data is provided
        if data:
            for param in self.tracked_parameters[machine]:
                if param in data:
                    self.trend_data[machine]["parameter_history"][param].append(float(data[param]))
        
        # Get canvas and axes
        canvas = self.machine_frames[machine]["trend_canvas"]
        axes = self.machine_frames[machine]["trend_axes"]
        
        # Clear all axes
        for ax in axes:
            ax.clear()
        
        timestamps = list(self.trend_data[machine]["timestamps"])
        
        if timestamps:
            # Plot parameter trends in first three subplots
            for idx, param in enumerate(self.tracked_parameters[machine]):
                if param in self.trend_data[machine]["parameter_history"]:
                    values = list(self.trend_data[machine]["parameter_history"][param])
                    if values:
                        # Create smooth curve
                        axes[idx].plot(timestamps, values, '-', color='#00FF00', linewidth=2)
                        axes[idx].set_title(param.replace('_', ' ').title(), color='white', pad=5)
                        axes[idx].grid(True, linestyle='--', alpha=0.3)
            
            # Plot fault status in bottom subplot
            faults = list(self.trend_data[machine]["faults"])
            fault_colors = ['green' if f == 0 else 'red' for f in faults]
            axes[-1].plot(timestamps, faults, '-', color='#FF5555', linewidth=2)
            axes[-1].set_ylim(-0.5, 4.5)
            axes[-1].set_yticks(range(5))
            axes[-1].set_yticklabels([self.fault_types[machine][i] for i in range(5)], 
                                    fontsize=8)
            axes[-1].set_title('Fault Status', color='white', pad=5)
        
        # Format x-axis
        for ax in axes:
            ax.tick_params(colors='white')
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Adjust layout
        fig = canvas.figure
        fig.tight_layout()
        canvas.draw()
        
        # Update statistics
        self.update_statistics(machine)

    def update_statistics(self, machine):
        """Update statistics display for a machine"""
        total_samples = sum(self.trend_data[machine]["fault_counts"].values())
        stats_text = "Fault Distribution:\n"
        
        for fault_type, count in self.trend_data[machine]["fault_counts"].items():
            percentage = (count / total_samples) * 100 if total_samples > 0 else 0
            fault_name = self.fault_types[machine][fault_type]
            stats_text += f"{fault_name}: {percentage:.1f}%\n"
        
        self.machine_frames[machine]["stats_label"].configure(text=stats_text)

    def get_fault_statistics(self, machine):
        """Get fault statistics for a machine"""
        total_samples = sum(self.trend_data[machine]["fault_counts"].values())
        statistics = {}
        
        for fault_type, count in self.trend_data[machine]["fault_counts"].items():
            percentage = (count / total_samples) * 100 if total_samples > 0 else 0
            fault_name = self.fault_types[machine][fault_type]
            statistics[fault_name] = {
                "count": count,
                "percentage": percentage
            }
        
        return statistics 