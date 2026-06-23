package com.example.financegpt.network

data class ChatRequest(val message: String)

data class TransactionResponse(
    val id: Int,
    val amount: Double,
    val category: String,
    val description: String,
    val type: String,
    val date: String,
    val owner_id: Int
)

data class DashboardResponse(
    val balance: Double,
    val total_income: Double,
    val total_expense: Double,
    val transactions_count: Int
)
