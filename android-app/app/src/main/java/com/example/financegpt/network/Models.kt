package com.example.financegpt.network

data class ChatRequest(val message: String)

data class TransactionResponse(
    val id: Int,
    val amount: Double,
    val category: String,
    val description: String,
    val type: String
)

data class DashboardResponse(
    val balance: Double,
    val total_income: Double,
    val total_expense: Double,
    val transactions_count: Int,
    val category_expenses: Map<String, Double>
)

data class TokenResponse(
    val access_token: String,
    val token_type: String
)

data class UserResponse(
    val id: Int,
    val username: String
)

data class BudgetRequest(
    val category: String,
    val limit_amount: Double
)

data class BudgetResponse(
    val id: Int,
    val category: String,
    val limit_amount: Double,
    val owner_id: Int
)

