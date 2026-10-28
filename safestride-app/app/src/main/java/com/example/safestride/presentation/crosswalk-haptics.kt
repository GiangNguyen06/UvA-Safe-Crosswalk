package com.example.safestride.presentation

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log

class CrosswalkHaptics(context: Context) {

    // This safely gets the vibration hardware for both newer and older Wear OS versions
    private val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
        vibratorManager.defaultVibrator
    } else {
        @Suppress("DEPRECATION")
        context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
    }

    // ADDED THIS: A variable to remember the last state we triggered
    private var lastStatus: String = "None"

    fun updatePulse(status: String) {
        // THE FIX: If the status hasn't changed, do nothing! Let the current vibration loop play out.
        if (status == lastStatus) {
            return
        }

        // If it is a new status, update our memory
        lastStatus = status

        // Stop any current vibration before starting the new one
        vibrator.cancel()

        Log.d("CrosswalkApp", "Triggering new vibration for status: $status")

        val timings: LongArray
        val amplitudes: IntArray

        // MAP THE EXACT PYTHON STRINGS TO THE VIBRATION PATTERNS
        when (status) {
            "> 30M AWAY" -> {
                // A very relaxed radar ping: Wait 0ms, Vibrate 200ms, Pause for 2000ms
                timings = longArrayOf(0, 200, 2000)
                amplitudes = intArrayOf(0, 255, 0)
            }
            "15-30M AWAY" -> {
                // A distinct DOUBLE-TAP: Wait 0, Vib 200, Pause 200, Vib 200, Pause 800
                timings = longArrayOf(0, 200, 200, 200, 800)
                amplitudes = intArrayOf(0, 255, 0, 255, 0)
            }
            "< 15M AWAY" -> {
                // Fastest Emergency Pulse: Wait 0, Vib 200, Pause 50ms
                timings = longArrayOf(0, 200, 50)
                amplitudes = intArrayOf(0, 255, 0)
            }
            "STOPPED OR GONE", "Stopped" -> {
                Log.d("CrosswalkApp", "Vibration stopped.")
                return
            }
            else -> {
                Log.d("CrosswalkApp", "Unknown status received by haptics: $status")
                return
            }
        }

        // The '0' tells the watch to repeat this pattern in an infinite loop
        val effect = VibrationEffect.createWaveform(timings, amplitudes, 0)
        vibrator.vibrate(effect)
    }
}