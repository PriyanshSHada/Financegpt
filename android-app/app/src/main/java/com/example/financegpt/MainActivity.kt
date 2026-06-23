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
import androidx.compose.ui.platform.LocalContext
import com.example.financegpt.data.AuthManager
import com.example.financegpt.theme.FinanceGPTTheme
import com.example.financegpt.ui.ChatScreen
import com.example.financegpt.ui.DashboardScreen
import com.example.financegpt.ui.LoginScreen
import com.example.financegpt.ui.RegisterScreen
import com.example.financegpt.ui.ScreenshotUploadScreen

enum class ScreenState {
    LOGIN, REGISTER, MAIN_APP
}

class MainActivity : ComponentActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    enableEdgeToEdge()
    setContent {
      FinanceGPTTheme { 
        val context = LocalContext.current
        val authManager = remember { AuthManager(context) }
        
        var currentScreen by remember { 
            mutableStateOf(if (authManager.isLoggedIn()) ScreenState.MAIN_APP else ScreenState.LOGIN) 
        }

        when (currentScreen) {
            ScreenState.LOGIN -> {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    LoginScreen(
                        onLoginSuccess = { token ->
                            authManager.saveToken(token)
                            currentScreen = ScreenState.MAIN_APP
                        },
                        onNavigateToRegister = {
                            currentScreen = ScreenState.REGISTER
                        }
                    )
                }
            }
            ScreenState.REGISTER -> {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    RegisterScreen(
                        onRegisterSuccess = {
                            currentScreen = ScreenState.LOGIN
                        },
                        onNavigateToLogin = {
                            currentScreen = ScreenState.LOGIN
                        }
                    )
                }
            }
            ScreenState.MAIN_APP -> {
                MainAppNavigation(
                    token = authManager.getToken() ?: "",
                    onLogout = {
                        authManager.clearToken()
                        currentScreen = ScreenState.LOGIN
                    }
                )
            }
        }
      }
    }
  }
}

@Composable
fun MainAppNavigation(token: String, onLogout: () -> Unit) {
    var selectedTab by remember { mutableStateOf(0) }

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
                0 -> DashboardScreen(token = token, onLogout = onLogout)
                1 -> ScreenshotUploadScreen(token = token)
                2 -> ChatScreen(token = token)
            }
        }
    }
}
