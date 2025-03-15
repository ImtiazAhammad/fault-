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
            
            # Parameters display
            params_frame = ctk.CTkFrame(machine_container, fg_color="#1B1B1B")
            params_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            params_title = ctk.CTkLabel(params_frame, text="PARAMETERS",
                                      font=("Roboto", 16, "bold"),
                                      text_color="#00FF00")
            params_title.pack(pady=5)
            
            # Live values display
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
                           font=("Roboto", 28, "bold"),
                           text_color="#00FF00")
        title.pack(pady=20)
        
        subtitle = ctk.CTkLabel(title_frame, 
                              text="Configure operational parameters for all devices",
                              font=("Roboto", 14),
                              text_color="#AAAAAA")
        subtitle.pack(pady=(0,10))
        
        # Dictionary to store temporary setpoint values
        self.temp_setpoints = {}
        
        # Create sections for each machine
        for machine in ["Air Handling Unit", "Chiller", "Generator"]:
            # Machine container with shadow effect
            machine_container = ctk.CTkFrame(settings, fg_color="#2B2B2B")
            machine_container.pack(fill="x", padx=30, pady=15)
            
            # Header frame with icon
            header_frame = ctk.CTkFrame(machine_container, fg_color="#1E1E1E")
            header_frame.pack(fill="x", padx=2, pady=2)
            
            # Machine icon mapping
            icons = {
                "Air Handling Unit": "🌀",
                "Chiller": "❄️",
                "Generator": "⚡"
            }
            
            # Machine title with icon
            machine_title = ctk.CTkLabel(header_frame, 
                                       text=f"{icons[machine]} {machine}",
                                       font=("Roboto", 22, "bold"),
                                       text_color="#00FF00")
            machine_title.pack(pady=15)
            
            # Initialize temporary setpoints for this machine
            self.temp_setpoints[machine] = {}
            
            # Parameters table
            param_frame = ctk.CTkFrame(machine_container, fg_color="#232323")
            param_frame.pack(fill="x", padx=15, pady=15)
            
            # Table headers
            headers = ["Parameter", "Min", "Current", "Max", "New Value"]
            header_colors = ["#00FF00", "#FFA500", "#00FFFF", "#FFA500", "#00FF00"]
            
            for col, (header, color) in enumerate(zip(headers, header_colors)):
                label = ctk.CTkLabel(param_frame, 
                                   text=header,
                                   font=("Roboto", 14, "bold"),
                                   text_color=color)
                label.grid(row=0, column=col, padx=15, pady=(10,5), sticky="w")
            
            # Add parameters
            if machine in self.setpoint_ranges:
                for idx, (param, (min_val, max_val)) in enumerate(self.setpoint_ranges[machine].items(), 1):
                    # Parameter name with custom style
                    param_name = ctk.CTkLabel(param_frame,
                                            text=param.replace('_', ' ').title(),
                                            font=("Roboto", 14),
                                            text_color="#FFFFFF")
                    param_name.grid(row=idx, column=0, padx=15, pady=10, sticky="w")
                    
                    # Min value
                    min_label = ctk.CTkLabel(param_frame,
                                           text=f"{min_val:.1f}",
                                           font=("Roboto", 12),
                                           text_color="#FFA500")
                    min_label.grid(row=idx, column=1, padx=15, pady=10)
                    
                    # Current value with highlight
                    current_frame = ctk.CTkFrame(param_frame, fg_color="#1E1E1E")
                    current_frame.grid(row=idx, column=2, padx=15, pady=10)
                    
                    current_label = ctk.CTkLabel(current_frame,
                                               text=f"{self.setpoints[machine][param]:.1f}",
                                               font=("Roboto", 12),
                                               text_color="#00FFFF")
                    current_label.pack(padx=10, pady=5)
                    
                    # Max value
                    max_label = ctk.CTkLabel(param_frame,
                                           text=f"{max_val:.1f}",
                                           font=("Roboto", 12),
                                           text_color="#FFA500")
                    max_label.grid(row=idx, column=3, padx=15, pady=10)
                    
                    # Entry for new value with custom style
                    entry_frame = ctk.CTkFrame(param_frame, fg_color="#1E1E1E")
                    entry_frame.grid(row=idx, column=4, padx=15, pady=10)
                    
                    entry = ctk.CTkEntry(entry_frame,
                                       width=100,
                                       font=("Roboto", 12),
                                       fg_color="#2B2B2B",
                                       border_color="#00FF00",
                                       text_color="#FFFFFF")
                    entry.insert(0, f"{self.setpoints[machine][param]:.1f}")
                    entry.pack(padx=10, pady=5)
                    
                    # Store reference to entry widget
                    self.temp_setpoints[machine][param] = {
                        'entry': entry,
                        'min': min_val,
                        'max': max_val
                    }
            
            # Control buttons frame
            button_frame = ctk.CTkFrame(machine_container, fg_color="#2B2B2B")
            button_frame.pack(fill="x", padx=15, pady=(5,15))
            
            # Reset button
            reset_btn = ctk.CTkButton(button_frame,
                                    text="↺ Reset",
                                    font=("Roboto", 12),
                                    fg_color="#555555",
                                    hover_color="#444444",
                                    width=100,
                                    command=lambda m=machine: self.reset_setpoints(m))
            reset_btn.pack(side="left", padx=15)
            
            # Save button with icon
            save_btn = ctk.CTkButton(button_frame,
                                    text="💾 Save Changes",
                                    font=("Roboto", 12, "bold"),
                                    fg_color="#008000",
                                    hover_color="#006400",
                                    width=150,
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
        
        # Update parameter values with comparison to setpoints
        params_text = ""
        for k, v in data.items():
            if k in self.setpoints.get(machine, {}):
                setpoint = self.setpoints[machine][k]
                current = float(v)
                deviation = abs(current - setpoint)
                color = "#00FF00" if deviation < (setpoint * 0.1) else "#FFA500"
                params_text += f"{k.replace('_', ' ').title()}:\n"
                params_text += f"Current: {current:.2f} | Setpoint: {setpoint:.2f}\n"
            else:
                params_text += f"{k.replace('_', ' ').title()}: {v:.2f}\n"
        
        frame["params"].configure(text=params_text)
        
        # Update trends using trend analyzer with parameter data
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