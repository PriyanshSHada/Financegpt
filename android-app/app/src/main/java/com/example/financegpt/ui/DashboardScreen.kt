package com.example.financegpt.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.financegpt.network.BudgetRequest
import com.example.financegpt.network.BudgetResponse
import com.example.financegpt.network.DashboardResponse
import com.example.financegpt.network.RetrofitClient
import kotlinx.coroutines.launch

@Composable
fun DashboardScreen(token: String, onLogout: () -> Unit = {}) {
    var dashboardData by remember { mutableStateOf<DashboardResponse?>(null) }
    var budgets by remember { mutableStateOf<List<BudgetResponse>>(emptyList()) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    
    var showBudgetDialog by remember { mutableStateOf(false) }
    var newBudgetCategory by remember { mutableStateOf("") }
    var newBudgetAmount by remember { mutableStateOf("") }
    
    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        coroutineScope.launch {
            try {
                dashboardData = RetrofitClient.apiService.getDashboard("Bearer $token")
                budgets = RetrofitClient.apiService.getBudgets("Bearer $token")
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
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Text(text = "Total Balance", style = MaterialTheme.typography.titleMedium)
                        TextButton(onClick = onLogout) {
                            Text("Logout", color = MaterialTheme.colorScheme.error)
                        }
                    }
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
            Spacer(modifier = Modifier.height(24.dp))
            
            Row(modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text(text = "Active Budgets", style = MaterialTheme.typography.titleMedium)
                IconButton(onClick = { showBudgetDialog = true }) {
                    Icon(Icons.Filled.Add, contentDescription = "Add Budget")
                }
            }

            budgets.forEach { budget ->
                val spent = dashboardData!!.category_expenses[budget.category] ?: 0.0
                val progress = if (budget.limit_amount > 0) (spent / budget.limit_amount).toFloat().coerceIn(0f, 1f) else 0f
                val progressColor = if (progress >= 0.9f) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary

                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(text = budget.category, style = MaterialTheme.typography.bodyLarge)
                            Text(text = "₹$spent / ₹${budget.limit_amount}", style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = { progress },
                            modifier = Modifier.fillMaxWidth(),
                            color = progressColor
                        )
                    }
                }
            }
        }
    }

    if (showBudgetDialog) {
        AlertDialog(
            onDismissRequest = { showBudgetDialog = false },
            title = { Text("Create New Budget") },
            text = {
                Column {
                    OutlinedTextField(
                        value = newBudgetCategory,
                        onValueChange = { newBudgetCategory = it },
                        label = { Text("Category (e.g. Food, Travel)") }
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = newBudgetAmount,
                        onValueChange = { newBudgetAmount = it },
                        label = { Text("Limit Amount (₹)") }
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    val amount = newBudgetAmount.toDoubleOrNull()
                    if (newBudgetCategory.isNotBlank() && amount != null) {
                        coroutineScope.launch {
                            try {
                                val req = BudgetRequest(newBudgetCategory, amount)
                                val newBudget = RetrofitClient.apiService.createBudget("Bearer $token", req)
                                budgets = budgets + newBudget
                                showBudgetDialog = false
                                newBudgetCategory = ""
                                newBudgetAmount = ""
                            } catch (e: Exception) {
                                errorMessage = "Failed to create budget: ${e.message}"
                            }
                        }
                    }
                }) {
                    Text("Save")
                }
            },
            dismissButton = {
                TextButton(onClick = { showBudgetDialog = false }) { Text("Cancel") }
            }
        )
    }
}
