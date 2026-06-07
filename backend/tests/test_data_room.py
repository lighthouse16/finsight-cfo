from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_data_room_readiness_contract():
    response = client.get("/api/data-room/demo-readiness")

    assert response.status_code == 200
    data = response.json()

    assert set(data.keys()) == {"records", "dependencies", "summary"}
    assert len(data["records"]) == 9
    assert len(data["dependencies"]) == 5

    summary = data["summary"]
    assert summary["totalRequired"] == 6
    assert summary["connectedRequired"] == 3
    assert summary["missingRequired"] == 3
    assert summary["readinessPercentage"] == 50
    assert summary["dataMode"] == "demo_workspace"

    record = data["records"][0]
    assert record["id"] == "pl-statement"
    assert record["status"] == "demo_available"
    assert "valuation" in record["requiredFor"]
