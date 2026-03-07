package com.example.safestride.presentation

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
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.edit
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.Icon
import androidx.wear.compose.material3.Text
import com.example.safestride.R
import com.example.safestride.presentation.theme.SafeStrideTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SafeStrideTheme {
                SafeStrideApp(this)
            }
        }
    }
}

@Composable
fun SafeStrideApp(context: Context) {
    val currentStatus by SafeStrideState.currentStatus.collectAsState()

    val prefs = context.getSharedPreferences("SafeStridePrefs", Context.MODE_PRIVATE)
    var showOnboarding by remember { mutableStateOf(prefs.getBoolean("FIRST_RUN", true)) }

    fun updateService(status: String) {
        val intent = Intent(context, SafeStrideService::class.java).apply {
            putExtra("STATUS", status)
        }
        context.startForegroundService(intent)
    }

    LaunchedEffect(Unit) {
        updateService("Init")
    }

    if (showOnboarding) {
        Box(
            modifier = Modifier.fillMaxSize().background(Color.DarkGray).padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(text = "Pro Tip:", color = Color.Green)
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "For quick access, map your watch's double-press crown shortcut to SafeStride in Settings > Gestures.",
                    color = Color.White,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(12.dp))
                Button(onClick = {
                    prefs.edit { putBoolean("FIRST_RUN", false) }
                    showOnboarding = false
                }) { Text("Got it") }
            }
        }
    } else {
        // Updated colors based on new status text
        val backgroundColor = when (currentStatus) {
            "> 30M AWAY" -> Color(0xFFE4C200) // Darker Yellow for better contrast on wear OS
            "15-30M AWAY" -> Color(0xFFFF9800) // Orange
            "< 15M AWAY" -> Color(0xFFF44336) // Red
            "STOPPED OR GONE" -> Color(0xFF4CAF50) // Green
            "Waiting..." -> Color.Black
            else -> Color.Black
        }

        // Dynamic icon switching
        val iconRes = when (currentStatus) {
            "Waiting..." -> R.drawable.ic_loading
            "STOPPED OR GONE" -> R.drawable.ic_walking
            else -> R.drawable.ic_stop_sign
        }

        Box(
            modifier = Modifier.fillMaxSize().background(backgroundColor),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {

                // The dynamic Icon replaces the title text
                Icon(
                    painter = painterResource(id = iconRes),
                    contentDescription = "Status Icon",
                    modifier = Modifier.size(42.dp),
                    tint = Color.White
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Updated text string format
                Text(
                    text = "CAR IS $currentStatus",
                    color = Color.White,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Manual trigger buttons removed! Exit remains.
                Button(onClick = {
                    updateService("Stopped")
                    (context as? ComponentActivity)?.finish()
                }) { Text("Exit") }
            }
        }
    }
}