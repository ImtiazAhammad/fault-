import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_device_data(device_type, num_samples=10000):
    np.random.seed(42)
    base_params = {'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(num_samples)]}
    
    if device_type == "AHU":
        data = {
            # AHU Parameters from Client List
            'supply_air_temp': np.random.normal(18, 1, num_samples),
            'return_air_temp': np.random.normal(23, 1, num_samples),
            'room_air_temp': np.random.normal(23, 1.5, num_samples),
            'return_air_humidity': np.random.uniform(40, 60, num_samples),
            'fan_speed': np.random.randint(40, 100, num_samples),
            'cooling_state': np.random.choice([0, 1], num_samples, p=[0.7, 0.3]),
            'electric_reheat_state': np.random.choice([0, 1], num_samples, p=[0.9, 0.1]),
            'filter_dp': np.random.uniform(50, 250, num_samples),
            'cool_water_valve': np.random.uniform(0, 100, num_samples),
            'hot_water_valve': np.random.uniform(0, 100, num_samples),
            'outside_air_damper': np.random.uniform(20, 80, num_samples),
            'supply_air_setpoint': np.full(num_samples, 18),
            'fault_type': np.zeros(num_samples, dtype=int)
        }
        
        # AHU Fault Injection (Client's Thresholds)
        fault_samples = 5000
        faults = {
            1: {'name': 'Fan Fault', 'conditions': lambda d, i: (
                d['fan_speed'][i] < 10,
                {'fan_speed': 0, 'supply_air_temp': d['supply_air_temp'][i] + 5}
            )},
            2: {'name': 'Filter Dirty', 'conditions': lambda d, i: (
                d['filter_dp'][i] > 300,
                {'filter_dp': np.random.uniform(350, 500), 'fan_speed': d['fan_speed'][i] * 0.6}
            )},
            3: {'name': 'Coil Fault', 'conditions': lambda d, i: (
                d['cooling_state'][i] == 1 and d['supply_air_temp'][i] > 20,
                {'cool_water_valve': 0, 'supply_air_temp': d['supply_air_temp'][i] + 3}
            )},
            4: {'name': 'Damper Fault', 'conditions': lambda d, i: (
                d['outside_air_damper'][i] in [0, 100],
                {'outside_air_damper': 100 if np.random.rand() > 0.5 else 0}
            )}
        }
        
        # Inject faults with balanced classes
        for fault_id in faults:
            indices = np.random.choice(num_samples, fault_samples, replace=False)
            data['fault_type'][indices] = fault_id
            for i in indices:
                condition, updates = faults[fault_id]['conditions'](data, i)
                if condition:
                    for k, v in updates.items():
                        data[k][i] = v

    elif device_type == "Chiller":
        data = {
            # Chiller Parameters from Client List
            'chill_water_outlet': np.random.normal(6, 0.5, num_samples),
            'chill_water_inlet': np.random.normal(10, 1, num_samples),
            'condenser_pressure': np.random.normal(4.5, 0.3, num_samples),
            'differential_pressure': np.random.normal(15, 2, num_samples),
            'supply_water_temp': np.random.normal(45, 1.5, num_samples),
            'cooling_tower_fan': np.random.choice([0, 1], num_samples, p=[0.3, 0.7]),
            'condenser_pump': np.random.choice([0, 1], num_samples, p=[0.2, 0.8]),
            'return_condenser_valve': np.random.choice([0, 1], num_samples, p=[0.1, 0.9]),
            'flow_switch': np.random.choice([0, 1], num_samples, p=[0.95, 0.05]),
            'fault_type': np.zeros(num_samples, dtype=int)
        }
        
        # Chiller Fault Injection (Client's Thresholds)
        fault_samples = 5000
        faults = {
            1: {'name': 'Low Refrigerant', 'conditions': lambda d, i: (
                d['condenser_pressure'][i] < 3.0,
                {'condenser_pressure': 2.5, 'chill_water_outlet': d['chill_water_outlet'][i] + 2}
            )},
            2: {'name': 'Condenser Fault', 'conditions': lambda d, i: (
                d['differential_pressure'][i] > 20,
                {'differential_pressure': 25, 'condenser_pressure': d['condenser_pressure'][i] + 1.5}
            )},
            3: {'name': 'Flow Switch Fault', 'conditions': lambda d, i: (
                d['flow_switch'][i] == 0,
                {'chill_water_inlet': d['chill_water_inlet'][i] + 4}
            )},
            4: {'name': 'Pump Failure', 'conditions': lambda d, i: (
                d['condenser_pump'][i] == 0,
                {'supply_water_temp': d['supply_water_temp'][i] + 5}
            )}
        }
        
        # Inject faults with balanced classes
        for fault_id in faults:
            indices = np.random.choice(num_samples, fault_samples, replace=False)
            data['fault_type'][indices] = fault_id
            for i in indices:
                condition, updates = faults[fault_id]['conditions'](data, i)
                if condition:
                    for k, v in updates.items():
                        data[k][i] = v

    elif device_type == "Generator":
        data = {
            # Generator Parameters from Client List
            'oil_pressure': np.random.normal(2.0, 0.2, num_samples),
            'coolant_temp': np.random.normal(85, 5, num_samples),
            'battery_voltage': np.random.normal(24, 0.3, num_samples),
            'phase1_voltage': np.random.normal(230, 3, num_samples),
            'phase2_voltage': np.random.normal(230, 3, num_samples),
            'phase3_voltage': np.random.normal(230, 3, num_samples),
            'frequency': np.random.normal(50, 0.1, num_samples),
            'load_percent': np.random.uniform(40, 80, num_samples),
            'run_hours': np.random.randint(0, 20000, num_samples),
            'fuel_level': np.random.uniform(30, 100, num_samples),
            'fault_type': np.zeros(num_samples, dtype=int)
        }
        
        # Generator Fault Injection (Client's Thresholds)
        fault_samples = 5000
        faults = {
            1: {'name': 'Low Oil Pressure', 'conditions': lambda d, i: (
                d['oil_pressure'][i] < 1.03,
                {'oil_pressure': 0.8, 'coolant_temp': d['coolant_temp'][i] + 10}
            )},
            2: {'name': 'Overheating', 'conditions': lambda d, i: (
                d['coolant_temp'][i] > 120,
                {'coolant_temp': 125, 'oil_pressure': d['oil_pressure'][i] - 0.5}
            )},
            3: {'name': 'Voltage Imbalance', 'conditions': lambda d, i: (
                abs(d['phase1_voltage'][i] - d['phase2_voltage'][i]) > 15,
                {'phase1_voltage': 210, 'phase2_voltage': 245, 'frequency': 49}
            )},
            4: {'name': 'Fuel System Fault', 'conditions': lambda d, i: (
                d['fuel_level'][i] < 10,
                {'fuel_level': 0, 'load_percent': 0}
            )}
        }
        
        # Inject faults with balanced classes
        for fault_id in faults:
            indices = np.random.choice(num_samples, fault_samples, replace=False)
            data['fault_type'][indices] = fault_id
            for i in indices:
                condition, updates = faults[fault_id]['conditions'](data, i)
                if condition:
                    for k, v in updates.items():
                        data[k][i] = v

    data.update(base_params)
    return pd.DataFrame(data)

if __name__ == "__main__":
    devices = ["AHU", "Chiller", "Generator"]
    for device in devices:
        df = generate_device_data(device)
        df.to_csv(f'{device.lower()}_data.csv', index=False)
        print(f"{device} Data Summary:")
        print(df['fault_type'].value_counts().sort_index())
        print("\n" + "="*50 + "\n")