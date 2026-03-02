from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app import models
import uuid

def test_save_pipeline():
    client = TestClient(app)
    db = SessionLocal()
    
    # 1. create a draft dataset
    dataset_id = str(uuid.uuid4())
    ds = models.Dataset(
        id=dataset_id, 
        original_filename="test.csv", 
        stored_filename=f"test_{dataset_id}.csv", 
        file_path="dummy.csv", 
        file_format="csv", 
        row_count=0, 
        col_count=0, 
        size_bytes=0
    )
    db.add(ds)
    db.commit()
    
    # 2. create a mock draft pipeline
    pipeline_id = str(uuid.uuid4())
    p = models.Pipeline(
        id=pipeline_id,
        name="Draft Pipeline",
        dataset_id=dataset_id,
        steps="[]",
        description="test"
    )
    db.add(p)
    db.commit()
    
    print("Pipeline ID:", pipeline_id)
    
    # 3. Call the POST clone endpoint
    response = client.post(f"/api/v1/pipelines/{pipeline_id}/clone", json={
        "name": "My Saved Pipeline",
        "description": "It works"
    })
    
    print("Status:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    test_save_pipeline()
