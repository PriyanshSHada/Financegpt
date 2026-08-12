package com.example.financegpt.network

import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface ApiService {
    @POST("/chat")
    suspend fun sendChatMessage(
        @Body request: ChatRequest
    ): ChatResponse

    @POST("/register")
    suspend fun register(
        @Body user: Map<String, String> // username, password
    ): UserResponse

    @FormUrlEncoded
    @POST("/token")
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String
    ): TokenResponse

    @GET("/dashboard")
    suspend fun getDashboard(): DashboardResponse

    @GET("/budgets")
    suspend fun getBudgets(): List<BudgetResponse>

    @POST("/budgets")
    suspend fun createBudget(
        @Body request: BudgetRequest
    ): BudgetResponse

    @Multipart
    @POST("/upload-screenshot")
    suspend fun uploadScreenshot(
        @retrofit2.http.Part file: okhttp3.MultipartBody.Part
    ): TransactionResponse
}
