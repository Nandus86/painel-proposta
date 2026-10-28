import asyncio
import base64
import io
import logging
import time

import httpx
import qrcode

from app.config import settings
from app.core.security import decrypt_data, encrypt_data
from app.models.empresa import Empresa
from app.models.sistema_config import SistemaConfig

logger = logging.getLogger(__name__)


def _get_uazapi_config(sistema_config: SistemaConfig) -> tuple[str | None, str | None]:
    base_url = (
        (sistema_config.uazapi_base_url if sistema_config else None)
        or getattr(settings, "WHATSAPP_API_URL", "http://localhost:8080")
    )
    token = (
        decrypt_data(sistema_config.uazapi_admin_token)
        if (sistema_config and sistema_config.uazapi_admin_token)
        else getattr(settings, "WHATSAPP_ADMIN_TOKEN", "whatsmeow-admin-key")
    )

    if not base_url:
        return None, None
    return base_url.rstrip("/"), token


def _build_headers(admin_token: str | None = None, instance_token: str | None = None) -> dict[str, str]:
    """Monta cabeçalhos compatíveis com WhatsMeow-Basileia (v0.0.8+) e Uazapi."""
    tok = instance_token or admin_token or ""
    if not tok:
        return {}
    headers = {
        "Authorization": f"Bearer {tok}",
        "X-API-Key": tok,
        "api_key": tok,
        "token": tok,
    }
    if admin_token:
        headers["admintoken"] = admin_token
    return headers


def _strip_data_url(qr_value: str | None) -> str | None:
    if not qr_value or not isinstance(qr_value, str):
        return None
    qr_value = qr_value.strip()
    if qr_value.startswith("data:") and "," in qr_value:
        return qr_value.split(",", 1)[1]
    return qr_value


def _encode_qr_png(raw_code: str) -> str:
    img = qrcode.make(raw_code)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


_active_qr_tasks: dict[str, asyncio.Task] = {}
_latest_qr_data: dict[str, dict] = {}


async def _listen_qr_stream(base_url: str, instance_id: str, headers: dict[str, str]):
    logger.info(f"Iniciando listener SSE de QR Code para {instance_id}")
    try:
        timeout = httpx.Timeout(connect=10.0, read=180.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", f"{base_url}/api/device/{instance_id}/qr", headers=headers) as resp:
                if resp.status_code != 200:
                    logger.warning(f"SSE /qr retornou status {resp.status_code} para {instance_id}")
                    return
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        raw_code = line.replace("data:", "").strip()
                        if raw_code:
                            qr_b64 = _encode_qr_png(raw_code)
                            _latest_qr_data[instance_id] = {
                                "qr": qr_b64,
                                "raw": raw_code,
                                "updated_at": time.time(),
                            }
                            logger.info(f"QR code recebido/atualizado para {instance_id}")
    except asyncio.CancelledError:
        logger.info(f"SSE listener para {instance_id} finalizado por cancelamento")
    except Exception as e:
        logger.debug(f"SSE listener para {instance_id} finalizado: {e}")
    finally:
        _latest_qr_data.pop(instance_id, None)
        _active_qr_tasks.pop(instance_id, None)


async def ensure_instance(empresa: Empresa, sistema_config: SistemaConfig) -> str:
    base_url, admin_token = _get_uazapi_config(sistema_config)
    if not base_url:
        raise ValueError("WhatsApp não configurado no sistema")

    instance_name = f"empresa-{str(empresa.id)[:8]}"
    instance_token = _get_instance_token(empresa)
    admin_headers = _build_headers(admin_token=admin_token)

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Se já temos token da instância, verificar se ela já existe via /api/instance/status
        if instance_token and empresa.uazapi_instance_id:
            try:
                inst_headers = _build_headers(admin_token=admin_token, instance_token=instance_token)
                st_resp = await client.get(f"{base_url}/api/instance/status", headers=inst_headers)
                if st_resp.status_code == 200 and st_resp.text:
                    st_data = st_resp.json()
                    inst_obj = st_data.get("instance") or {}
                    if inst_obj.get("id"):
                        empresa.uazapi_instance_id = inst_obj["id"]
                        return inst_obj["id"]
            except Exception as e:
                logger.debug(f"Instance status check skipped: {e}")

        # 2. Tentar API WhatsMeow-Basileia (/api/device) com chave de admin/operator
        try:
            device_resp = await client.get(f"{base_url}/api/device", headers=admin_headers)
            if device_resp.status_code == 200:
                devices = device_resp.json()
                if isinstance(devices, list):
                    for d in devices:
                        if d.get("id") == empresa.uazapi_instance_id or d.get("name") == instance_name:
                            empresa.uazapi_instance_id = d["id"]
                            api_key = d.get("api_key")
                            if api_key and "*" not in api_key:
                                empresa.uazapi_instance_token = encrypt_data(api_key)
                            elif not empresa.uazapi_instance_token:
                                empresa.uazapi_instance_token = encrypt_data(d["id"])
                            return d["id"]

                    create_resp = await client.post(
                        f"{base_url}/api/device",
                        headers=admin_headers,
                        json={"name": instance_name},
                    )
                    if create_resp.status_code in (200, 201):
                        data = create_resp.json()
                        dev_id = data.get("device_id") or data.get("id")
                        api_key = data.get("api_key") or dev_id
                        if dev_id:
                            empresa.uazapi_instance_id = dev_id
                            empresa.uazapi_instance_token = encrypt_data(api_key)
                            return dev_id
            elif device_resp.status_code == 401:
                raise ValueError(
                    "Chave de API (Admin Token) do WhatsApp inválida ou não autorizada. "
                    "Configure a chave correta em Super Admin → Configurações ou WHATSAPP_ADMIN_TOKEN."
                )
        except ValueError:
            raise
        except Exception as e:
            logger.debug(f"Whatsmeow device check skipped: {e}")

        # 3. Tentar UAZAPI v2 /api/instance/create (WhatsMeow-Basileia / Uazapi)
        try:
            uaz_create = await client.post(
                f"{base_url}/api/instance/create",
                headers=admin_headers,
                json={"name": instance_name},
            )
            if uaz_create.status_code in (200, 201) and uaz_create.text:
                data = uaz_create.json()
                inst_obj = data.get("instance") or {}
                dev_id = inst_obj.get("id") or data.get("instanceId") or instance_name
                tok = data.get("token") or inst_obj.get("api_key") or dev_id
                empresa.uazapi_instance_id = dev_id
                empresa.uazapi_instance_token = encrypt_data(tok)
                return dev_id
        except Exception as e:
            logger.debug(f"UAZAPI /api/instance/create skipped: {e}")

        # 4. Fallback legado Uazapi (/instance/init)
        resp = await client.post(
            f"{base_url}/instance/init",
            headers=admin_headers,
            json={"instanceName": instance_name},
        )
        if resp.status_code == 400 and "already" in resp.text.lower():
            pass
        elif resp.status_code == 401:
            raise ValueError("Chave de API (Admin Token) do WhatsApp inválida ou ausente.")
        elif resp.status_code not in (200, 201):
            logger.error(f"WhatsApp init failed: {resp.status_code} {resp.text}")
            raise ValueError("Falha ao criar instância WhatsApp")

        data = resp.json() if resp.text else {}
        token = data.get("token") or data.get("instance", {}).get("token")
        instance_id = data.get("instanceId") or data.get("instance", {}).get("id")

        if token:
            empresa.uazapi_instance_id = instance_id or instance_name
            empresa.uazapi_instance_token = encrypt_data(token)

    return empresa.uazapi_instance_id or instance_name


async def connect(empresa: Empresa, sistema_config: SistemaConfig) -> dict:
    base_url, admin_token = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url:
        raise ValueError("Instância WhatsApp não configurada")

    instance_name = f"empresa-{str(empresa.id)[:8]}"
    instance_id = empresa.uazapi_instance_id or instance_name
    headers = _build_headers(admin_token=admin_token, instance_token=token)

    # 1. Tentar rota síncrona /api/instance/connect do WhatsMeow-Basileia v0.0.8+
    # (funciona perfeitamente com múltiplos workers Uvicorn pois o estado fica no servidor Go)
    if token:
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    f"{base_url}/api/instance/connect",
                    headers=headers,
                )
                if resp.status_code in (200, 201) and resp.text:
                    data = resp.json()
                    state = data.get("state") or "connecting"
                    if state == "connected":
                        empresa.whatsapp_status = "connected"
                        empresa.whatsapp_conectado = True
                        return {"qrcode_base64": None, "paircode": None, "status": "connected"}

                    raw_qr = data.get("qrcode_raw")
                    qrcode_b64 = _strip_data_url(data.get("qrcode"))
                    if not qrcode_b64 and raw_qr:
                        qrcode_b64 = _encode_qr_png(raw_qr)
                    paircode = data.get("paircode") or data.get("pairCode")
                    if qrcode_b64 or paircode:
                        return {
                            "qrcode_base64": qrcode_b64,
                            "paircode": paircode,
                            "status": "connecting",
                        }
        except Exception as e:
            logger.debug(f"Whatsmeow /api/instance/connect fallback to SSE: {e}")

    # 2. Tentar WhatsMeow-Basileia SSE QR stream: GET /api/device/{id}/qr
    old_task = _active_qr_tasks.get(instance_id)
    if old_task and not old_task.done():
        old_task.cancel()
        await asyncio.sleep(0.1)

    task = asyncio.create_task(_listen_qr_stream(base_url, instance_id, headers))
    _active_qr_tasks[instance_id] = task

    for _ in range(40):
        if instance_id in _latest_qr_data:
            return {
                "qrcode_base64": _latest_qr_data[instance_id]["qr"],
                "paircode": None,
                "status": "connecting",
            }
        await asyncio.sleep(0.2)

    # 3. Fallback padrão Uazapi /instance/connect
    if token:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{base_url}/instance/connect",
                    headers=headers,
                )
                if resp.status_code in (200, 201):
                    data = resp.json() if resp.text else {}
                    qrcode_data = _strip_data_url(data.get("qrcode") or data.get("qrCode") or data.get("qr"))
                    paircode = data.get("paircode") or data.get("pairCode")

                    return {
                        "qrcode_base64": qrcode_data,
                        "paircode": paircode,
                        "status": "connecting",
                    }
        except Exception as e:
            logger.debug(f"Uazapi connect failed: {e}")

    raise ValueError("Falha ao gerar QR Code do WhatsApp")


async def get_status(empresa: Empresa, sistema_config: SistemaConfig) -> dict:
    base_url, admin_token = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url:
        return {"status": "disconnected", "numero": None}

    instance_name = f"empresa-{str(empresa.id)[:8]}"
    instance_id = empresa.uazapi_instance_id or instance_name
    headers = _build_headers(admin_token=admin_token, instance_token=token)
    admin_headers = _build_headers(admin_token=admin_token)

    async with httpx.AsyncClient(timeout=10) as client:
        # 1. Tentar WhatsMeow-Basileia v0.0.8+ GET /api/instance/status (retorna estado + QR ativo)
        if token:
            try:
                resp = await client.get(f"{base_url}/api/instance/status", headers=headers)
                if resp.status_code == 200 and resp.text:
                    data = resp.json()
                    if isinstance(data, dict) and ("state" in data or "instance" in data):
                        inst_obj = data.get("instance") or {}
                        st_obj = data.get("status") or {}
                        if inst_obj.get("id") and empresa.uazapi_instance_id != inst_obj.get("id"):
                            empresa.uazapi_instance_id = inst_obj["id"]

                        is_online = (
                            data.get("state") == "connected"
                            or bool(st_obj.get("loggedIn") and st_obj.get("connected"))
                            or inst_obj.get("status") in ("online", "connected")
                        )
                        status = "connected" if is_online else "disconnected"
                        jid = st_obj.get("jid") or inst_obj.get("jid") or ""
                        numero = jid.split(":")[0].split("@")[0] if jid else None

                        empresa.whatsapp_status = status
                        empresa.whatsapp_conectado = is_online
                        if numero:
                            empresa.whatsapp_numero = numero

                        if is_online:
                            qr_task = _active_qr_tasks.pop(instance_id, None)
                            if qr_task and not qr_task.done():
                                qr_task.cancel()
                            _latest_qr_data.pop(instance_id, None)
                            return {"status": "connected", "numero": numero, "qr": None}

                        latest_qr = _strip_data_url(data.get("qrcode"))
                        if not latest_qr and data.get("qrcode_raw"):
                            latest_qr = _encode_qr_png(data["qrcode_raw"])
                        if not latest_qr:
                            latest_qr = _latest_qr_data.get(instance_id, {}).get("qr")

                        return {"status": status, "numero": numero, "qr": latest_qr}
            except Exception as e:
                logger.debug(f"Whatsmeow /api/instance/status error: {e}")

        # 2. Tentar WhatsMeow-Basileia GET /api/device
        try:
            resp = await client.get(f"{base_url}/api/device", headers=admin_headers or headers)
            if resp.status_code == 200:
                devices = resp.json()
                if isinstance(devices, list):
                    found = None
                    for d in devices:
                        if d.get("id") == instance_id or d.get("name") in (instance_id, instance_name):
                            found = d
                            break

                    if found:
                        if not empresa.uazapi_instance_id or empresa.uazapi_instance_id != found.get("id"):
                            empresa.uazapi_instance_id = found.get("id")

                        is_online = found.get("status") in ("online", "connected")
                        status = "connected" if is_online else "disconnected"
                        jid = found.get("jid") or ""
                        numero = jid.split(":")[0].split("@")[0] if jid else None

                        empresa.whatsapp_status = status
                        empresa.whatsapp_conectado = is_online
                        if numero:
                            empresa.whatsapp_numero = numero

                        if is_online:
                            qr_task = _active_qr_tasks.pop(instance_id, None)
                            if qr_task and not qr_task.done():
                                qr_task.cancel()
                            _latest_qr_data.pop(instance_id, None)

                        latest_qr = _latest_qr_data.get(instance_id, {}).get("qr")
                        return {"status": status, "numero": numero, "qr": latest_qr}
                    else:
                        return {"status": "disconnected", "numero": None}
        except Exception as e:
            logger.debug(f"Whatsmeow status check error: {e}")

        # 3. Fallback padrão Uazapi /instance/status
        if token:
            try:
                resp = await client.get(
                    f"{base_url}/instance/status",
                    headers=headers,
                )
                if resp.status_code == 401:
                    return {"status": "disconnected", "numero": None}

                if resp.status_code == 200 and resp.text:
                    try:
                        data = resp.json()
                        status = data.get("status") or data.get("instance", {}).get("status", "disconnected")
                        numero = data.get("owner") or data.get("numero")

                        empresa.whatsapp_status = status
                        if numero:
                            empresa.whatsapp_numero = str(numero)
                        empresa.whatsapp_conectado = status == "connected"

                        return {"status": status, "numero": numero}
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"WhatsApp status check failed: {e}")

        return {"status": "disconnected", "numero": None}


async def disconnect(empresa: Empresa, sistema_config: SistemaConfig) -> None:
    base_url, admin_token = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url:
        return

    instance_name = f"empresa-{str(empresa.id)[:8]}"
    instance_id = empresa.uazapi_instance_id or instance_name
    headers = _build_headers(admin_token=admin_token, instance_token=token)

    qr_task = _active_qr_tasks.pop(instance_id, None)
    if qr_task and not qr_task.done():
        qr_task.cancel()
    _latest_qr_data.pop(instance_id, None)

    async with httpx.AsyncClient(timeout=15) as client:
        # 1. Tentar Whatsmeow DELETE /api/device/{id}
        try:
            await client.delete(f"{base_url}/api/device/{instance_id}", headers=headers)
        except Exception:
            pass

        # 2. Tentar Whatsmeow/UAZAPI POST /api/instance/disconnect ou /instance/disconnect
        if token:
            for path in ("/api/instance/disconnect", "/instance/disconnect"):
                try:
                    await client.post(f"{base_url}{path}", headers=headers)
                except Exception:
                    pass

    empresa.whatsapp_status = "disconnected"
    empresa.whatsapp_numero = None
    empresa.whatsapp_conectado = False


async def send_text(empresa: Empresa, sistema_config: SistemaConfig, numero: str, texto: str) -> dict:
    base_url, admin_token = _get_uazapi_config(sistema_config)
    token = _get_instance_token(empresa)
    if not base_url or not token:
        raise ValueError("WhatsApp não configurado")

    if not empresa.whatsapp_conectado:
        raise ValueError("WhatsApp não está conectado")

    numero = numero.strip().replace("+", "").replace("-", "").replace(" ", "")
    headers = _build_headers(admin_token=admin_token, instance_token=token)
    if empresa.uazapi_instance_id:
        headers["X-Instance-Id"] = empresa.uazapi_instance_id

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Tentar WhatsMeow-Basileia /api/send/text
        try:
            resp = await client.post(
                f"{base_url}/api/send/text",
                headers=headers,
                json={"number": numero, "text": texto, "linkPreview": True, "delay": 0},
            )
            if resp.status_code in (200, 201):
                return resp.json() if resp.text else {}
        except Exception as e:
            logger.debug(f"Whatsmeow /api/send/text error: {e}")

        # 2. Fallback padrão Uazapi /send/text
        resp = await client.post(
            f"{base_url}/send/text",
            headers=headers,
            json={"number": numero, "text": texto, "linkPreview": True, "delay": 0},
        )
        if resp.status_code not in (200, 201):
            logger.error(f"WhatsApp send failed: {resp.status_code} {resp.text}")
            raise ValueError("Falha ao enviar mensagem")

        return resp.json() if resp.text else {}


def _get_instance_token(empresa: Empresa) -> str | None:
    if not empresa.uazapi_instance_token:
        return None
    return decrypt_data(empresa.uazapi_instance_token)
