"""
car_notification.py — Android Auto notification integration.

Uses PyJNIus (bundled with Kivy for Android) to create a persistent
notification visible on the Android Auto car screen.

On desktop this module is a no-op.  On Android it requests the
POST_NOTIFICATIONS runtime permission (Android 13+), then creates a
persistent notification with VISIBILITY_PUBLIC so it appears on the
car screen.

Call ``create_car_notification()`` from your App's ``build()`` method.
The global ``_notification_status`` string is updated at every step and
can be read by ``get_notification_status()`` for on-screen debugging.
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

# System icon: ic_dialog_info (always valid monochrome notification icon).
# The app's colored launcher icon causes silent notification failures
# on Android 13+ because notification small icons must be monochrome.
_SMALL_ICON_RES_ID = 16903401

# On-screen debug status (read by main.py HUD label)
_notification_status = ["initializing..."]


def get_notification_status() -> str:
    """Return the current notification creation status for on-screen HUD."""
    return _notification_status[0]


def _toast(activity, msg: str) -> None:
    """Show a brief Android Toast, swallowing any errors."""
    try:
        Toast = autoclass('android.widget.Toast')
        Toast.makeText(activity, msg, Toast.LENGTH_LONG).show()
    except Exception:
        pass


def _check_notification_permission(activity) -> bool:
    """Check if POST_NOTIFICATIONS is granted (Android 13+ / API 33+)."""
    _notification_status[0] = "checking permission..."
    try:
        ContextCompat = autoclass(
            'androidx.core.content.ContextCompat')
        result = ContextCompat.checkSelfPermission(
            activity, 'android.permission.POST_NOTIFICATIONS')
        granted = (result == 0)
        print(f"[car_notification] POST_NOTIFICATIONS: "
              f"{'granted' if granted else 'DENIED'} (result={result})")
        return granted
    except Exception as e:
        # AndroidX unavailable or pre-API 33 — assume granted
        print(f"[car_notification] Permission check skipped: {e}")
        return True


def _request_notification_permission(activity) -> None:
    """Request POST_NOTIFICATIONS runtime permission (Android 13+)."""
    try:
        ActivityCompat = autoclass(
            'androidx.core.app.ActivityCompat')
        ActivityCompat.requestPermissions(
            activity, ['android.permission.POST_NOTIFICATIONS'], 0)
        print("[car_notification] Permission dialog requested")
        _notification_status[0] = "waiting for permission dialog..."
    except Exception as e:
        print(f"[car_notification] Permission request failed: {e}")


def create_car_notification(
        title: str = "Bouncing Ball Simulator",
        text: str = "Tap to launch the bouncing ball") -> bool:
    """Create a persistent notification visible on Android Auto.

    Returns True on success, False if permission was requested
    (retry follows) or an error occurred.
    """
    _notification_status[0] = "starting..."

    if not _HAS_JNIUS:
        print("[car_notification] jnius not available — desktop mode")
        _notification_status[0] = "jnius not available (desktop)"
        return False

    print("[car_notification] Starting notification creation...")
    _notification_status[0] = "loading Android classes..."

    try:
        # -- Android Java classes ---------------------------------------
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        Notification = autoclass('android.app.Notification')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')

        activity = PythonActivity.mActivity
        print(f"[car_notification] Activity obtained: {activity}")

        # -- Check POST_NOTIFICATIONS permission (Android 13+) ----------
        has_permission = _check_notification_permission(activity)

        if not has_permission:
            print("[car_notification] Permission not granted — requesting...")
            _request_notification_permission(activity)
            _toast(activity,
                   "Tap to enable notifications for Android Auto")
            # Schedule retry after user has time to respond
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: create_car_notification(title, text), 3.0)
            return False

        print("[car_notification] Permission granted — creating notification")
        _notification_status[0] = "creating notification..."

        # -- Create notification channel (Android 8.0+) -----------------
        notification_manager = cast(
            'android.app.NotificationManager',
            activity.getSystemService(Context.NOTIFICATION_SERVICE))

        channel = NotificationChannel(
            _CHANNEL_ID,
            title,
            NotificationManager.IMPORTANCE_DEFAULT)
        channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC)
        notification_manager.createNotificationChannel(channel)
        print("[car_notification] Channel created")

        # -- Build the notification --------------------------------------
        builder = NotificationBuilder(activity, _CHANNEL_ID)
        builder.setContentTitle(title)
        builder.setContentText(text)
        builder.setOngoing(True)
        builder.setOnlyAlertOnce(True)
        builder.setAutoCancel(False)
        builder.setLocalOnly(False)

        # *** CRITICAL: must be VISIBILITY_PUBLIC for Android Auto ***
        builder.setVisibility(Notification.VISIBILITY_PUBLIC)
        builder.setCategory(Notification.CATEGORY_SERVICE)

        # Small icon — system icon (always valid on Android 13+)
        builder.setSmallIcon(_SMALL_ICON_RES_ID)

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
        print("[car_notification] Notification posted successfully!")
        _notification_status[0] = "notification created!"
        _toast(activity, "Android Auto notification created!")

        return True

    except Exception as exc:
        print(f"[car_notification] ERROR: {exc}")
        _notification_status[0] = f"error: {exc}"
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
