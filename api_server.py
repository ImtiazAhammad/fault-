from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import json
import base64
from datetime import datetime
import os

app = FastAPI()

class DetectionData(BaseModel):
    detection_data: Dict[str, Any]
    snapshot: str
    timestamp: str

@app.post("/vehicle-detection")
async def receive_detection(data: DetectionData):
    try:
        # Create directory for storing snapshots if it doesn't exist
        os.makedirs("vehicle_snapshots", exist_ok=True)
        
        # Save snapshot
        timestamp = datetime.fromisoformat(data.timestamp)
        filename = f"vehicle_snapshots/vehicle_{data.detection_data['track_id']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Decode and save image
        img_data = base64.b64decode(data.snapshot)
        with open(filename, "wb") as f:
            f.write(img_data)
        
        # Save detection data
        detection_filename = f"vehicle_snapshots/vehicle_{data.detection_data['track_id']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(detection_filename, "w") as f:
            json.dump(data.detection_data, f, indent=4)
        
        return {"status": "success", "message": "Detection data and snapshot saved"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 