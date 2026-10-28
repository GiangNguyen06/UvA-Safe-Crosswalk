package com.example.safestride.presentation

import android.content.Context
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetSocketAddress
import java.net.SocketAddress

class SafeStrideService : Service() {
    private lateinit var haptics: CrosswalkHaptics
    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)

    private var udpSocket: DatagramSocket? = null

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

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(1, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(1, notification)
        }

        startUdpServer()
    }

    private fun startUdpServer() {
        serviceScope.launch(Dispatchers.IO) {

            // 1. WAKE UP THE WI-FI ANTENNA FOR BROADCASTS
            val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as android.net.wifi.WifiManager
            val multicastLock = wifiManager.createMulticastLock("SafeStrideLock")
            multicastLock.setReferenceCounted(true)
            multicastLock.acquire()
            Log.d("SafeStrideUDP", "Multicast Lock Acquired - Wi-Fi is awake!")

            try {
                udpSocket?.close()

                // 2. OPEN THE SOCKET AND ENABLE BROADCASTS
                val socket = DatagramSocket(null).apply {
                    reuseAddress = true
                    broadcast = true // CRITICAL: Allows 255.255.255.255 messages
                    bind(InetSocketAddress("0.0.0.0", 9000))
                }
                udpSocket = socket

                Log.d("SafeStrideUDP", "UDP Server listening for Broadcasts on port 9000")
                val buffer = ByteArray(1024)

                while (isActive) {
                    val packet = DatagramPacket(buffer, buffer.size)
                    udpSocket?.receive(packet)

                    val status = String(packet.data, 0, packet.length).trim()
                    Log.d("SafeStrideUDP", "Received UDP packet: $status")

                    withContext(Dispatchers.Main) {
                        // Pass the exact string to the haptics and UI
                        haptics.updatePulse(status)
                        SafeStrideState.updateStatus(status)
                    }
                }
            } catch (e: Exception) {
                if (isActive) Log.e("SafeStrideUDP", "UDP Server Error", e)
            } finally {
                // 3. CLEAN UP TO SAVE BATTERY
                udpSocket?.close()
                udpSocket = null

                if (multicastLock.isHeld) {
                    multicastLock.release()
                    Log.d("SafeStrideUDP", "Multicast Lock Released")
                }
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val status = intent?.getStringExtra("STATUS")

        // 1. NEW LOGIC: When the app first opens, force the UI back to the waiting state
        if (status == "Init") {
            SafeStrideState.updateStatus("Waiting for camera connection...")
        }

        // 2. UPDATED LOGIC: When Exit is pressed, kill the haptics but reset the UI memory
        if (status == "Stopped") {
            Log.d("SafeStrideUDP", "Manual stop triggered from UI")
            haptics.updatePulse("Stopped") // This tells the motor to stop vibrating

            // THE FIX: Reset the UI state instead of saving "Stopped"
            SafeStrideState.updateStatus("Waiting for camera connection...")

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                stopForeground(STOP_FOREGROUND_REMOVE)
            } else {
                @Suppress("DEPRECATION")
                stopForeground(true)
            }
            stopSelf()
        }

        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceJob.cancel()
        udpSocket?.close()
        udpSocket = null
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createSilentNotificationChannel() {
        val channel = NotificationChannel(
            "safestride_channel",
            "SafeStride Background Service",
            NotificationManager.IMPORTANCE_LOW
        ).apply { enableVibration(false) }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }
}