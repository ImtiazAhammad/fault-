# ui.py
import customtkinter as ctk
import joblib
import pandas as pd
import numpy as np
from tkinter import messagebox
import time
from data_sender import generate_random_fault_data
import threading
from trend_analyzer import TrendAnalyzer
from tkinter import ttk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FaultDetectionApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Industrial Fault Detection System")
        self.window.geometry("1500x900")
        
        # Define setpoint ranges for each parameter
        self.setpoint_ranges = {
            "Air Handling Unit": {
                "supply_air_temp": (15, 25),
                "return_air_temp": (20, 28),
                "fan_speed": (30, 100),
                "filter_dp": (50, 300)
            },
            "Chiller": {
                "chill_water_outlet": (4, 12),
                "condenser_pressure": (3, 6),
                "differential_pressure": (10, 20)
            },
            "Generator": {
                "oil_pressure": (1.5, 2.5),
                "coolant_temp": (75, 95),
                "frequency": (49.5, 50.5)
            }
        }
        
        # Initialize setpoint values
        self.setpoints = {}
        for machine, params in self.setpoint_ranges.items():
            self.setpoints[machine] = {
                param: (min_val + max_val) / 2 
                for param, (min_val, max_val) in params.items()
            }
        
        # Define fault types for each machine
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
        
        # Initialize trend analyzer
        self.trend_analyzer = TrendAnalyzer()
        
        # Create the main layout with navbar
        self.create_navbar_layout()
        
        # Load models
        try:
            self.models = {
                "Air Handling Unit": joblib.load("models/ahu_model.pkl"),
                "Chiller": joblib.load("models/chiller_model.pkl"),
                "Generator": joblib.load("models/generator_model.pkl")
            }
            print("Models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            messagebox.showerror("Error", f"Failed to load models: {str(e)}")
            return
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self.continuous_monitoring)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def create_navbar_layout(self):
        # Create main container with navbar and content area
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True)
        
        # Create navbar
        self.navbar = ctk.CTkFrame(self.main_container, width=200, fg_color="#1B1B1B")
        self.navbar.pack(side="left", fill="y", padx=5, pady=5)
        
        # Add logo or title to navbar
        nav_title = ctk.CTkLabel(self.navbar, text="Control Panel",
                               font=("Roboto", 20, "bold"),
                               text_color="#00FF00")
        nav_title.pack(pady=20, padx=10)
        
        # Add navigation buttons
        self.create_nav_button("Dashboard", self.show_dashboard)
        self.create_nav_button("Settings", self.show_settings)
        self.create_nav_button("Statistics", self.show_statistics)
        
        # Create main content area with scrollbar
        self.content_container = ctk.CTkFrame(self.main_container)
        self.content_container.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.content_container)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # Create frames dictionary to hold different views
        self.views = {}
        
        # Create dashboard view
        self.views['dashboard'] = self.create_dashboard()
        
        # Create settings view
        self.views['settings'] = self.create_settings()
        
        # Show dashboard by default
        self.show_dashboard()

    def create_nav_button(self, text, command):
        btn = ctk.CTkButton(self.navbar, text=text,
                           font=("Roboto", 14),
                           fg_color="#2B2B2B",
                           hover_color="#3B3B3B",
                           command=command)
        btn.pack(pady=5, padx=10, fill="x")

    def create_dashboard(self):
        # Create dashboard frame
        dashboard = ctk.CTkFrame(self.scrollable_frame)
        
        # Create three columns for machines
        self.machine_frames = {}
        
        for idx, machine in enumerate(["Air Handling Unit", "Chiller", "Generator"]):
            # Create machine container
            machine_container = ctk.CTkFrame(dashboard)
            machine_container.grid(row=0, column=idx, padx=10, pady=10, sticky="nsew")
            dashboard.grid_columnconfigure(idx, weight=1)
            
            # Machine header
            header_frame = ctk.CTkFrame(machine_container, fg_color="#2B2B2B")
            header_frame.pack(fill="x", padx=5, pady=5)
            
            title = ctk.CTkLabel(header_frame, text=machine, 
                               font=("Roboto", 20, "bold"),
                               text_color="#00FF00")
            title.pack(pady=10)
            
            # Status display
            status_frame = ctk.CTkFrame(machine_container, fg_color="#1B1B1B")
            status_frame.pack(fill="x", padx=5, pady=5)
            
            status = ctk.CTkLabel(status_frame, text="MONITORING...",
                                font=("Roboto", 16, "bold"),
                                text_color="#FFA500")
            status.pack(pady=5)
            
            fault_type = ctk.CTkLabel(status_frame, text="",
                                    font=("Roboto", 14))
            fault_type.pack(pady=5)
            
            # Parameters display (remove scrollable)
            params_frame = ctk.CTkFrame(machine_container, fg_color="#1B1B1B")
            params_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            params_title = ctk.CTkLabel(params_frame, text="PARAMETERS",
                                      font=("Roboto", 16, "bold"),
                                      text_color="#00FF00")
            params_title.pack(pady=5)
            
            # Changed from CTkScrollableFrame to regular CTkFrame
            values_frame = ctk.CTkFrame(params_frame, fg_color="#2B2B2B")
            values_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            params_values = ctk.CTkLabel(values_frame, text="",
                                       font=("Roboto", 12))
            params_values.pack(pady=5)
            
            # Add trend graphs
            trend_frame = self.trend_analyzer.create_trend_graphs(machine_container, machine)
            
            self.machine_frames[machine] = {
                "status": status,
                "fault_type": fault_type,
                "params": params_values
            }
        
        return dashboard

    def create_settings(self):
        # Create settings frame with gradient effect
        settings = ctk.CTkFrame(self.scrollable_frame)
        
        # Main title with decorative elements
        title_frame = ctk.CTkFrame(settings, fg_color="#1E1E1E")
        title_frame.pack(fill="x", padx=20, pady=(20,30))
        
        title = ctk.CTkLabel(title_frame, text="⚙️ System Setpoint Configuration",
                           font=("Orbitron", 28, "bold"),
                           text_color="#00FF00")
        title.pack(pady=20)
        
        subtitle = ctk.CTkLabel(title_frame, 
                              text="Configure operational parameters for all devices",
                              font=("Exo 2", 14),
                              text_color="#AAAAAA")
        subtitle.pack(pady=(0,10))
        
        # Dictionary to store temporary setpoint values
        self.temp_setpoints = {}
        
        # Create sections for each machine
        for machine in ["Air Handling Unit", "Chiller", "Generator"]:
            machine_container = ctk.CTkFrame(settings, fg_color="#2B2B2B")
            machine_container.pack(fill="x", padx=30, pady=15)
            
            header_frame = ctk.CTkFrame(machine_container, fg_color="#1E1E1E")
            header_frame.pack(fill="x", padx=2, pady=2)
            
            icons = {
                "Air Handling Unit": "🌀",
                "Chiller": "❄️",
                "Generator": "⚡"
            }
            
            machine_title = ctk.CTkLabel(header_frame, 
                                       text=f"{icons[machine]} {machine}",
                                       font=("Orbitron", 22, "bold"),
                                       text_color="#00FF00")
            machine_title.pack(pady=15)
            
            self.temp_setpoints[machine] = {}
            
            # Enhanced parameter grid
            param_frame = ctk.CTkFrame(machine_container, fg_color="#232323")
            param_frame.pack(fill="x", padx=15, pady=15)
            
            # Create header row with industrial style
            headers = [
                ("Parameter", "w", "#00FF00", "Orbitron"),
                ("Current Value", "nsew", "#00FFFF", "DSEG14 Classic"),
                ("Setpoint Range", "nsew", "#FFA500", "Exo 2"),
                ("New Setpoint", "nsew", "#00FF00", "Orbitron")
            ]
            
            for col, (text, align, color, font) in enumerate(headers):
                header = ctk.CTkLabel(param_frame,
                                    text=text,
                                    font=(font, 14, "bold"),
                                    text_color=color)
                header.grid(row=0, column=col, padx=15, pady=(10,5), sticky=align)
            
            # Add parameters with enhanced styling
            if machine in self.setpoint_ranges:
                for idx, (param, (min_val, max_val)) in enumerate(self.setpoint_ranges[machine].items(), 1):
                    # Parameter name
                    param_name = ctk.CTkLabel(param_frame,
                                            text=param.replace('_', ' ').title(),
                                            font=("Exo 2", 12, "bold"),
                                            text_color="#FFFFFF")
                    param_name.grid(row=idx, column=0, padx=15, pady=10, sticky="w")
                    
                    # Current value with digital display style
                    current_frame = ctk.CTkFrame(param_frame, fg_color="#1A1A1A")
                    current_frame.grid(row=idx, column=1, padx=15, pady=10, sticky="ew")
                    
                    current_value = self.setpoints[machine][param]
                    current_label = ctk.CTkLabel(current_frame,
                                               text=f"{current_value:.2f}",
                                               font=("DSEG14 Classic", 16),
                                               text_color="#00FFFF")
                    current_label.pack(padx=10, pady=5)
                    
                    # Range display with industrial style
                    range_frame = ctk.CTkFrame(param_frame, fg_color="#1A1A1A")
                    range_frame.grid(row=idx, column=2, padx=15, pady=10, sticky="ew")
                    
                    range_text = f"[{min_val:.1f} - {max_val:.1f}]"
                    range_label = ctk.CTkLabel(range_frame,
                                             text=range_text,
                                             font=("Share Tech Mono", 12),
                                             text_color="#FFA500")
                    range_label.pack(padx=10, pady=5)
                    
                    # New setpoint entry with industrial style
                    entry_frame = ctk.CTkFrame(param_frame, fg_color="#1A1A1A")
                    entry_frame.grid(row=idx, column=3, padx=15, pady=10, sticky="ew")
                    
                    entry = ctk.CTkEntry(entry_frame,
                                       width=100,
                                       font=("Share Tech Mono", 14),
                                       fg_color="#2B2B2B",
                                       border_color="#00FF00",
                                       border_width=2,
                                       text_color="#00FF00")
                    entry.insert(0, f"{current_value:.2f}")
                    entry.pack(padx=10, pady=5)
                    
                    self.temp_setpoints[machine][param] = {
                        'entry': entry,
                        'min': min_val,
                        'max': max_val
                    }
            
            # Control buttons with enhanced styling
            button_frame = ctk.CTkFrame(machine_container, fg_color="#2B2B2B")
            button_frame.pack(fill="x", padx=15, pady=(5,15))
            
            reset_btn = ctk.CTkButton(button_frame,
                                    text="↺ Reset Values",
                                    font=("Exo 2", 12),
                                    fg_color="#555555",
                                    hover_color="#444444",
                                    width=120,
                                    corner_radius=6,
                                    command=lambda m=machine: self.reset_setpoints(m))
            reset_btn.pack(side="left", padx=15)
            
            save_btn = ctk.CTkButton(button_frame,
                                    text="💾 Save Changes",
                                    font=("Orbitron", 12, "bold"),
                                    fg_color="#008000",
                                    hover_color="#006400",
                                    width=150,
                                    corner_radius=6,
                                    command=lambda m=machine: self.save_setpoints(m))
            save_btn.pack(side="right", padx=15)
        
        return settings

    def reset_setpoints(self, machine):
        """Reset setpoint values to current values"""
        try:
            for param, data in self.temp_setpoints[machine].items():
                data['entry'].delete(0, 'end')
                data['entry'].insert(0, f"{self.setpoints[machine][param]:.1f}")
            
            messagebox.showinfo("Reset", f"Setpoint values for {machine} have been reset.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset setpoints: {str(e)}")

    def save_setpoints(self, machine):
        """Save new setpoint values for a machine"""
        try:
            # Validate and update setpoints
            new_setpoints = {}
            for param, data in self.temp_setpoints[machine].items():
                try:
                    value = float(data['entry'].get())
                    if value < data['min'] or value > data['max']:
                        messagebox.showerror("Invalid Value", 
                            f"Value for {param} must be between {data['min']} and {data['max']}")
                        return
                    new_setpoints[param] = value
                except ValueError:
                    messagebox.showerror("Invalid Input", 
                        f"Invalid value for {param}. Please enter a number.")
                    return
            
            # Update setpoints if all values are valid
            self.setpoints[machine].update(new_setpoints)
            messagebox.showinfo("Success", 
                f"✅ Setpoints for {machine} have been updated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save setpoints: {str(e)}")

    def show_dashboard(self):
        # Hide all views
        for view in self.views.values():
            view.pack_forget()
        # Show dashboard
        self.views['dashboard'].pack(fill="both", expand=True)

    def show_settings(self):
        # Hide all views
        for view in self.views.values():
            view.pack_forget()
        # Show settings
        self.views['settings'].pack(fill="both", expand=True)

    def show_statistics(self):
        # Hide all views
        for view in self.views.values():
            view.pack_forget()
        # Show statistics
        if 'statistics' not in self.views:
            self.views['statistics'] = self.create_statistics()
        self.views['statistics'].pack(fill="both", expand=True)

    def create_statistics(self):
        # Create statistics frame
        stats_frame = ctk.CTkFrame(self.scrollable_frame)
        
        # Title
        title_frame = ctk.CTkFrame(stats_frame, fg_color="#1E1E1E")
        title_frame.pack(fill="x", padx=20, pady=(20,30))
        
        title = ctk.CTkLabel(title_frame, text="📊 System Statistics",
                           font=("Orbitron", 28, "bold"),
                           text_color="#00FF00")
        title.pack(pady=20)
        
        # Create container for all machines
        for machine in ["Air Handling Unit", "Chiller", "Generator"]:
            machine_frame = ctk.CTkFrame(stats_frame, fg_color="#2B2B2B")
            machine_frame.pack(fill="x", padx=30, pady=15)
            
            # Machine header with icon
            header_frame = ctk.CTkFrame(machine_frame, fg_color="#1E1E1E")
            header_frame.pack(fill="x", padx=2, pady=2)
            
            icons = {
                "Air Handling Unit": "🌀",
                "Chiller": "❄️",
                "Generator": "⚡"
            }
            
            machine_title = ctk.CTkLabel(header_frame,
                                       text=f"{icons[machine]} {machine}",
                                       font=("Orbitron", 22, "bold"),
                                       text_color="#00FF00")
            machine_title.pack(pady=15)
            
            # Create grid for statistics displays
            stats_grid = ctk.CTkFrame(machine_frame, fg_color="#232323")
            stats_grid.pack(fill="x", padx=15, pady=15)
            stats_grid.grid_columnconfigure(0, weight=1)
            stats_grid.grid_columnconfigure(1, weight=1)
            
            # Left side: Fault Distribution Histogram
            hist_frame = ctk.CTkFrame(stats_grid, fg_color="#1A1A1A")
            hist_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            hist_title = ctk.CTkLabel(hist_frame,
                                    text="Fault Distribution",
                                    font=("Exo 2", 16, "bold"),
                                    text_color="#00FFFF")
            hist_title.pack(pady=5)
            
            # Create histogram
            self.trend_analyzer.create_fault_histogram(hist_frame, machine)
            
            # Right side: Fault Status Trend
            trend_frame = ctk.CTkFrame(stats_grid, fg_color="#1A1A1A")
            trend_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            
            trend_title = ctk.CTkLabel(trend_frame,
                                     text="Fault Status Trend",
                                     font=("Exo 2", 16, "bold"),
                                     text_color="#00FFFF")
            trend_title.pack(pady=5)
            
            # Create fault status trend
            self.trend_analyzer.create_fault_trend(trend_frame, machine)
        
        return stats_frame

    def update_setpoint(self, machine, param, value, label):
        """Update setpoint value and display"""
        self.setpoints[machine][param] = float(value)
        label.configure(text=f"{value:.1f}")

    def update_status(self, machine, data, prediction, probability):
        if not self.window.winfo_exists():
            return
            
        frame = self.machine_frames[machine]
        
        # Update status with LED-like indicator
        if prediction == 0:
            frame["status"].configure(text="● NORMAL OPERATION", text_color="#00FF00")
            frame["fault_type"].configure(text="System Healthy", text_color="#00FF00")
        else:
            frame["status"].configure(text="● FAULT DETECTED!", text_color="#FF0000")
            fault_name = self.fault_types[machine][prediction]
            frame["fault_type"].configure(
                text=f"Fault: {fault_name}\nConfidence: {probability:.2f}%",
                text_color="#FF0000"
            )
        
        # Get or create the main parameters container
        if not hasattr(frame["params"], 'param_widgets'):
            # Initialize parameter display structure
            frame["params"].param_widgets = {}
            
            # Create main container
            params_container = ctk.CTkFrame(frame["params"].master, fg_color="#1A1A1A")
            params_container.pack(fill="both", expand=True, padx=10, pady=5)
            frame["params"].param_widgets['container'] = params_container
            
            # Create header
            header_frame = ctk.CTkFrame(params_container, fg_color="#232323")
            header_frame.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(header_frame, text="Parameter",
                        font=("Orbitron", 12, "bold"),
                        text_color="#00FF00").pack(side="left", padx=10)
            ctk.CTkLabel(header_frame, text="Current",
                        font=("DSEG14 Classic", 12, "bold"),
                        text_color="#00FFFF").pack(side="left", padx=10, expand=True)
            ctk.CTkLabel(header_frame, text="Setpoint",
                        font=("Share Tech Mono", 12, "bold"),
                        text_color="#FFA500").pack(side="right", padx=10)
            
            # Create scrollable area for parameters
            scroll_frame = ctk.CTkScrollableFrame(params_container)
            scroll_frame.pack(fill="both", expand=True)
            frame["params"].param_widgets['scroll_frame'] = scroll_frame
        
        # Get references to existing widgets
        container = frame["params"].param_widgets['container']
        scroll_frame = frame["params"].param_widgets['scroll_frame']
        
        # Create or update parameter rows
        for idx, (k, v) in enumerate(data.items()):
            if k not in frame["params"].param_widgets:
                # Create new parameter row if it doesn't exist
                param_container = ctk.CTkFrame(scroll_frame, fg_color="#2B2B2B")
                param_container.pack(fill="x", padx=5, pady=2)
                
                # Parameter name
                name_label = ctk.CTkLabel(param_container,
                                        text=k.replace('_', ' ').title(),
                                        font=("Exo 2", 11),
                                        text_color="#FFFFFF")
                name_label.pack(side="left", padx=10)
                
                # Current value
                current_label = ctk.CTkLabel(param_container,
                                           font=("DSEG14 Classic", 14))
                current_label.pack(side="left", padx=10, expand=True)
                
                # Trend indicator
                trend_label = ctk.CTkLabel(param_container,
                                         font=("Arial", 14, "bold"))
                trend_label.pack(side="right", padx=2)
                
                # Setpoint value
                setpoint_label = ctk.CTkLabel(param_container,
                                            font=("Share Tech Mono", 12))
                setpoint_label.pack(side="right", padx=10)
                
                # Store references
                frame["params"].param_widgets[k] = {
                    'container': param_container,
                    'name': name_label,
                    'current': current_label,
                    'trend': trend_label,
                    'setpoint': setpoint_label
                }
            
            # Update values
            widget_set = frame["params"].param_widgets[k]
            
            if k in self.setpoints.get(machine, {}):
                current = float(v)
                setpoint = self.setpoints[machine][k]
                deviation = abs(current - setpoint)
                
                # Update current value color
                if deviation < (setpoint * 0.05):
                    value_color = "#00FF00"
                elif deviation < (setpoint * 0.1):
                    value_color = "#FFA500"
                else:
                    value_color = "#FF0000"
                
                widget_set['current'].configure(
                    text=f"{current:.2f}",
                    text_color=value_color
                )
                
                # Update setpoint display
                widget_set['setpoint'].configure(
                    text=f"{setpoint:.2f}",
                    text_color="#FFA500"
                )
                
                # Update trend indicator
                trend_indicator = "↑" if current > setpoint else "↓" if current < setpoint else "="
                trend_color = "#FF0000" if trend_indicator != "=" else "#00FF00"
                widget_set['trend'].configure(
                    text=trend_indicator,
                    text_color=trend_color
                )
                
                # Show all elements
                widget_set['container'].pack(fill="x", padx=5, pady=2)
                widget_set['setpoint'].pack(side="right", padx=10)
                widget_set['trend'].pack(side="right", padx=2)
            else:
                # For non-setpoint parameters
                widget_set['current'].configure(
                    text=f"{float(v):.2f}",
                    text_color="#888888"
                )
                widget_set['setpoint'].pack_forget()
                widget_set['trend'].pack_forget()
        
        # Update trends
        self.trend_analyzer.update_trends(machine, prediction, data=data)

    def continuous_monitoring(self):
        while self.monitoring_active:
            try:
                # Generate and predict for each machine
                machine_types = {
                    "Air Handling Unit": "AHU",
                    "Chiller": "CHILLER",
                    "Generator": "GENERATOR"
                }
                
                for machine, device_type in machine_types.items():
                    try:
                        # Generate data
                        data = generate_random_fault_data(device_type)
                        # print(f"\nData generated for {machine}:")
                        # print(data.head())
                        
                        # Convert data to list and remove timestamp if present
                        features_dict = data.iloc[0].to_dict()
                        if 'timestamp' in features_dict:
                            del features_dict['timestamp']
            
            # Make prediction
                        features_df = pd.DataFrame([features_dict])
                        prediction = self.models[machine].predict(features_df)[0]
                        probability = np.max(self.models[machine].predict_proba(features_df)) * 100
                        
                        # Update UI
                        self.window.after(0, self.update_status, machine, 
                                        features_dict, prediction, probability)
                        
                    except Exception as e:
                        print(f"Error processing {machine}: {str(e)}")
                        print(f"Data shape: {data.shape if 'data' in locals() else 'No data'}")
                        print(f"Data types: {data.dtypes if 'data' in locals() else 'No data'}")
                        self.window.after(0, self.update_error_status, machine, str(e))
                
                time.sleep(5)  # Wait 10 seconds before next update
            
            except Exception as e:
                    print(f"Monitoring error: {str(e)}")
                    time.sleep(1)  # Wait before retrying

    def update_error_status(self, machine, error_msg):
        """Handle error states in the UI"""
        if not self.window.winfo_exists():
            return
        
        frame = self.machine_frames[machine]
        frame["status"].configure(text="ERROR", text_color="#FFA500")
        frame["fault_type"].configure(text=f"Error: {error_msg}", text_color="#FFA500")

    def on_closing(self):
        self.monitoring_active = False
        self.window.destroy()

if __name__ == "__main__":
    app = FaultDetectionApp()