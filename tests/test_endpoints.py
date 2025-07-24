import io
import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_csv_success(client):
    csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA\nBob,35,Chicago"
    file_data = io.BytesIO(csv_content.encode())
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.csv", file_data, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "preview" in data
    assert data["filename"] == "test.csv"
    assert len(data["preview"]) > 0
    assert data["preview"][0] == ["name", "age", "city"]  

def test_upload_invalid_extension(client):
    file_data = io.BytesIO(b"invalid content")
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", file_data, "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["error"]

def test_process_file(client):
    csv_content = "value1,value2\n10,20\n30,40\n50,60"
    file_data = io.BytesIO(csv_content.encode())
    
    upload_response = client.post(
        "/api/v1/upload",
        files={"file": ("test.csv", file_data, "text/csv")}
    )
    
    file_id = upload_response.json()["file_id"]
    
    process_response = client.post(
        "/api/v1/process",
        json={"file_id": file_id}
    )
    
    assert process_response.status_code == 200
    data = process_response.json()
    assert data["status"] == "processing"
    assert data["file_id"] == file_id

def test_get_insights_not_processed(client):
    csv_content = "value1,value2\n10,20\n30,40\n50,60"
    file_data = io.BytesIO(csv_content.encode())
    
    upload_response = client.post(
        "/api/v1/upload",
        files={"file": ("test.csv", file_data, "text/csv")}
    )
    
    file_id = upload_response.json()["file_id"]
    
    response = client.get(f"/api/v1/insights?file_id={file_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uploaded"

def test_get_file_status(client):
    csv_content = "name,score\nAlice,95\nBob,87"
    file_data = io.BytesIO(csv_content.encode())
    
    upload_response = client.post(
        "/api/v1/upload",
        files={"file": ("test.csv", file_data, "text/csv")}
    )
    
    file_id = upload_response.json()["file_id"]
    
    response = client.get(f"/api/v1/status?file_id={file_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    assert data["status"] == "uploaded"
    assert data["filename"] == "test.csv"

def test_process_nonexistent_file(client):
    response = client.post(
        "/api/v1/process",
        json={"file_id": "nonexistent-id"}
    )
    
    assert response.status_code == 404
    assert "File not found" in response.json()["error"]