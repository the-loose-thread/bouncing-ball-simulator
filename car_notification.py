"""
car_notification.py — Android Auto notification integration.

Uses PyJNIus (bundled with Kivy for Android) to create a persistent
notification that appears on the Android Auto car screen.  Tapping the
notification from the car's display launches the bouncing-ball app.

On desktop platforms this module is a complete no-op (all functions
return ``False``) so it can be imported unconditionally.

Key fixes:
  - POST_NOTIFICATIONS runtime permission check (Android 13+ / API 33)
  - System icon (ic_dialog_info) instead of app launcher icon
  - VISIBILITY_PUBLIC on both channel and notification
  - setLocalOnly(false) so Android Auto displays it
  - Toast feedback for debugging on device
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

# Android system icon: ic_dialog_info (always valid monochrome notification icon)
# Using app launcher icon on Android 13+ causes silent notification failures
# because launcher icons are colored — notification icons MUST be monochrome.
_SMALL_ICON_RES_ID = 16903401


def _toast(activity, msg: str) -> None:
    """Show a brief Android Toast, swallowing any errors."""
    try:
        Toast = autoclass('android.widget.Toast')
        Toast.makeText(activity, msg, Toast.LENGTH_LONG).show()
    except Exception:
        pass


def _check_notification_permission(activity) -> bool:
    """Check if POST_NOTIFICATIONS is granted (Android 13+ / API 33).

    On devices below API 33 this always returns True.
    """
    try:
        ContextCompat = autoclass('androidx.core.content.ContextCompat')
        # PERMISSION_GRANTED = 0 in Android
        result = ContextCompat.checkSelfPermission(
            activity, 'android.permission.POST_NOTIFICATIONS')
        granted = (result == 0)
        print(f"[car_notification] POST_NOTIFICATIONS permission: "
              f"{'granted' if granted else 'DENIED'} (result={result})")
        return granted
    except Exception as e:
        # AndroidX or pre-API 33 — assume permission is granted
        print(f"[car_notification] Permission check skipped: {e}")
        return True


def _request_notification_permission(activity) -> None:
    """Request POST_NOTIFICATIONS runtime permission (Android 13+)."""
    try:
        ActivityCompat = autoclass('androidx.core.app.ActivityCompat')
        ActivityCompat.requestPermissions(
            activity, ['android.permission.POST_NOTIFICATIONS'], 0)
        print("[car_notification] Permission dialog requested")
    except Exception as e:
        print(f"[car_notification] Permission request failed: {e}")


def create_car_notification(
        title: str = "Bouncing Ball Simulator",
        text: str = "Tap to launch the bouncing ball") -> bool:
    """Create a persistent notification visible on Android Auto.

    Returns ``True`` on success, ``False`` if the permission was
    requested (retry will follow) or if creation failed.
    """
    if not _HAS_JNIUS:
        print("[car_notification] jnius not available — desktop mode")
        return False

    print("[car_notification] Starting notification creation...")

    try:
        # -- Android Java classes ---------------------------------------
        PythonActivity       = autoclass('org.kivy.android.PythonActivity')
        Context              = autoclass('android.content.Context')
        Notification         = autoclass('android.app.Notification')
        NotificationBuilder  = autoclass('android.app.Notification$Builder')
        NotificationManager  = autoclass('android.app.NotificationManager')
        NotificationChannel  = autoclass('android.app.NotificationChannel')
        Intent               = autoclass('android.content.Intent')
        PendingIntent        = autoclass('android.app.PendingIntent')

        activity = PythonActivity.mActivity
        print(f"[car_notification] Activity obtained: {activity}")

        # -- Check POST_NOTIFICATIONS permission (Android 13+) ----------
        has_permission = _check_notification_permission(activity)

        if not has_permission:
            print("[car_notification] Permission not granted — requesting...")
            _request_notification_permission(activity)
            _toast(activity, "Tapping to enable notifications — please accept")
            # Schedule retry after user has time to respond to the dialog
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: create_car_notification(title, text), 3.0)
            return False

        # -- Create notification channel (Android 8.0+) -----------------
        notification_manager = cast(
            'android.app.NotificationManager',
            activity.getSystemService(Context.NOTIFICATION_SERVICE))
        print("[car_notification] NotificationManager obtained")

        channel = NotificationChannel(
            _CHANNEL_ID,
            title,
            NotificationManager.IMPORTANCE_DEFAULT)    # visible, no sound
        channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC)
        notification_manager.createNotificationChannel(channel)
        print("[car_notification] Channel created")

        # -- Build the notification --------------------------------------
        builder = NotificationBuilder(activity, _CHANNEL_ID)
        builder.setContentTitle(title)
        builder.setContentText(text)
        builder.setOngoing(True)            # persistent — won't auto-dismiss
        builder.setOnlyAlertOnce(True)      # don't beep on rebuilds
        builder.setAutoCancel(False)        # don't dismiss when tapped
        builder.setLocalOnly(False)         # show on Android Auto too

        # *** CRITICAL: must be VISIBILITY_PUBLIC for Android Auto ***
        builder.setVisibility(Notification.VISIBILITY_PUBLIC)

        # Category hint so Android Auto places it in the status tray
        builder.setCategory(Notification.CATEGORY_SERVICE)

        # Small icon — MUST be monochrome. Use system icon (always valid).
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
        _toast(activity, "Android Auto notification created!")

        return True

    except Exception as exc:
        print(f"[car_notification] ERROR: {exc}")
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
