import requests
import time
from data_genarator import generate_device_data
import pandas as pd
import numpy as np
from datetime import datetime

# API endpoints (local FastAPI server)
API_ENDPOINTS = {
    "AHU": "http://localhost:8000/predict/ahu",
    "Chiller": "http://localhost:8000/predict/chiller",
    "Generator": "http://localhost:8000/predict/generator"
}

def generate_random_fault_data(device_type):
    """
    Generate a single record with possible fault
    """
    try:
        if device_type == "AHU":
            data = {
                'supply_air_temp': np.random.normal(18, 1),
                'supply_air_setpoint': 18.0,
                'return_air_temp': np.random.normal(23, 1),
                'return_air_setpoint': 24.0,
                'room_air_temp': np.random.normal(23, 1.5),
                'room_air_setpoint': 23.0,
                'return_air_humidity': np.random.uniform(40, 60),
                'return_air_humidity_setpoint': 50.0,
                'fan_speed': np.random.randint(40, 100),
                'fan_speed_setpoint': 75.0,
                'cooling_state': np.random.choice([0, 1]),
                'cooling_state_setpoint': 0.5,
                'electric_reheat_state': np.random.choice([0, 1]),
                'electric_reheat_state_setpoint': 0.5,
                'filter_dp': np.random.uniform(50, 250),
                'filter_dp_setpoint': 150.0,
                'cool_water_valve': np.random.uniform(0, 100),
                'cool_water_valve_setpoint': 50.0,
                'hot_water_valve': np.random.uniform(0, 100),
                'hot_water_valve_setpoint': 50.0,
                'outside_air_damper': np.random.uniform(20, 80),
                'outside_air_damper_setpoint': 50.0
            }
            
            # AHU Fault Injection (20% chance)
            if np.random.random() < 0.2:
                fault_type = np.random.randint(1, 5)
                if fault_type == 1:  # Fan Fault
                    data['fan_speed'] = 0
                    data['supply_air_temp'] += 5
                elif fault_type == 2:  # Filter Dirty
                    data['filter_dp'] = np.random.uniform(350, 500)
                    data['fan_speed'] *= 0.6
                elif fault_type == 3:  # Coil Fault
                    data['cool_water_valve'] = 0
                    data['supply_air_temp'] += 3
                elif fault_type == 4:  # Damper Fault
                    data['outside_air_damper'] = 100 if np.random.random() > 0.5 else 0
        
        elif device_type == "CHILLER":
            data = {
                'chill_water_outlet': float(np.random.normal(6, 0.5)),
                'chill_water_outlet_setpoint': 6.0,
                'chill_water_inlet': float(np.random.normal(10, 1)),
                'chill_water_inlet_setpoint': 10.0,
                'condenser_pressure': float(np.random.normal(4.5, 0.3)),
                'condenser_pressure_setpoint': 4.5,
                'differential_pressure': float(np.random.normal(15, 2)),
                'differential_pressure_setpoint': 15.0,
                'supply_water_temp': float(np.random.normal(45, 1.5)),
                'supply_water_temp_setpoint': 45.0,
                'cooling_tower_fan': int(np.random.choice([0, 1])),
                'cooling_tower_fan_setpoint': 0.5,
                'condenser_pump': int(np.random.choice([0, 1])),
                'condenser_pump_setpoint': 0.5,
                'return_condenser_valve': int(np.random.choice([0, 1])),
                'return_condenser_valve_setpoint': 0.5,
                'flow_switch': int(np.random.choice([0, 1])),
                'flow_switch_setpoint': 0.5
            }
            
            # Chiller Fault Injection (20% chance)
            if np.random.random() < 0.2:
                fault_type = np.random.randint(1, 5)
                if fault_type == 1:  # Low Refrigerant
                    data['condenser_pressure'] = 2.5
                    data['chill_water_outlet'] += 2
                elif fault_type == 2:  # Condenser Fault
                    data['differential_pressure'] = 25
                    data['condenser_pressure'] += 1.5
                elif fault_type == 3:  # Flow Switch Fault
                    data['flow_switch'] = 0
                    data['chill_water_inlet'] += 4
                elif fault_type == 4:  # Pump Failure
                    data['condenser_pump'] = 0
                    data['supply_water_temp'] += 5
        
        elif device_type == "GENERATOR":
            data = {
                'oil_pressure': float(np.random.normal(2.0, 0.2)),
                'oil_pressure_setpoint': 2.0,
                'coolant_temp': float(np.random.normal(85, 5)),
                'coolant_temp_setpoint': 85.0,
                'battery_voltage': float(np.random.normal(24, 0.3)),
                'battery_voltage_setpoint': 24.0,
                'phase1_voltage': float(np.random.normal(230, 3)),
                'phase1_voltage_setpoint': 230.0,
                'phase2_voltage': float(np.random.normal(230, 3)),
                'phase2_voltage_setpoint': 230.0,
                'phase3_voltage': float(np.random.normal(230, 3)),
                'phase3_voltage_setpoint': 230.0,
                'frequency': float(np.random.normal(50, 0.1)),
                'frequency_setpoint': 50.0,
                'load_percent': float(np.random.uniform(40, 80)),
                'load_percent_setpoint': 60.0,
                'run_hours': int(np.random.randint(0, 20000)),
                'run_hours_setpoint': 10000.0,
                'fuel_level': float(np.random.uniform(30, 100)),
                'fuel_level_setpoint': 65.0
            }
            
            # Generator Fault Injection (20% chance)
            if np.random.random() < 0.2:
                fault_type = np.random.randint(1, 5)
                if fault_type == 1:  # Low Oil Pressure
                    data['oil_pressure'] = 0.8
                    data['coolant_temp'] += 10
                elif fault_type == 2:  # Overheating
                    data['coolant_temp'] = 125
                    data['oil_pressure'] -= 0.5
                elif fault_type == 3:  # Voltage Imbalance
                    data['phase1_voltage'] = 210
                    data['phase2_voltage'] = 245
                    data['frequency'] = 49
                elif fault_type == 4:  # Fuel System Fault
                    data['fuel_level'] = 0
                    data['load_percent'] = 0
        
        else:
            raise ValueError(f"Unknown device type: {device_type}")
        
        # Create DataFrame with explicit type conversion
        df = pd.DataFrame([data])
        print(f"Generated data for {device_type}:")
        print(df.dtypes)
        return df
    
    except Exception as e:
        print(f"Error generating data for {device_type}: {str(e)}")
        raise

def send_device_data(device_type, data):
    """
    Send data to respective API endpoint and get prediction
    """
    try:
        response = requests.post(
            API_ENDPOINTS[device_type],
            json=data.to_dict(orient='records')[0]
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n{device_type} Prediction:")
            print(f"Fault Type: {result['fault_type']}")
            print(f"Probability: {result['probability']:.2f}")
            print(f"Data: {data.to_dict(orient='records')[0]}")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error sending {device_type} data: {str(e)}")

def main():
    print("Starting data sender...")
    while True:
        for device_type in ["AHU", "CHILLER", "GENERATOR"]:
            try:
                data = generate_random_fault_data(device_type)
                print(f"\n{device_type} Data Generated:")
                print(data.to_dict(orient='records')[0])
                send_device_data(device_type, data)
            except Exception as e:
                print(f"Error with {device_type}: {str(e)}")
        
        print("\n" + "="*50 + "\n")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping data sender...") 