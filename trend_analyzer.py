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

        # Update tracked_parameters for all devices
        self.tracked_parameters = {
            "Air Handling Unit": [
                ("supply_air_temp", "supply_air_setpoint"),
                ("return_air_temp", "return_air_setpoint"),
                ("room_air_temp", "room_air_setpoint"),
                ("return_air_humidity", "return_air_humidity_setpoint"),
                ("fan_speed", "fan_speed_setpoint"),
                ("cooling_state", "cooling_state_setpoint"),
                ("electric_reheat_state", "electric_reheat_state_setpoint"),
                ("filter_dp", "filter_dp_setpoint"),
                ("cool_water_valve", "cool_water_valve_setpoint"),
                ("hot_water_valve", "hot_water_valve_setpoint"),
                ("outside_air_damper", "outside_air_damper_setpoint")
            ],
            "Chiller": [
                ("chill_water_outlet", "chill_water_outlet_setpoint"),
                ("chill_water_inlet", "chill_water_inlet_setpoint"),
                ("condenser_pressure", "condenser_pressure_setpoint"),
                ("differential_pressure", "differential_pressure_setpoint"),
                ("supply_water_temp", "supply_water_temp_setpoint"),
                ("cooling_tower_fan", "cooling_tower_fan_setpoint"),
                ("condenser_pump", "condenser_pump_setpoint"),
                ("return_condenser_valve", "return_condenser_valve_setpoint"),
                ("flow_switch", "flow_switch_setpoint")
            ],
            "Generator": [
                ("oil_pressure", "oil_pressure_setpoint"),
                ("coolant_temp", "coolant_temp_setpoint"),
                ("battery_voltage", "battery_voltage_setpoint"),
                ("phase1_voltage", "phase1_voltage_setpoint"),
                ("phase2_voltage", "phase2_voltage_setpoint"),
                ("phase3_voltage", "phase3_voltage_setpoint"),
                ("frequency", "frequency_setpoint"),
                ("load_percent", "load_percent_setpoint"),
                ("run_hours", "run_hours_setpoint"),
                ("fuel_level", "fuel_level_setpoint")
            ]
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
        num_params = len(self.tracked_parameters[machine])
        fig = Figure(figsize=(6, 2*num_params), facecolor='#1B1B1B')  # Adjust figure height based on parameters
        
        # Create subplots for all parameters
        gs = fig.add_gridspec(num_params, 1)
        axes = [fig.add_subplot(gs[i]) for i in range(num_params)]
        
        # Customize appearance for all subplots
        for ax in axes:
            ax.set_facecolor('#2B2B2B')
            ax.tick_params(colors='white', labelsize=8)  # Reduced font size
            for spine in ax.spines.values():
                spine.set_color('white')
            ax.grid(True, linestyle='--', alpha=0.3)
        
        # Create canvas with scrollable container
        canvas_frame = ctk.CTkScrollableFrame(trend_frame, fg_color="#1B1B1B")
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Initialize parameter history
        for param, setpoint_param in self.tracked_parameters[machine]:
            self.trend_data[machine]["parameter_history"][param] = deque(maxlen=100)
        
        # Store references
        if machine not in self.machine_frames:
            self.machine_frames[machine] = {}
            
        self.machine_frames[machine].update({
            "trend_canvas": canvas,
            "trend_axes": axes
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
            for param, setpoint_param in self.tracked_parameters[machine]:
                # Ensure both parameter and setpoint exist in data
                if param in data and setpoint_param in data:
                    # Store both value and setpoint
                    self.trend_data[machine]["parameter_history"].setdefault(param, deque(maxlen=100)).append(
                        (data[param], data[setpoint_param])
                    )
        
        # Get canvas and axes
        canvas = self.machine_frames[machine]["trend_canvas"]
        axes = self.machine_frames[machine]["trend_axes"]
        
        # Clear all axes
        for ax in axes:
            ax.clear()
        
        # Get timestamps list
        timestamps = list(self.trend_data[machine]["timestamps"])
        
        # Plot parameter trends
        for idx, (param, setpoint_param) in enumerate(self.tracked_parameters[machine]):
            history = self.trend_data[machine]["parameter_history"].get(param, [])
            if len(history) >= 2:  # Need at least 2 points to plot
                values = [h[0] for h in history]
                setpoints = [h[1] for h in history]
                
                # Plot actual values
                axes[idx].plot(timestamps[-len(values):], values, '-', color='#00FF00', linewidth=2, label='Actual')
                
                # Plot setpoints
                axes[idx].plot(timestamps[-len(setpoints):], setpoints, '--', color='#FFA500', linewidth=1.5, label='Setpoint')
                
                # Configure plot
                axes[idx].set_title(param.replace('_', ' ').title(), color='white', pad=5, fontsize=8)
                axes[idx].grid(True, linestyle='--', alpha=0.3)
                axes[idx].legend(fontsize=6, facecolor='#2B2B2B', edgecolor='white')
                
                # Add current value annotation
                if values:
                    axes[idx].annotate(f'{values[-1]:.2f}', 
                                     (timestamps[-1], values[-1]),
                                     textcoords="offset points",
                                     xytext=(0,5),
                                     ha='center',
                                     color='#00FFFF',
                                     fontsize=6)
        
        # Format axes
        for ax in axes:
            ax.tick_params(colors='white', labelsize=6)
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
            ax.set_facecolor('#2B2B2B')
            for spine in ax.spines.values():
                spine.set_color('white')
        
        try:
            canvas.figure.tight_layout()
            canvas.draw()
        except Exception as e:
            print(f"Graph update warning: {str(e)}")
        
        # Update statistics with prediction
        self.update_statistics(machine, prediction)

    def update_statistics(self, machine, prediction):
        """Update both histogram and trend graphs"""
        # Update histogram
        if hasattr(self, 'histograms') and machine in self.histograms:
            ax = self.histograms[machine]['ax']
            ax.clear()
            
            fault_counts = self.trend_data[machine]['fault_counts']
            labels = [self.fault_types[machine][i] for i in range(5)]
            values = [fault_counts[i] for i in range(5)]
            
            bars = ax.bar(range(len(labels)), values, 
                         color=['#00FF00' if i == 0 else '#FF0000' for i in range(5)])
            
            # Set ticks and labels properly
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_ylabel('Count', color='white')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', color='white')
            
            self.histograms[machine]['fig'].tight_layout()
            self.histograms[machine]['canvas'].draw()
        
        # Update fault trend
        if hasattr(self, 'fault_trends') and machine in self.fault_trends:
            ax = self.fault_trends[machine]['ax']
            ax.clear()
            
            timestamps = list(self.trend_data[machine]['timestamps'])
            faults = list(self.trend_data[machine]['faults'])
            
            if timestamps and faults:
                ax.plot(timestamps, faults, '-', color='#FF5555', linewidth=2)
                ax.set_ylim(-0.5, 4.5)
                ax.set_yticks(range(5))
                ax.set_yticklabels([self.fault_types[machine][i] for i in range(5)])
                
                ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.fault_trends[machine]['fig'].tight_layout()
            self.fault_trends[machine]['canvas'].draw()

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

    def create_statistics_histogram(self, parent_frame):
        """Create histogram visualization for fault statistics"""
        fig = Figure(figsize=(8, 4), facecolor='#2B2B2B')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2B2B2B')
        
        # Customize axes
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('#00FF00')
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store references
        self.histogram = {
            'fig': fig,
            'ax': ax,
            'canvas': canvas
        }
    
    def update_statistics_histogram(self, machine):
        """Update the histogram with current data"""
        if not hasattr(self, 'histogram'):
            return
        
        ax = self.histogram['ax']
        ax.clear()
        
        # Get fault counts
        fault_counts = self.trend_data[machine]['fault_counts']
        faults = [self.fault_types[machine][k] for k in sorted(fault_counts.keys())]
        counts = [fault_counts[k] for k in sorted(fault_counts.keys())]
        
        # Create bars
        bars = ax.bar(faults, counts, color=['#00FF00' if k==0 else '#FF0000' for k in sorted(fault_counts.keys())])
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}',
                    ha='center', va='bottom',
                    color='white', fontsize=10)
        
        # Formatting
        ax.set_title(f'{machine} Fault Distribution', fontsize=14)
        ax.set_xlabel('Fault Type', fontsize=12)
        ax.set_ylabel('Occurrences', fontsize=12)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
        self.histogram['fig'].tight_layout()
        self.histogram['canvas'].draw()

    def create_fault_histogram(self, parent_frame, machine):
        """Create histogram for fault distribution"""
        fig = Figure(figsize=(6, 4), facecolor='#1A1A1A')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1A1A1A')
        
        # Customize appearance
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Store references
        if not hasattr(self, 'histograms'):
            self.histograms = {}
        self.histograms[machine] = {
            'fig': fig,
            'ax': ax,
            'canvas': canvas
        }

    def create_fault_trend(self, parent_frame, machine):
        """Create trend graph for fault status"""
        fig = Figure(figsize=(6, 4), facecolor='#1A1A1A')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1A1A1A')
        
        # Customize appearance
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Store references
        if not hasattr(self, 'fault_trends'):
            self.fault_trends = {}
        self.fault_trends[machine] = {
            'fig': fig,
            'ax': ax,
            'canvas': canvas
        } 