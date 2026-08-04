"""
car_notification.py — Android Auto notification integration.

Uses PyJNIus (bundled with Kivy for Android) to create a persistent
notification that appears on the Android Auto car screen.  Tapping the
notification from the car's display launches the bouncing-ball app.

On desktop platforms this module is a complete no-op (all functions
return ``False``) so it can be imported unconditionally.
"""

from kivy.utils import platform

# ------------------------------------------------------------------
# Guard: only import jnius on Android
# ------------------------------------------------------------------
_HAS_JNIUS = False
if platform == 'android':
    try:
        from jnius import autoclass, cast
        _HAS_JNIUS = True
    except ImportError:               # pragma: no cover
        _HAS_JNIUS = False

# Notification channel + ID
_CAR_NOTIFICATION_ID = 1001
_CHANNEL_ID = "bouncing_ball_channel"


def _toast(activity, msg: str) -> None:
    """Show a brief Android Toast, swallowing any errors."""
    try:
        Toast = autoclass('android.widget.Toast')
        Toast.makeText(activity, msg, Toast.LENGTH_LONG).show()
    except Exception:
        pass


def create_car_notification(
        title: str = "Bouncing Ball Simulator",
        text: str = "Tap to launch the bouncing ball") -> bool:
    """Create a persistent notification visible on Android Auto.

    Returns ``True`` on success, ``False`` otherwise.
    """
    if not _HAS_JNIUS:
        return False

    try:
        # -- Android Java classes ---------------------------------------
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context          = autoclass('android.content.Context')
        Notification     = autoclass('android.app.Notification')
        NotificationBuilder    = autoclass('android.app.Notification$Builder')
        NotificationManager    = autoclass('android.app.NotificationManager')
        NotificationChannel    = autoclass('android.app.NotificationChannel')
        Intent       = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')

        activity = PythonActivity.mActivity

        # -- Create notification channel (Android 8.0+) -----------------
        notification_manager = cast(
            'android.app.NotificationManager',
            activity.getSystemService(Context.NOTIFICATION_SERVICE))

        channel = NotificationChannel(
            _CHANNEL_ID,
            title,
            NotificationManager.IMPORTANCE_DEFAULT)          # no sound
        channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC)
        notification_manager.createNotificationChannel(channel)

        # -- Build the notification --------------------------------------
        builder = NotificationBuilder(activity, _CHANNEL_ID)
        builder.setContentTitle(title)
        builder.setContentText(text)
        builder.setOngoing(True)           # persistent — won't auto-dismiss
        builder.setOnlyAlertOnce(True)     # don't beep on rebuilds
        builder.setAutoCancel(False)       # don't dismiss when tapped
        builder.setLocalOnly(False)        # show on Android Auto too

        # *** CRITICAL: must be VISIBILITY_PUBLIC for Android Auto ***
        builder.setVisibility(Notification.VISIBILITY_PUBLIC)

        # Category hint so Android Auto places it in the status tray
        builder.setCategory(Notification.CATEGORY_SERVICE)

        # Small icon — use app icon resource ID, fallback to system icon
        try:
            builder.setSmallIcon(activity.getApplicationInfo().icon)
        except Exception:
            builder.setSmallIcon(16903401)   # ic_dialog_info

        # -- PendingIntent: tapping opens the app -----------------------
        intent = Intent(activity, PythonActivity)
        intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP
                        | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_NEW_TASK)

        pending_intent = PendingIntent.getActivity(
            activity, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT
            | PendingIntent.FLAG_IMMUTABLE)

        builder.setContentIntent(pending_intent)

        # -- Show it ----------------------------------------------------
        notification = builder.build()
        notification_manager.notify(_CAR_NOTIFICATION_ID, notification)

        _toast(activity, "Android Auto notification created!")
        return True

    except Exception as exc:
        _toast(activity, f"Notification error: {exc}")
        return False


def remove_car_notification() -> None:
    """Remove the persistent notification (call on app exit)."""
    if not _HAS_JNIUS:
        return

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')

        activity = PythonActivity.mActivity
        notification_manager = cast(
            'android.app.NotificationManager',
            activity.getSystemService(Context.NOTIFICATION_SERVICE))
        notification_manager.cancel(_CAR_NOTIFICATION_ID)
    except Exception:
        pass
