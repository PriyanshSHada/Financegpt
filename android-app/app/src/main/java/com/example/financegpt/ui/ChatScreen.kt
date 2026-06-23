package com.example.financegpt.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.financegpt.network.ChatRequest
import com.example.financegpt.network.RetrofitClient
import kotlinx.coroutines.launch

@Composable
fun ChatScreen(token: String) {
    var messages by remember { mutableStateOf(listOf<String>()) }
    var inputText by remember { mutableStateOf("") }
    val coroutineScope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text(text = "FinanceGPT Chat", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        
        LazyColumn(modifier = Modifier.weight(1f)) {
            items(messages) { message ->
                Surface(
                    color = if (message.startsWith("You:")) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.secondaryContainer,
                    shape = MaterialTheme.shapes.medium,
                    modifier = Modifier.padding(vertical = 4.dp).fillMaxWidth()
                ) {
                    Text(text = message, modifier = Modifier.padding(12.dp))
                }
            }
        }

        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Spent 120 on chai...") }
            )
            Spacer(modifier = Modifier.width(8.dp))
            Button(onClick = {
                val userMessage = inputText
                if (userMessage.isNotBlank()) {
                    messages = messages + "You: $userMessage"
                    inputText = ""
                    coroutineScope.launch {
                        try {
                            val response = RetrofitClient.apiService.sendChatMessage(
                                token = "Bearer $token",
                                request = ChatRequest(userMessage)
                            )
                            val botResponse = "Saved! Amount: ${response.amount}, Category: ${response.category}, Type: ${response.type}"
                            messages = messages + "FinanceGPT: $botResponse"
                        } catch (e: Exception) {
                            messages = messages + "FinanceGPT: Error - ${e.message}"
                        }
                    }
                }
            }) {
                Text("Send")
            }
        }
    }
}
