import io

def test_home(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Crop Disease Detection System" in res.data

def test_upload_no_file(client):
    res = client.post("/upload")
    assert res.status_code == 400
    assert b"No file uploaded" in res.data

def test_upload_with_file(client):
    # 1x1 transparent PNG image (valid for Pillow)
    tiny_png = (
        io.BytesIO(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01"
            b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
        "tiny.png"
    )
    res = client.post("/upload", data={"file": tiny_png}, content_type="multipart/form-data")
    assert res.status_code == 200
    data = res.get_json()
    assert "result" in data

    data = res.get_json()
    assert "result" in data
    assert "plant" in data["result"]

def test_chatbot_message(client):
    res = client.post("/api/chat", json={"session_id": "test123", "message": "hello"})
    assert res.status_code == 200
    data = res.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
