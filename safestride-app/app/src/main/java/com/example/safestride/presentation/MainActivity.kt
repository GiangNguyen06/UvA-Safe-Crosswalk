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
import androidx.compose.ui.unit.sp

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
                Text(text = "Pro Tip!", color = Color.Cyan)
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
        // Updated to look for the new waiting text
        val backgroundColor = when (currentStatus) {
            "> 30M AWAY" -> Color(0xFFE4C200)
            "15-30M AWAY" -> Color(0xFFFF9800)
            "< 15M AWAY" -> Color(0xFFF44336)
            "STOPPED OR GONE" -> Color(0xFF4CAF50)
            "Waiting for camera connection..." -> Color.Black
            else -> Color.Black
        }

        // Updated to look for the new waiting text
        val iconRes = when (currentStatus) {
            "Waiting for camera connection..." -> R.drawable.ic_loading
            "STOPPED OR GONE" -> R.drawable.ic_walking
            else -> R.drawable.ic_stop_sign
        }

        // THE SMART TEXT LOGIC:
        // If we are waiting, just show the waiting text. If not, add "CAR IS "
        val displayText = if (currentStatus == "Waiting for camera connection...") {
            currentStatus
        } else {
            "CAR IS $currentStatus"
        }

        Box(
            modifier = Modifier.fillMaxSize().background(backgroundColor),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {

                Icon(
                    painter = painterResource(id = iconRes),
                    contentDescription = "Status Icon",
                    modifier = Modifier.size(42.dp),
                    tint = Color.White
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = displayText,
                    color = Color.White,
                    textAlign = TextAlign.Center,
                    fontSize = if (displayText.length > 20) 12.sp else 16.sp,
                    modifier = Modifier.padding(horizontal = 8.dp)
                )

                Spacer(modifier = Modifier.height(16.dp))

                Button(onClick = {
                    updateService("Stopped")
                    (context as? ComponentActivity)?.finish()
                }) { Text("Exit") }
            }
        }
    }
}