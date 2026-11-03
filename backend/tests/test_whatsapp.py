import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.whatsapp import (
    _build_headers,
    _strip_data_url,
    _encode_qr_png,
    ensure_instance,
    connect,
    get_status,
)
from app.models.empresa import Empresa
from app.models.sistema_config import SistemaConfig
from app.core.security import encrypt_data
import uuid


def test_build_headers():
    h = _build_headers(admin_token="adm123", instance_token="inst456", instance_id="dev-789")
    assert h["Authorization"] == "Bearer adm123"
    assert h["admintoken"] == "adm123"
    assert h["token"] == "inst456"
    assert h["X-Instance-Id"] == "dev-789"

    h2 = _build_headers(instance_token="inst456", instance_id="dev-789")
    assert h2["Authorization"] == "Bearer inst456"
    assert h2["X-Instance-Id"] == "dev-789"


def test_strip_data_url():
    assert _strip_data_url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==") == "iVBORw0KGgoAAAANSUhEUg=="
    assert _strip_data_url("iVBORw0KGgoAAAANSUhEUg==") == "iVBORw0KGgoAAAANSUhEUg=="
    assert _strip_data_url(None) is None


def test_encode_qr_png():
    b64 = _encode_qr_png("2@abc,def,ghi")
    assert isinstance(b64, str)
    assert len(b64) > 100


@pytest.mark.asyncio
async def test_ensure_instance_finds_existing(db_session):
    empresa = Empresa(id=uuid.uuid4(), razao_social="Empresa Teste", cnpj="12345678000199")
    sc = SistemaConfig(id=1, uazapi_base_url="http://fake-whatsapp:8080", uazapi_admin_token=encrypt_data("admin-key"))

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"id": "dev123", "name": f"empresa-{str(empresa.id)[:8]}", "api_key": "wmb_secretkey123"}
    ]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        dev_id = await ensure_instance(empresa, sc)
        assert dev_id == "dev123"
        assert empresa.uazapi_instance_id == "dev123"


@pytest.mark.asyncio
async def test_connect_returns_qr(db_session):
    empresa = Empresa(id=uuid.uuid4(), razao_social="Empresa Teste", cnpj="12345678000199", uazapi_instance_id="dev123")
    sc = SistemaConfig(id=1, uazapi_base_url="http://fake-whatsapp:8080", uazapi_admin_token=encrypt_data("admin-key"))

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"state": "connecting", "qrcode_raw": "2@testrawcode", "qrcode": "data:image/png;base64,AAAA"}'
    mock_resp.json.return_value = {
        "state": "connecting",
        "qrcode_raw": "2@testrawcode",
        "qrcode": "data:image/png;base64,AAAA",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        res = await connect(empresa, sc)
        assert res["status"] == "connecting"
        assert res["qrcode_base64"] == "AAAA"
