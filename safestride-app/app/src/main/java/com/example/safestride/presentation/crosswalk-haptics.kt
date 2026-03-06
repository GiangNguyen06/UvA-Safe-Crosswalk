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

    fun updatePulse(status: String) {
        // Stop any current vibration before starting a new one
        vibrator.cancel()

        Log.d("CrosswalkApp", "Triggering vibration for status: $status")

        val timings: LongArray
        val amplitudes: IntArray

        when (status) {
            "Slow" -> {
                // Wait 0ms, Vibrate 200ms, Pause 1000ms
                timings = longArrayOf(0, 200, 1000)
                amplitudes = intArrayOf(0, 255, 0)
            }
            "Medium" -> {
                // Wait 0ms, Vibrate 200ms, Pause 500ms
                timings = longArrayOf(0, 200, 500)
                amplitudes = intArrayOf(0, 255, 0)
            }
            "Fast" -> {
                // Wait 0ms, Vibrate 150ms, Pause 150ms
                timings = longArrayOf(0, 150, 150)
                amplitudes = intArrayOf(0, 255, 0)
            }
            "Stopped" -> {
                Log.d("CrosswalkApp", "Vibration stopped.") // Log the stop too
                return
            }
            else -> return
        }

        // The '0' tells the watch to repeat this pattern in an infinite loop from the beginning
        val effect = VibrationEffect.createWaveform(timings, amplitudes, 0)
        vibrator.vibrate(effect)
    }
}