"""
car_notification.py — Android Auto notification integration.

Uses PyJNIus (bundled with Kivy for Android) to create a persistent
notification that appears on the Android Auto car screen.  Tapping the
notification from the car's display launches the bouncing-ball app.

On desktop platforms this module is a complete no-op (all functions
return ``None`` and print nothing) so it can be imported unconditionally.
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

# Notification ID — keeps the notification stable across updates
_CAR_NOTIFICATION_ID = 1001
_CHANNEL_ID = "bouncing_ball_channel"


def create_car_notification(
        title: str = "Bouncing Ball Simulator",
        text: str = "Tap to launch the bouncing ball") -> bool:
    """Create a persistent notification visible on Android Auto.

    Returns ``True`` on success, ``False`` otherwise.
    """
    if not _HAS_JNIUS:
        return False

    # -- Android Java classes --------------------------------------------
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')

    activity = PythonActivity.mActivity

    # -- Create notification channel (Android 8.0+) -------------------
    notification_manager = cast(
        'android.app.NotificationManager',
        activity.getSystemService(Context.NOTIFICATION_SERVICE))

    # IMPORTANCE_DEFAULT lets the notification appear without sound
    # on Android Auto's "status" area.
    channel = NotificationChannel(
        _CHANNEL_ID,
        title,
        NotificationManager.IMPORTANCE_DEFAULT)

    # Try setting category (best-effort on newer APIs)
    try:
        channel.setLockscreenVisibility(NotificationChannel.VISIBILITY_PUBLIC)
    except Exception:
        pass

    notification_manager.createNotificationChannel(channel)

    # -- Build the notification ------------------------------------------
    builder = NotificationBuilder(activity, _CHANNEL_ID)
    builder.setContentTitle(title)
    builder.setContentText(text)
    builder.setOngoing(True)          # persistent — won't auto-dismiss
    builder.setOnlyAlertOnce(True)   # don't beep on every rebuild

    # Small icon: fall back to app icon resource ID
    try:
        builder.setSmallIcon(activity.getApplicationInfo().icon)
    except Exception:
        # Last resort — use a default system icon (16903401 = ic_dialog_info)
        builder.setSmallIcon(16903401)

    # Category hint so Android Auto places it in the right tray
    # CATEGORY_SERVICE = 2 (constant in android.app.Notification)
    try:
        builder.setCategory(builder().getClass() \
            .getDeclaredField('CATEGORY_SERVICE').get(None))
    except Exception:
        pass

    # -- PendingIntent: tapping the notification opens the app ----------
    intent = Intent(activity, PythonActivity)
    intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP
                    | Intent.FLAG_ACTIVITY_CLEAR_TOP
                    | Intent.FLAG_ACTIVITY_NEW_TASK)

    pending_intent = PendingIntent.getActivity(
        activity, 0, intent,
        PendingIntent.FLAG_UPDATE_CURRENT
        | PendingIntent.FLAG_IMMUTABLE)

    builder.setContentIntent(pending_intent)

    # -- Show it ----------------------------------------------------------
    notification = builder.build()
    notification_manager.notify(_CAR_NOTIFICATION_ID, notification)

    return True


def remove_car_notification() -> None:
    """Remove the persistent notification (call on app exit)."""
    if not _HAS_JNIUS:
        return

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    NotificationManager = autoclass('android.app.NotificationManager')

    activity = PythonActivity.mActivity
    notification_manager = cast(
        'android.app.NotificationManager',
        activity.getSystemService(Context.NOTIFICATION_SERVICE))
    notification_manager.cancel(_CAR_NOTIFICATION_ID)
