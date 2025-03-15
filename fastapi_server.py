from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import joblib  # Added for alternative model loading
import os

app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models as None
ahu_model = None
chiller_model = None
generator_model = None

def load_model(model_path):
    """
    Try different methods to load the model
    """
    try:
        # Try loading with pickle first
        with open(model_path, 'rb') as file:
            return pickle.load(file)
    except:
        try:
            # Try loading with joblib if pickle fails
            return joblib.load(model_path)
        except Exception as e:
            print(f"Error loading model {model_path}: {str(e)}")
            return None

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Load the trained models with better error handling
print("Loading models...")
model_paths = {
    'ahu': 'models/ahu_model.pkl',
    'chiller': 'models/chiller_model.pkl',
    'generator': 'models/generator_model.pkl'
}

for model_name, path in model_paths.items():
    if os.path.exists(path):
        if model_name == 'ahu':
            ahu_model = load_model(path)
        elif model_name == 'chiller':
            chiller_model = load_model(path)
        elif model_name == 'generator':
            generator_model = load_model(path)
        print(f"Loaded {model_name} model successfully")
    else:
        print(f"Warning: {model_name} model file not found at {path}")

# Pydantic models for data validation
class AHUData(BaseModel):
    supply_air_temp: float
    return_air_temp: float
    room_air_temp: float
    return_air_humidity: float
    fan_speed: float
    cooling_state: int
    electric_reheat_state: int
    filter_dp: float
    cool_water_valve: float
    hot_water_valve: float
    outside_air_damper: float

class ChillerData(BaseModel):
    chill_water_outlet: float
    chill_water_inlet: float
    condenser_pressure: float
    differential_pressure: float
    supply_water_temp: float
    cooling_tower_fan: int
    condenser_pump: int
    return_condenser_valve: int
    flow_switch: int

class GeneratorData(BaseModel):
    oil_pressure: float
    coolant_temp: float
    battery_voltage: float
    phase1_voltage: float
    phase2_voltage: float
    phase3_voltage: float
    frequency: float
    load_percent: float
    run_hours: int
    fuel_level: float

@app.post("/predict/ahu")
async def predict_ahu(data: AHUData):
    if ahu_model is None:
        raise HTTPException(status_code=503, detail="AHU model not loaded")
    try:
        df = pd.DataFrame([data.dict()])
        prediction = ahu_model.predict(df)[0]
        probability = ahu_model.predict_proba(df)[0].max()
        return {
            "fault_type": int(prediction),
            "probability": float(probability),
            "data": data.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/chiller")
async def predict_chiller(data: ChillerData):
    if chiller_model is None:
        raise HTTPException(status_code=503, detail="Chiller model not loaded")
    try:
        df = pd.DataFrame([data.dict()])
        prediction = chiller_model.predict(df)[0]
        probability = chiller_model.predict_proba(df)[0].max()
        return {
            "fault_type": int(prediction),
            "probability": float(probability),
            "data": data.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/generator")
async def predict_generator(data: GeneratorData):
    if generator_model is None:
        raise HTTPException(status_code=503, detail="Generator model not loaded")
    try:
        df = pd.DataFrame([data.dict()])
        prediction = generator_model.predict(df)[0]
        probability = generator_model.predict_proba(df)[0].max()
        return {
            "fault_type": int(prediction),
            "probability": float(probability),
            "data": data.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Endpoint to check if models are loaded properly
    """
    return {
        "status": "running",
        "models_loaded": {
            "ahu": ahu_model is not None,
            "chiller": chiller_model is not None,
            "generator": generator_model is not None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    