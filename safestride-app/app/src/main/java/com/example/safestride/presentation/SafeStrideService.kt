package com.example.safestride.presentation

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
        serviceScope.launch {
            try {
                udpSocket?.close()
                val socket = DatagramSocket(null as SocketAddress?).apply {
                    reuseAddress = true
                    bind(InetSocketAddress(9000))
                }
                udpSocket = socket

                Log.d("SafeStrideUDP", "UDP Server listening on port 9000")
                val buffer = ByteArray(1024)

                while (isActive) {
                    val packet = DatagramPacket(buffer, buffer.size)
                    udpSocket?.receive(packet)

                    val status = String(packet.data, 0, packet.length).trim()
                    Log.d("SafeStrideUDP", "Received UDP packet: $status")

                    withContext(Dispatchers.Main) {
                        // We translate the new strings back to the old ones just for the haptics engine
                        val hapticCommand = when (status) {
                            "> 30M AWAY" -> "Slow"
                            "15-30M AWAY" -> "Medium"
                            "< 15M AWAY" -> "Fast"
                            "STOPPED OR GONE" -> "Stopped"
                            else -> null
                        }

                        if (hapticCommand != null) {
                            haptics.updatePulse(hapticCommand)
                            SafeStrideState.updateStatus(status) // Send the real text to the UI
                        } else {
                            Log.d("SafeStrideUDP", "Unknown status received: $status")
                        }
                    }
                }
            } catch (e: Exception) {
                if (isActive) Log.e("SafeStrideUDP", "UDP Server Error", e)
            } finally {
                udpSocket?.close()
                udpSocket = null
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val status = intent?.getStringExtra("STATUS")
        if (status == "Stopped") {
            Log.d("SafeStrideUDP", "Manual stop triggered from UI")
            haptics.updatePulse("Stopped")
            SafeStrideState.updateStatus("Stopped")

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