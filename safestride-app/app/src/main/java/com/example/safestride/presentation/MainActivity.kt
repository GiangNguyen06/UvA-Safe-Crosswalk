package com.example.safestride.presentation

import androidx.compose.foundation.shape.CircleShape
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.edit
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.ButtonDefaults
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
        // App Background Color
        val backgroundColor = when (currentStatus) {
            "> 30M AWAY" -> Color(0xFFFFFF00) // Pure bright yellow
            "15-30M AWAY" -> Color(0xFFFF9800) // Orange
            "< 15M AWAY" -> Color(0xFFF44336) // Red
            "STOPPED OR GONE" -> Color(0xFF4CAF50) // Green
            "Waiting for camera connection..." -> Color.Black
            else -> Color.Black
        }

        // Status Text & Icon Color
        val contentColor = when (currentStatus) {
            "> 30M AWAY", "15-30M AWAY", "< 15M AWAY" -> Color.Black
            else -> Color.White // STOPPED OR GONE and Waiting default to white
        }

        // Exit Button Background Color
        val exitButtonColor = when (currentStatus) {
            "> 30M AWAY" -> Color(0xFF9C9C0C)
            "15-30M AWAY" -> Color(0xFF9E4F0B)
            "< 15M AWAY" -> Color(0xFF8B0303)
            "STOPPED OR GONE" -> Color(0xFF006520)
            else -> Color.Black
        }

        val iconRes = when (currentStatus) {
            "Waiting for camera connection..." -> R.drawable.ic_loading
            "STOPPED OR GONE" -> R.drawable.ic_walking
            "> 30M AWAY" -> R.drawable.ic_warning
            else -> R.drawable.ic_stop_sign
        }

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
                    tint = contentColor // Dynamic icon color
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = displayText,
                    color = contentColor, // Dynamic text color
                    textAlign = TextAlign.Center,
                    fontWeight = FontWeight.Bold, // Bold text
                    fontSize = if (displayText.length > 20) 12.sp else 16.sp,
                    modifier = Modifier.padding(horizontal = 8.dp)
                )

                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    onClick = {
                        updateService("Stopped")
                        (context as? ComponentActivity)?.finish()
                    },
                    modifier = Modifier.size(64.dp),
                    shape = CircleShape,
                    contentPadding = PaddingValues(0.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = exitButtonColor,
                        contentColor = Color.White
                    )
                ) {
                    // THE FIX: A Box that fills the circle and perfectly centers the text inside it
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Exit",
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                    }
                }
            }
        }
    }
}