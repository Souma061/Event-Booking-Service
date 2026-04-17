import base64
import io
import json
from typing import Any

import qrcode

def build_ticket_payload(ticket_code:str,booking_id: int, show_id:int, user_id:int) -> dict[str, Any]:
    return {
        "ticket_code" :ticket_code,
        "booking_id": booking_id,
        "show_id": show_id,
        "user_id": user_id
    }

def generate_qr_base64(payload: dict[str, Any]) -> tuple[str,str]:
    seriealized_payload = json.dumps(payload, separators=(',', ':'),sort_keys=True)
    img = qrcode.make(seriealized_payload)
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    png_bytes = buffer.getvalue()
    return base64.b64encode(png_bytes).decode("ascii"),seriealized_payload
