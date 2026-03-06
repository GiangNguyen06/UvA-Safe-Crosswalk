package com.example.safestride.presentation

import androidx.compose.runtime.collectAsState
import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.Text
import com.example.safestride.presentation.theme.SafeStrideTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SafeStrideTheme {
                // We pass the "Context" (this) so the UI can start the background service
                SafeStrideApp(this)
            }
        }
    }
}

@Composable
fun SafeStrideApp(context: Context) {
    // The UI now actively listens to the shared bridge!
    val currentStatus by SafeStrideState.currentStatus.collectAsState()

    val prefs = context.getSharedPreferences("SafeStridePrefs", Context.MODE_PRIVATE)
    var showOnboarding by remember { mutableStateOf(prefs.getBoolean("FIRST_RUN", true)) }

    fun updateService(status: String) {
        val intent = Intent(context, SafeStrideService::class.java).apply {
            putExtra("STATUS", status)
        }
        context.startForegroundService(intent)
    }

    // --- ADDED THIS BLOCK ---
    // This tells Compose to run the code inside exactly once when the app opens.
    // By passing "Stopped", it safely wakes up the service to start listening
    // to UDP packets without immediately triggering any haptic vibrations.
    LaunchedEffect(Unit) {
        updateService("Stopped")
    }

    // --- SCREEN 1: THE ONBOARDING POP-UP ---
    if (showOnboarding) {
        Box(
            modifier = Modifier.fillMaxSize().background(Color.DarkGray).padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(text = "Pro Tip!", color = Color.Cyan)
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "For quick access, map your watch's double-press crown shortcut to SafeStride in Settings > Gestures.",
                    color = Color.White,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(12.dp))
                Button(onClick = {
                    // Save to memory so they never see this again
                    prefs.edit().putBoolean("FIRST_RUN", false).apply()
                    showOnboarding = false
                }) { Text("Got it") }
            }
        }
    }
    // --- SCREEN 2: THE MAIN UI ---
    else {
        val backgroundColor = when (currentStatus) {
            "Slow" -> Color(0xFF4CAF50)
            "Medium" -> Color(0xFFFF9800)
            "Fast" -> Color(0xFFF44336)
            else -> Color.DarkGray
        }

        Box(
            modifier = Modifier.fillMaxSize().background(backgroundColor),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(text = "SafeStride", color = Color.Green)
                Spacer(modifier = Modifier.height(8.dp))
                Text(text = "Status: $currentStatus", color = Color.White)
                Spacer(modifier = Modifier.height(16.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { updateService("Slow") }) { Text("Low") }
                    Button(onClick = { updateService("Medium") }) { Text("Med") }
                    Button(onClick = { updateService("Fast") }) { Text("Hi") }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Button(onClick = { updateService("Stopped") }) { Text("Stop") }
            }
        }
    }
}