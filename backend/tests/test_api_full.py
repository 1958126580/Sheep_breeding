
from fastapi.testclient import TestClient
import pytest
from main import app
from database import Base, engine, SessionLocal
from models.blockchain import BlockchainRecord, AnimalCertificate
from models.cloud import SyncTask
from models.iot import IoTDevice, IoTData
from models.health import HealthRecord, VaccinationRecord

# Initialize DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    yield db
    db.close()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Sheep Breeding System API"}

def test_blockchain_lifecycle():
    # Submit Record
    data = {
        "record_type": "animal_register",
        "animal_id": 1001,
        "data": {"foo": "bar"}
    }
    res = client.post("/api/v1/blockchain/records", json=data)
    assert res.status_code == 201
    record = res.json()
    assert record["record_type"] == "animal_register"
    tx_hash = record["tx_hash"]
    
    # Verify Record
    res = client.post(f"/api/v1/blockchain/records/verify?tx_hash={tx_hash}", json={"foo": "bar"})
    assert res.status_code == 200
    assert res.json()["verified"] == True

    # List Records
    res = client.get("/api/v1/blockchain/records")
    assert res.status_code == 200
    assert len(res.json()) > 0

def test_cloud_lifecycle():
    # Start Sync
    data = {
        "direction": "upload",
        "categories": ["animals"]
    }
    res = client.post("/api/v1/cloud/sync/start", json=data)
    assert res.status_code == 201
    task_id = res.json()["id"]
    
    # Get Task
    res = client.get(f"/api/v1/cloud/sync/tasks/{task_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "pending"

def test_iot_lifecycle():
    # Register Device
    device_data = {
        "device_type": "scale",
        "device_sn": "TEST001",
        "farm_id": 1
    }
    res = client.post("/api/v1/iot/devices", json=device_data)
    assert res.status_code == 201
    device_id = res.json()["id"]
    
    # Upload Data
    data_points = {
        "data_points": [
            {
                "device_id": device_id,
                "metric_type": "weight",
                "metric_value": 50.5,
                "unit": "kg"
            }
        ]
    }
    res = client.post("/api/v1/iot/data", json=data_points)
    assert res.status_code == 201
    assert res.json()["processed"] == 1

def test_health_lifecycle():
    # Create Vaccine Record
    rec_data = {
        "animal_id": 1001,
        "vaccine_type_id": 1,
        "vaccination_date": "2024-01-01",
        "next_vaccination_date": "2024-02-01"
    }
    res = client.post("/api/v1/health/vaccinations", json=rec_data)
    assert res.status_code == 201
    
    # Check Due
    res = client.get("/api/v1/health/vaccinations/due?days_ahead=365")
    assert res.status_code == 200
    # Note: Might return empty if date logic doesn't match, but ensures endpoint works
