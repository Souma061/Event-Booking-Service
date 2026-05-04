import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "max-age=31536000; includeSubDomains" in headers.get("Strict-Transport-Security", "")

def test_cors_options():
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_input_validation():
    long_string = "A" * 2000
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": long_string,
            "email": "test_e2e@example.com",
            "phone": "1234567890",
            "password": "Password123!"
        }
    )
    assert response.status_code in (400, 422)

def test_rate_limiting_login():
    # Hit the endpoint repeatedly to trigger the rate limit.
    for i in range(20):
        res = client.post(
            "/api/auth/login",
            json={
                "email": "rate_limit_test@example.com",
                "password": "Password123!"
            }
        )
        if res.status_code == 429:
            assert "Too many" in res.json().get("detail", "")
            return
    pytest.fail("Rate limiting did not engage")
