import logging
import httpx
from app.models.empresa import Empresa
from app.models.sistema_config import SistemaConfig
from app.core.security import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


def _get_uazapi_config(sistema_config: SistemaConfig) -> tuple[str | None, str | None]:
    if not sistema_config.uazapi_base_url or not sistema_config.uazapi_admin_token:
        return None, None
    base_url = sistema_config.uazapi_base_url.rstrip("/")
    token = decrypt_data(sistema_config.uazapi_admin_token)
    if not token:
        return None, None
    return base_url, token


async def ensure_instance(empresa: Empresa, sistema_config: SistemaConfig) -> str:
    base_url, admin_token = _get_uazapi_config(sistema_config)
    if not base_url:
        raise ValueError("Uazapi não configurado no sistema")

    instance_name = f"empresa-{str(empresa.id)[:8]}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/instance/init",
            headers={"admintoken": admin_token},
            json={"instanceName": instance_name},
        )
        if resp.status_code == 400 and "already" in resp.text.lower():
            pass
        elif resp.status_code not in (200, 201):
            logger.error(f"Uazapi init failed: {resp.status_code} {resp.text}")
            raise ValueError("Falha ao criar instância WhatsApp")

        data = resp.json() if resp.text else {}
        token = data.get("token") or data.get("instance", {}).get("token")
        instance_id = data.get("instanceId") or data.get("instance", {}).get("id")

        if token:
            empresa.uazapi_instance_id = instance_id or instance_name
            empresa.uazapi_instance_token = encrypt_data(token)

    return instance_name


async def connect(empresa: Empresa, sistema_config: SistemaConfig) -> dict:
    base_url, _ = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url or not token:
        raise ValueError("Instância WhatsApp não configurada")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/instance/connect",
            headers={"token": token},
        )
        if resp.status_code not in (200, 201):
            logger.error(f"Uazapi connect failed: {resp.status_code} {resp.text}")
            raise ValueError("Falha ao conectar WhatsApp")

        data = resp.json() if resp.text else {}
        qrcode = data.get("qrcode") or data.get("qrCode") or data.get("qr")
        paircode = data.get("paircode") or data.get("pairCode")

        return {
            "qrcode_base64": qrcode,
            "paircode": paircode,
            "status": "connecting",
        }


async def get_status(empresa: Empresa, sistema_config: SistemaConfig) -> dict:
    base_url, _ = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url or not token:
        return {"status": "disconnected", "numero": None}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{base_url}/instance/status",
                headers={"token": token},
            )
            if resp.status_code == 401:
                return {"status": "disconnected", "numero": None}

            data = resp.json() if resp.text else {}
            status = data.get("status") or data.get("instance", {}).get("status", "disconnected")
            numero = data.get("owner") or data.get("numero")

            empresa.whatsapp_status = status
            if numero:
                empresa.whatsapp_numero = str(numero)
            empresa.whatsapp_conectado = status == "connected"

            return {"status": status, "numero": numero}
        except Exception as e:
            logger.error(f"Uazapi status check failed: {e}")
            return {"status": "disconnected", "numero": None}


async def disconnect(empresa: Empresa, sistema_config: SistemaConfig) -> None:
    base_url, _ = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url or not token:
        return

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            await client.post(
                f"{base_url}/instance/disconnect",
                headers={"token": token},
            )
        except Exception:
            pass

    empresa.whatsapp_status = "disconnected"
    empresa.whatsapp_numero = None
    empresa.whatsapp_conectado = False


async def send_text(empresa: Empresa, sistema_config: SistemaConfig, numero: str, texto: str) -> dict:
    base_url, _ = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url or not token:
        raise ValueError("WhatsApp não configurado")

    if not empresa.whatsapp_conectado:
        raise ValueError("WhatsApp não está conectado")

    numero = numero.strip().replace("+", "").replace("-", "").replace(" ", "")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/send/text",
            headers={"token": token},
            json={"number": numero, "text": texto, "linkPreview": True, "delay": 0},
        )
        if resp.status_code not in (200, 201):
            logger.error(f"Uazapi send failed: {resp.status_code} {resp.text}")
            raise ValueError("Falha ao enviar mensagem")

        return resp.json() if resp.text else {}


def _get_instance_token(empresa: Empresa) -> str | None:
    if not empresa.uazapi_instance_token:
        return None
    return decrypt_data(empresa.uazapi_instance_token)
