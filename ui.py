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
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FaultDetectionApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Industrial Fault Detection System")
        self.window.geometry("1500x900")
        
        # Add prediction history storage
        self.prediction_history = []
        
        # Update setpoint ranges for all parameters
        self.setpoint_ranges = {
            "Air Handling Unit": {
                "supply_air_temp": (15, 25),
                "return_air_temp": (20, 28),
                "room_air_temp": (20, 26),
                "return_air_humidity": (40, 60),
                "fan_speed": (30, 100),
                "cooling_state": (0, 1),
                "electric_reheat_state": (0, 1),
                "filter_dp": (50, 300),
                "cool_water_valve": (0, 100),
                "hot_water_valve": (0, 100),
                "outside_air_damper": (20, 80)
            },
            "Chiller": {
                "chill_water_outlet": (4, 12),
                "chill_water_inlet": (8, 15),
                "condenser_pressure": (3, 6),
                "differential_pressure": (10, 20),
                "supply_water_temp": (40, 50),
                "cooling_tower_fan": (0, 1),
                "condenser_pump": (0, 1),
                "return_condenser_valve": (0, 1),
                "flow_switch": (0, 1)
            },
            "Generator": {
                "oil_pressure": (1.5, 2.5),
                "coolant_temp": (75, 95),
                "battery_voltage": (23.5, 24.5),
                "phase1_voltage": (220, 240),
                "phase2_voltage": (220, 240),
                "phase3_voltage": (220, 240),
                "frequency": (49.5, 50.5),
                "load_percent": (40, 80),
                "run_hours": (0, 20000),
                "fuel_level": (30, 100)
            }
        }
        
        # Initialize all setpoints with mid-range values
        self.setpoints = {}
        for machine, params in self.setpoint_ranges.items():
            self.setpoints[machine] = {
                param: (min_val + max_val) / 2 if isinstance(min_val, (int, float)) else min_val
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
        self.create_nav_button("Report", self.show_report)
        
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

    def show_report(self):
        # Hide all views
        for view in self.views.values():
            view.pack_forget()
        # Show report
        if 'report' not in self.views:
            self.views['report'] = self.create_report()
        self.views['report'].pack(fill="both", expand=True)

    def create_report(self):
        # Create report frame
        report_frame = ctk.CTkFrame(self.scrollable_frame)
        
        # Title and controls frame
        control_frame = ctk.CTkFrame(report_frame, fg_color="#1E1E1E")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(control_frame, text="📊 Fault Prediction Report",
                   font=("Orbitron", 24, "bold"),
                   text_color="#00FF00").pack(side="left", padx=10)

        # Add export button
        export_btn = ctk.CTkButton(control_frame, text="📤 Export CSV",
                                 command=self.export_report_csv,
                                 fg_color="#2B579A", hover_color="#1E3D6B")
        export_btn.pack(side="right", padx=5)

        # Add search/filter controls
        filter_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        filter_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(filter_frame, text="🔍 Search:").pack(side="left")
        self.search_entry = ctk.CTkEntry(filter_frame, width=200)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.update_report_display())

        self.filter_var = ctk.StringVar(value="All")
        filter_menu = ctk.CTkOptionMenu(filter_frame, 
                                      values=["All", "Normal", "Fault"],
                                      variable=self.filter_var,
                                      command=lambda _: self.update_report_display())
        filter_menu.pack(side="left", padx=5)

        # Create visualization container
        vis_frame = ctk.CTkFrame(report_frame, fg_color="#1B1B1B")
        vis_frame.pack(fill="x", padx=20, pady=10)
        
        # Create fault distribution pie chart
        self.create_report_visualization(vis_frame)

        # Create scrollable table
        self.table_frame = ctk.CTkScrollableFrame(report_frame, fg_color="#1B1B1B")
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Initial table setup
        self.update_report_display()
        return report_frame

    def create_report_visualization(self, parent_frame):
        # Create visualization frame with matplotlib figure
        fig = Figure(figsize=(8, 3), facecolor='#1B1B1B')
        self.report_ax = fig.add_subplot(111)
        self.report_ax.set_facecolor('#1B1B1B')
        
        # Style the axes
        self.report_ax.tick_params(colors='white')
        for spine in self.report_ax.spines.values():
            spine.set_color('white')

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", expand=True)
        self.report_canvas = canvas

    def update_report_visualization(self):
        self.report_ax.clear()
        
        # Get fault counts
        fault_counts = {"Normal": 0, "Fault": 0}
        for entry in self.prediction_history:
            if entry['prediction'] == 0:
                fault_counts["Normal"] += 1
            else:
                fault_counts["Fault"] += 1

        # Create pie chart
        labels = ['Normal Operation', 'Fault Detected']
        sizes = [fault_counts["Normal"], fault_counts["Fault"]]
        colors = ['#00FF00', '#FF0000']
        explode = (0.1, 0)  # explode 1st slice

        self.report_ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                         autopct='%1.1f%%', shadow=True, startangle=140,
                         textprops={'color':'white'})
        self.report_ax.axis('equal')  # Equal aspect ratio
        self.report_canvas.draw()

    def export_report_csv(self):
        try:
            df = pd.DataFrame(self.prediction_history)
            df['timestamp'] = df['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
            df['parameters'] = df['parameters'].apply(lambda x: str(x))
            df.to_csv('fault_report.csv', index=False)
            messagebox.showinfo("Export Successful", 
                              "Report exported to fault_report.csv")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def update_report_display(self):
        # Clear existing entries
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Create filtered list
        search_term = self.search_entry.get().lower()
        filter_type = self.filter_var.get()

        filtered = [
            entry for entry in self.prediction_history
            if (search_term in entry['machine'].lower() or 
                search_term in entry['fault_type'].lower() or
                any(search_term in k.lower() for k in entry['parameters'].keys()))
            and (filter_type == "All" or 
                (filter_type == "Normal" and entry['prediction'] == 0) or
                (filter_type == "Fault" and entry['prediction'] != 0))
        ]

        # Create header row
        headers = [
            ("Timestamp", 1), ("Machine", 1), 
            ("Fault Type", 2), ("Probability", 1), 
            ("Parameters", 3), ("Details", 1)
        ]
        
        header_row = ctk.CTkFrame(self.table_frame, fg_color="#2B2B2B")
        header_row.pack(fill="x", pady=(0,5))
        
        for col, (text, weight) in enumerate(headers):
            ctk.CTkLabel(header_row, text=text,
                        font=("Roboto", 14, "bold"),
                        text_color="#00FF00",
                        width=150*weight).grid(row=0, column=col, padx=2, sticky="w")
            header_row.grid_columnconfigure(col, weight=weight)

        # Add filtered entries
        for entry in filtered:
            row = ctk.CTkFrame(self.table_frame, fg_color="#2B2B2B")
            row.pack(fill="x", pady=2)

            # Existing columns
            ctk.CTkLabel(row, text=entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                       font=("Consolas", 12), width=150).grid(row=0, column=0, padx=5, sticky="w")
            
            ctk.CTkLabel(row, text=entry['machine'],
                       font=("Roboto", 12), width=150).grid(row=0, column=1, padx=5, sticky="w")

            fault_color = "#FF0000" if entry['prediction'] != 0 else "#00FF00"
            ctk.CTkLabel(row, text=entry['fault_type'],
                       font=("Roboto", 12, "bold"),
                       text_color=fault_color, width=300).grid(row=0, column=2, padx=5, sticky="w")

            ctk.CTkLabel(row, text=f"{entry['probability']:.1f}%",
                       font=("Roboto Mono", 12),
                       text_color="#FFA500", width=150).grid(row=0, column=3, padx=5, sticky="w")

            params_text = "\n".join([f"{k}: {v:.2f}" for k,v in entry['parameters'].items()][:3])
            ctk.CTkLabel(row, text=params_text,
                       font=("Consolas", 11),
                       text_color="#AAAAAA", width=450).grid(row=0, column=4, padx=5, sticky="w")

            # Add detail button
            detail_btn = ctk.CTkButton(row, text="🔍 Details", width=80,
                                     command=lambda e=entry: self.show_detail_view(e))
            detail_btn.grid(row=0, column=5, padx=5, sticky="e")

            # Configure columns
            for col in range(6):
                row.grid_columnconfigure(col, weight=[1,1,2,1,3,1][col])

        # Update visualization
        self.update_report_visualization()

    def show_detail_view(self, entry):
        detail_window = ctk.CTkToplevel(self.window)
        detail_window.title(f"Detail View - {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        detail_window.geometry("600x400")

        # Create parameter table
        table_frame = ctk.CTkScrollableFrame(detail_window)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create headers
        header_row = ctk.CTkFrame(table_frame)
        header_row.pack(fill="x")
        ctk.CTkLabel(header_row, text="Parameter", width=250, 
                   font=("Roboto", 12, "bold")).pack(side="left")
        ctk.CTkLabel(header_row, text="Value", width=150,
                   font=("Roboto", 12, "bold")).pack(side="left")

        # Add parameters
        for param, value in entry['parameters'].items():
            row = ctk.CTkFrame(table_frame)
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=param.replace('_', ' ').title(), 
                       width=250).pack(side="left")
            ctk.CTkLabel(row, text=f"{value:.2f}", 
                       width=150).pack(side="left")

        # Add close button
        ctk.CTkButton(detail_window, text="Close",
                    command=detail_window.destroy).pack(pady=10)

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
            
        # Store prediction in history
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'machine': machine,
            'prediction': prediction,
            'probability': probability,
            'fault_type': self.fault_types[machine][prediction],
            'parameters': {k: float(v) for k,v in data.items() if isinstance(v, (int, float))}
        })
        
        # Keep only last 100 entries
        if len(self.prediction_history) > 100:
            self.prediction_history = self.prediction_history[-100:]
        
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
            
            # Create header with grid layout
            header_frame = ctk.CTkFrame(params_container, fg_color="#232323")
            header_frame.pack(fill="x", padx=5, pady=5)
            
            # Configure grid columns
            header_frame.grid_columnconfigure(0, weight=3, uniform="group1")  # Parameter
            header_frame.grid_columnconfigure(1, weight=2, uniform="group1")  # Current
            header_frame.grid_columnconfigure(2, weight=2, uniform="group1")  # Setpoint
            header_frame.grid_columnconfigure(3, weight=1, uniform="group1")  # Trend
            
            # Create headers
            headers = [
                ("Parameter", "#00FF00", "Orbitron", 12, "w"),
                ("Current Value", "#00FFFF", "DSEG14 Classic", 12, "center"),
                ("Setpoint", "#FFA500", "Share Tech Mono", 12, "center"),
                ("Trend", "#FFFFFF", "Arial", 12, "center")
            ]
            
            for col, (text, color, font, size, anchor) in enumerate(headers):
                ctk.CTkLabel(header_frame, text=text,
                            text_color=color,
                            font=(font, size, "bold"),
                            anchor=anchor
                            ).grid(row=0, column=col, padx=5, pady=2, sticky="nsew")
            
            # Create scrollable area for parameters
            scroll_frame = ctk.CTkScrollableFrame(params_container)
            scroll_frame.pack(fill="both", expand=True)
            frame["params"].param_widgets['scroll_frame'] = scroll_frame
            frame["params"].param_widgets['rows'] = {}

        # Get references to existing widgets
        scroll_frame = frame["params"].param_widgets['scroll_frame']
        rows = frame["params"].param_widgets['rows']
        
        # Create/update parameter rows
        for k, v in data.items():
            if k not in rows:
                # Create new row if it doesn't exist
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="#2B2B2B")
                row_frame.grid_columnconfigure(0, weight=3, uniform="group1")
                row_frame.grid_columnconfigure(1, weight=2, uniform="group1")
                row_frame.grid_columnconfigure(2, weight=2, uniform="group1")
                row_frame.grid_columnconfigure(3, weight=1, uniform="group1")
                
                # Parameter name (left-aligned)
                name_label = ctk.CTkLabel(row_frame,
                                        text=k.replace('_', ' ').title(),
                                        font=("Exo 2", 11),
                                        text_color="#FFFFFF",
                                        anchor="w")
                name_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
                
                # Current value (centered)
                current_label = ctk.CTkLabel(row_frame,
                                           text="",
                                           font=("DSEG14 Classic", 14),
                                           anchor="center")
                current_label.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")
                
                # Setpoint and trend (centered)
                setpoint_label = ctk.CTkLabel(row_frame,
                                            text="",
                                            font=("Share Tech Mono", 12),
                                            anchor="center")
                setpoint_label.grid(row=0, column=2, padx=5, pady=2, sticky="nsew")
                
                trend_label = ctk.CTkLabel(row_frame,
                                         text="",
                                         font=("Arial", 14, "bold"),
                                         anchor="center")
                trend_label.grid(row=0, column=3, padx=5, pady=2, sticky="nsew")
                
                row_frame.pack(fill="x", pady=1)
                rows[k] = {
                    'frame': row_frame,
                    'current': current_label,
                    'setpoint': setpoint_label,
                    'trend': trend_label
                }
            
            # Update values and colors
            current_value = float(v)
            row_data = rows[k]
            
            # Update current value
            if k in self.setpoints.get(machine, {}):
                setpoint = self.setpoints[machine][k]
                deviation = abs(current_value - setpoint)
                
                # Determine color based on deviation
                if deviation < (setpoint * 0.05):
                    value_color = "#00FF00"
                elif deviation < (setpoint * 0.1):
                    value_color = "#FFA500"
                else:
                    value_color = "#FF0000"
                
                # Update current value display
                row_data['current'].configure(
                    text=f"{current_value:.2f}",
                    text_color=value_color
                )
                
                # Update setpoint display
                row_data['setpoint'].configure(
                    text=f"{setpoint:.2f}",
                    text_color="#FFA500"
                )
                
                # Update trend indicator
                trend_indicator = "↑" if current_value > setpoint else "↓" if current_value < setpoint else "="
                trend_color = "#FF0000" if trend_indicator != "=" else "#00FF00"
                row_data['trend'].configure(
                    text=trend_indicator,
                    text_color=trend_color
                )
                
                # Show all elements
                row_data['setpoint'].grid()
                row_data['trend'].grid()
            else:
                # For non-setpoint parameters
                row_data['current'].configure(
                    text=f"{current_value:.2f}",
                    text_color="#888888"
                )
                row_data['setpoint'].grid_remove()
                row_data['trend'].grid_remove()
        
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
                        
                        # Filter out setpoint parameters for model prediction
                        features_dict = {
                            k: v for k, v in data.iloc[0].to_dict().items() 
                            if not k.endswith('_setpoint') and k != 'timestamp'
                        }
                        
                        # Make prediction with original parameters only
                        features_df = pd.DataFrame([features_dict])
                        prediction = self.models[machine].predict(features_df)[0]
                        probability = np.max(self.models[machine].predict_proba(features_df)) * 100
                        
                        # Update UI with full data (including setpoints)
                        self.window.after(0, self.update_status, machine, 
                                        data.iloc[0].to_dict(), prediction, probability)
                        
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