package com.example.financegpt.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.financegpt.network.DashboardResponse
import com.example.financegpt.network.RetrofitClient
import kotlinx.coroutines.launch

@Composable
fun DashboardScreen(token: String) {
    var dashboardData by remember { mutableStateOf<DashboardResponse?>(null) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        coroutineScope.launch {
            try {
                val response = RetrofitClient.apiService.getDashboard("Bearer $token")
                dashboardData = response
            } catch (e: Exception) {
                errorMessage = e.message
            }
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "Dashboard", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(24.dp))

        if (errorMessage != null) {
            Text(text = "Error: $errorMessage", color = MaterialTheme.colorScheme.error)
        } else if (dashboardData == null) {
            CircularProgressIndicator()
        } else {
            Card(
                modifier = Modifier.fillMaxWidth().padding(8.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(text = "Total Balance", style = MaterialTheme.typography.titleMedium)
                    Text(text = "₹${dashboardData!!.balance}", style = MaterialTheme.typography.headlineLarge)
                }
            }

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Card(modifier = Modifier.weight(1f).padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(text = "Income", style = MaterialTheme.typography.titleSmall)
                        Text(text = "₹${dashboardData!!.total_income}", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
                    }
                }
                Card(modifier = Modifier.weight(1f).padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(text = "Expense", style = MaterialTheme.typography.titleSmall)
                        Text(text = "₹${dashboardData!!.total_expense}", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.error)
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
            Text(text = "Total Transactions: ${dashboardData!!.transactions_count}", style = MaterialTheme.typography.bodyLarge)
        }
    }
}
