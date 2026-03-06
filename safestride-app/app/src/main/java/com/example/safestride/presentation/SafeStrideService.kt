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
    // We use Coroutines to run the UDP server in the background
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

        // START THE UDP SERVER
        startUdpServer()
    }

    private fun startUdpServer() {
        serviceScope.launch {
            try {
                // Ensure any previous socket is closed
                udpSocket?.close()

                // Use SO_REUSEADDR to avoid "Address already in use" errors during restarts
                val socket = DatagramSocket(null as SocketAddress?).apply {
                    reuseAddress = true
                    bind(InetSocketAddress(9000))
                }
                udpSocket = socket
                
                Log.d("SafeStrideUDP", "UDP Server listening on port 9000")

                val buffer = ByteArray(1024)

                while (isActive) {
                    val packet = DatagramPacket(buffer, buffer.size)

                    // The 'receive' command pauses here until a packet arrives
                    udpSocket?.receive(packet)

                    val status = String(packet.data, 0, packet.length).trim()
                    Log.d("SafeStrideUDP", "Received UDP packet: $status")

                    withContext(Dispatchers.Main) {
                        when (status) {
                            "Slow", "Medium", "Fast", "Stopped" -> {
                                haptics.updatePulse(status)
                                // ADD THIS LINE: Broadcast the new status to the UI!
                                SafeStrideState.updateStatus(status)
                            }
                            else -> Log.d("SafeStrideUDP", "Unknown status received: $status")
                        }
                    }
                }
            } catch (e: Exception) {
                if (isActive) {
                    Log.e("SafeStrideUDP", "UDP Server Error", e)
                } else {
                    Log.d("SafeStrideUDP", "UDP Socket closed normally")
                }
            } finally {
                udpSocket?.close()
                udpSocket = null
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
        // Forcefully close the socket port when the service is killed!
        udpSocket?.close()
        udpSocket = null
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