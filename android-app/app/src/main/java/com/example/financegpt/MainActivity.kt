package com.example.financegpt

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddCircle
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.example.financegpt.theme.FinanceGPTTheme
import com.example.financegpt.ui.ChatScreen
import com.example.financegpt.ui.DashboardScreen
import com.example.financegpt.ui.ScreenshotUploadScreen

class MainActivity : ComponentActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    enableEdgeToEdge()
    setContent {
      FinanceGPTTheme { 
        var selectedTab by remember { mutableStateOf(0) }
        val dummyToken = "dummy_token_for_now" // Replace with actual login token later

        Scaffold(
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(
                        icon = { Icon(Icons.Filled.Home, contentDescription = "Dashboard") },
                        label = { Text("Dashboard") },
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0 }
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Filled.AddCircle, contentDescription = "Scan") },
                        label = { Text("Scan") },
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1 }
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Filled.Send, contentDescription = "Chat") },
                        label = { Text("Chat") },
                        selected = selectedTab == 2,
                        onClick = { selectedTab = 2 }
                    )
                }
            }
        ) { innerPadding ->
            Surface(modifier = Modifier.fillMaxSize().padding(innerPadding), color = MaterialTheme.colorScheme.background) { 
                when (selectedTab) {
                    0 -> DashboardScreen(token = dummyToken)
                    1 -> ScreenshotUploadScreen(token = dummyToken)
                    2 -> ChatScreen(token = dummyToken)
                }
            }
        }
      }
    }
  }
}
