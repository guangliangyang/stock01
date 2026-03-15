from typing import List
from winotify import Notification, audio

from src.models.stock import AlertItem
from src.utils.logger import get_logger
from src.i18n import tr

logger = get_logger(__name__)


class ToastNotifier:
    """Windows toast notification handler."""

    def __init__(self, app_id: str = None):
        self.app_id = app_id or tr("app_name")

    def show_sell_alert(self, alert: AlertItem) -> bool:
        """Show a sell alert notification.

        Args:
            alert: Alert item containing stock info.

        Returns:
            True if notification was shown successfully.
        """
        try:
            toast = Notification(
                app_id=tr("app_name"),
                title=tr("notifications.sell_alert", name=alert.stock_name),
                msg=tr("notifications.sell_alert_msg",
                       code=alert.stock_code,
                       yield_value=f"{alert.current_yield:.2f}",
                       threshold=f"{alert.threshold:.2f}"),
                duration="long"
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            logger.info(f"Showed sell alert for {alert.stock_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False

    def show_multiple_alerts(self, alerts: List[AlertItem]) -> int:
        """Show notifications for multiple alerts.

        Args:
            alerts: List of alert items.

        Returns:
            Number of notifications successfully shown.
        """
        if not alerts:
            return 0

        # If multiple alerts, show summary notification
        if len(alerts) > 3:
            try:
                toast = Notification(
                    app_id=tr("app_name"),
                    title=tr("notifications.multiple_alerts", count=len(alerts)),
                    msg=tr("notifications.multiple_alerts_msg"),
                    duration="long"
                )
                toast.set_audio(audio.Default, loop=False)
                toast.show()
                logger.info(f"Showed summary alert for {len(alerts)} stocks")
                return 1
            except Exception as e:
                logger.error(f"Failed to show summary notification: {e}")
                return 0

        # Show individual notifications
        success_count = 0
        for alert in alerts:
            if self.show_sell_alert(alert):
                success_count += 1

        return success_count

    def show_screening_complete(self, count: int) -> bool:
        """Show notification when screening is complete.

        Args:
            count: Number of qualifying stocks found.

        Returns:
            True if notification was shown successfully.
        """
        try:
            toast = Notification(
                app_id=tr("app_name"),
                title=tr("notifications.screening_complete"),
                msg=tr("notifications.screening_complete_msg", count=count),
                duration="short"
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            logger.info(f"Showed screening complete notification")
            return True
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False

    def show_info(self, title: str, message: str) -> bool:
        """Show an informational notification.

        Args:
            title: Notification title.
            message: Notification message.

        Returns:
            True if notification was shown successfully.
        """
        try:
            toast = Notification(
                app_id=self.app_id,
                title=title,
                msg=message,
                duration="short"
            )
            toast.show()
            return True
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False
