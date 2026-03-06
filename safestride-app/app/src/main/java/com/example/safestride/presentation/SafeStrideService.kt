package com.example.safestride.presentation

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket

class SafeStrideService : Service() {
    private lateinit var haptics: CrosswalkHaptics
    // We use Coroutines to run the UDP server in the background
    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)

    override fun onCreate() {
        super.onCreate()
        haptics = CrosswalkHaptics(this)
        createSilentNotificationChannel()

        val notification = NotificationCompat.Builder(this, "safestride_channel")
            .setContentTitle("SafeStride Active")
            .setContentText("Monitoring UDP status")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .build()

        startForeground(1, notification)

        // START THE UDP SERVER
        startUdpServer()
    }

    private fun startUdpServer() {
        serviceScope.launch {
            try {
                // Listen on port 9000 (standard unprivileged port)
                val socket = DatagramSocket(9000)
                Log.d("SafeStrideUDP", "UDP Server listening on port 9000")

                val buffer = ByteArray(1024)

                while (isActive) {
                    val packet = DatagramPacket(buffer, buffer.size)
                    // The 'receive' command pauses here until a packet arrives
                    socket.receive(packet)

                    // Convert the incoming bytes to a String
                    val status = String(packet.data, 0, packet.length).trim()
                    Log.d("SafeStrideUDP", "Received UDP packet: $status")

                    // Map the status string to our haptic pulses
                    // We switch to the Main thread to update the haptics
                    withContext(Dispatchers.Main) {
                        when (status) {
                            "Slow", "Medium", "Fast", "Stopped" -> haptics.updatePulse(status)
                            else -> Log.d("SafeStrideUDP", "Unknown status received: $status")
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e("SafeStrideUDP", "UDP Server Error", e)
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // We no longer need the MainActivity to send commands.
        // The service now reacts to UDP packets directly.
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        // Cancel the coroutine job when the service is destroyed
        serviceJob.cancel()
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