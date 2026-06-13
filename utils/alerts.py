import os
import requests
from dotenv import load_dotenv

# WHY load_dotenv: reads your .env file and makes
# TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID available
# as environment variables. Without this, os.getenv returns None.
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NDVI_ALERT_THRESHOLD = -0.05 # trigger alert if NDVI drops more than this


def send_telegram_message(message: str) -> bool:
    """
    Send a message via Telegram Bot API.
    
    WHY REST API directly:
    No need for heavy telegram library.
    Telegram's API is a simple HTTP POST — requests handles it cleanly.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not configured in .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"  # WHY: allows bold, italic formatting in message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


def check_and_alert(region: str, result: dict, carbon: dict) -> dict:
    """
    Check analysis result and send Telegram alert if deforestation detected.
    
    WHY threshold -0.05:
    Small drops (-0.01 to -0.04) could be seasonal variation.
    Drops beyond -0.05 are statistically significant enough to alert.
    """
    ndvi_change = result["ndvi_change"]
    severity = result["severity"]
    deforested = result["deforested"]

    alert_sent = False
    alert_message = None

    # Only alert on actual significant drops
    if ndvi_change <= NDVI_ALERT_THRESHOLD:
        status_line = result["status"]
        before_date = result["before"]["image_date"]
        after_date = result["after"]["image_date"]
        ml_label = result["ml_after"]["class_label"] if result.get("ml_available") else "N/A"
        ml_conf = int(result["ml_after"]["confidence"] * 100) if result.get("ml_available") else 0

        alert_message = f"""
*FORESTWATCH ALERT*
━━━━━━━━━━━━━━━━━━
*Region:* {region}
*Status:* {status_line}
*Severity:* {severity}

*NDVI Before:* {result['before']['ndvi_mean']} ({before_date})
*NDVI After:* {result['after']['ndvi_mean']} ({after_date})
*NDVI Change:* {ndvi_change:+.4f} ({result['pct_change']:+.1f}%)

*AI Classification:* {ml_label} ({ml_conf}% confidence)
*Deforestation Confirmed:* {"YES" if deforested else "NO"}

*Carbon Impact:*
  Area affected: {carbon['area_affected_ha']:,.0f} ha
  CO2 estimate: {carbon['carbon_tons']:,.0f} tons
  Carbon credits: {carbon['carbon_credits']:,}
━━━━━━━━━━━━━━━━━━
_Sent by ForestWatch AI_
        """.strip()

        alert_sent = send_telegram_message(alert_message)

    return {
        "alert_sent": alert_sent,
        "alert_triggered": ndvi_change <= NDVI_ALERT_THRESHOLD,
        "message": alert_message
    }