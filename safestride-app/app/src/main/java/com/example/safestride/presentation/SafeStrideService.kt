package com.example.safestride.presentation

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

class SafeStrideService : Service() {
    private lateinit var haptics: CrosswalkHaptics

    override fun onCreate() {
        super.onCreate()
        // Initialize haptics here in the background service!
        haptics = CrosswalkHaptics(this)

        createSilentNotificationChannel()

        // Build the ongoing silent notification
        val notification = NotificationCompat.Builder(this, "safestride_channel")
            .setContentTitle("SafeStride Active")
            .setContentText("Monitoring crosswalk status")
            .setSmallIcon(android.R.drawable.ic_dialog_info) // Default system icon
            .setOngoing(true) // Prevents the user from swiping it away
            .build()

        // This tells Android: "Do not kill this app, it is doing important work!"
        startForeground(1, notification)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // When MainActivity sends a status update, change the haptic pulse
        val status = intent?.getStringExtra("STATUS") ?: "Stopped"
        haptics.updatePulse(status)

        // If we get a "Stopped" command, we can kill the background service to save battery
        if (status == "Stopped") {
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }

        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createSilentNotificationChannel() {
        val channel = NotificationChannel(
            "safestride_channel",
            "SafeStride Background Service",
            NotificationManager.IMPORTANCE_LOW // IMPORTANCE_LOW prevents vibration/sound!
        ).apply {
            enableVibration(false)
        }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }
}