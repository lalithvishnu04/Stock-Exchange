"""Telegram and Email notification service."""
import asyncio
from datetime import datetime
from typing import Optional
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

try:
    from telegram import Bot
    from telegram.error import TelegramError
    _TELEGRAM_AVAILABLE = True
except ImportError:
    _TELEGRAM_AVAILABLE = False


SIGNAL_EMOJI = {
    "BUY": "🟢 BUY",
    "ADD_MORE": "🟩 ADD MORE",
    "HOLD": "🔵 HOLD",
    "PARTIAL_SELL": "🟡 PARTIAL SELL",
    "SELL": "🔴 SELL",
    "AVOID": "⚫ AVOID",
}

RISK_EMOJI = {
    "LOW": "✅ LOW RISK",
    "MEDIUM": "⚠️ MEDIUM RISK",
    "HIGH": "🚨 HIGH RISK",
}


class NotificationService:
    def __init__(self):
        self._telegram_bot: Optional[object] = None
        if _TELEGRAM_AVAILABLE and settings.TELEGRAM_BOT_TOKEN:
            self._telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def send_recommendation_alert(
        self,
        symbol: str,
        company_name: str,
        signal: str,
        risk_level: str,
        current_price: float,
        target_price: Optional[float],
        stop_loss: Optional[float],
        reason: str,
        chat_id: Optional[str] = None,
        email_to: Optional[str] = None,
    ) -> dict:
        signal_label = SIGNAL_EMOJI.get(signal, signal)
        risk_label = RISK_EMOJI.get(risk_level, risk_level)

        message = (
            f"📊 *Stock Alert – {symbol}*\n\n"
            f"Signal: *{signal_label}*\n"
            f"Risk: *{risk_label}*\n"
            f"Company: {company_name}\n"
            f"Current Price: ₹{current_price:,.2f}\n"
        )
        if target_price:
            message += f"Target: ₹{target_price:,.2f}\n"
        if stop_loss:
            message += f"Stop Loss: ₹{stop_loss:,.2f}\n"
        message += f"\n📝 Reason: {reason}\n"
        message += f"\n🕒 {datetime.now().strftime('%d %b %Y %I:%M %p IST')}"

        results = {}
        if self._telegram_bot and (chat_id or settings.TELEGRAM_CHAT_ID):
            results["telegram"] = await self._send_telegram(
                message, chat_id or settings.TELEGRAM_CHAT_ID
            )
        if email_to or settings.ALERT_EMAIL_TO:
            subject = f"[Stock Advisor] {signal} Alert – {symbol}"
            html_body = _build_email_html(symbol, company_name, signal, risk_level, current_price, target_price, stop_loss, reason)
            results["email"] = await self._send_email(
                subject, html_body, email_to or settings.ALERT_EMAIL_TO
            )
        return results

    async def send_daily_report(
        self,
        report_html: str,
        chat_id: Optional[str] = None,
        email_to: Optional[str] = None,
    ) -> dict:
        results = {}
        summary = "📊 Your daily stock market report is ready. Check your dashboard."
        if self._telegram_bot and (chat_id or settings.TELEGRAM_CHAT_ID):
            results["telegram"] = await self._send_telegram(summary, chat_id or settings.TELEGRAM_CHAT_ID)
        if email_to or settings.ALERT_EMAIL_TO:
            results["email"] = await self._send_email(
                f"Daily Report – {datetime.now().strftime('%d %b %Y')}",
                report_html,
                email_to or settings.ALERT_EMAIL_TO,
            )
        return results

    async def _send_telegram(self, message: str, chat_id: str) -> bool:
        if not self._telegram_bot:
            return False
        try:
            await self._telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )
            return True
        except Exception:
            return False

    async def _send_email(self, subject: str, html_body: str, to_addr: str) -> bool:
        if not settings.SMTP_USERNAME:
            return False
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = to_addr
        msg.attach(MIMEText(html_body, "html"))
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=False,
                start_tls=True,
            )
            return True
        except Exception:
            return False


def _build_email_html(
    symbol: str,
    company_name: str,
    signal: str,
    risk_level: str,
    price: float,
    target: Optional[float],
    stop_loss: Optional[float],
    reason: str,
) -> str:
    color = {"BUY": "#16a34a", "ADD_MORE": "#22c55e", "HOLD": "#2563eb",
             "PARTIAL_SELL": "#d97706", "SELL": "#dc2626", "AVOID": "#6b7280"}.get(signal, "#111")
    risk_color = {"LOW": "#16a34a", "MEDIUM": "#d97706", "HIGH": "#dc2626"}.get(risk_level, "#111")
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <div style="background:{color};color:#fff;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="margin:0">{signal} – {symbol}</h2>
        <p style="margin:4px 0">{company_name}</p>
      </div>
      <div style="border:1px solid #e5e7eb;border-top:none;padding:20px;border-radius:0 0 8px 8px">
        <table style="width:100%;border-collapse:collapse">
          <tr><td><b>Risk Level</b></td><td style="color:{risk_color}"><b>{risk_level}</b></td></tr>
          <tr><td><b>Current Price</b></td><td>₹{price:,.2f}</td></tr>
          {"<tr><td><b>Target Price</b></td><td>₹{:,.2f}</td></tr>".format(target) if target else ""}
          {"<tr><td><b>Stop Loss</b></td><td>₹{:,.2f}</td></tr>".format(stop_loss) if stop_loss else ""}
        </table>
        <hr style="border-color:#e5e7eb;margin:16px 0">
        <p><b>Reason:</b> {reason}</p>
        <p style="color:#6b7280;font-size:12px">
          This is an AI-generated recommendation. You are the final decision maker.
          Never invest more than 10% of your portfolio in a single stock.
        </p>
      </div>
    </body></html>
    """
