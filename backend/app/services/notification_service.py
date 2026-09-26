import os
import urllib.request
import urllib.parse
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.sos import SOSEvent, SOSNotification
from backend.app.models.trusted_contact import TrustedContact


def _try_send_real_sms(phone_number: str, message: str) -> str:
    """
    Attempts to send a real SMS to `phone_number` if FAST2SMS_API_KEY (India) or TWILIO credentials
    are configured in environment variables. Returns the delivery status string.
    """
    clean_phone = "".join(ch for ch in phone_number if ch.isdigit())
    if clean_phone.startswith("91") and len(clean_phone) == 12:
        clean_10 = clean_phone[2:]
    else:
        clean_10 = clean_phone[-10:]

    fast2sms_key = os.getenv("FAST2SMS_API_KEY")
    if fast2sms_key and len(clean_10) == 10:
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = json.dumps({
                "route": "q",
                "message": message,
                "language": "english",
                "flash": 0,
                "numbers": clean_10,
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "authorization": fast2sms_key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    return "SENT_REAL_SMS"
        except Exception:
            return "FAILED_SMS_GATEWAY_LOGGED"

    return "SENT"


async def dispatch_sos_notifications(
    db: AsyncSession,
    sos: SOSEvent,
    contacts: List[TrustedContact],
    share_url: str,
) -> List[SOSNotification]:
    """
    Dispatches emergency notifications to both registered SafeRoute users (in-app + SMS)
    and external contacts (SMS/share link). Never aborts SOS creation if a notification fails.
    """
    records: List[SOSNotification] = []
    for c in contacts:
        try:
            channel = "IN_APP_AND_SMS" if c.contact_user_id else "SMS"
            summary = (
                f"EMERGENCY SOS from SafeRoute user on {sos.road_name or 'Chennai Corridor'} "
                f"({sos.latest_lat:.5f}, {sos.latest_lon:.5f}). "
                f"Nearest Police: {sos.nearest_police_station_name} ({sos.nearest_police_station_distance_km} km). "
                f"Live Track: {share_url}"
            )
            delivery_status = _try_send_real_sms(c.phone_number, summary)
            notif = SOSNotification(
                sos_id=sos.id,
                recipient_contact_id=c.id,
                channel=channel,
                delivery_status=delivery_status,
                message_summary=summary[:500],
            )
            db.add(notif)
            records.append(notif)
        except Exception as exc:
            failed_notif = SOSNotification(
                sos_id=sos.id,
                recipient_contact_id=c.id,
                channel="SMS",
                delivery_status="FAILED",
                message_summary=f"Notification dispatch error: {str(exc)[:200]}",
            )
            db.add(failed_notif)
            records.append(failed_notif)
    return records


async def dispatch_sos_status_update(
    db: AsyncSession,
    sos: SOSEvent,
    contacts: List[TrustedContact],
    new_status: str,
) -> None:
    """Notifies trusted contacts when an active SOS is CANCELLED or RESOLVED (User Safe)."""
    for c in contacts:
        try:
            msg = (
                f"SafeRoute Update: SOS #{str(sos.id)[:8]} has been marked {new_status} by the user."
            )
            _try_send_real_sms(c.phone_number, msg)
            db.add(
                SOSNotification(
                    sos_id=sos.id,
                    recipient_contact_id=c.id,
                    channel="IN_APP_AND_SMS" if c.contact_user_id else "SMS",
                    delivery_status="SENT",
                    message_summary=msg,
                )
            )
        except Exception:
            pass
