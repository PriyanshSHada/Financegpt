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
        @Header("Authorization") token: String,
        @Body request: ChatRequest
    ): TransactionResponse

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
    suspend fun getDashboard(
        @Header("Authorization") token: String
    ): DashboardResponse

    @GET("/budgets")
    suspend fun getBudgets(
        @Header("Authorization") token: String
    ): List<BudgetResponse>

    @POST("/budgets")
    suspend fun createBudget(
        @Header("Authorization") token: String,
        @Body request: BudgetRequest
    ): BudgetResponse

    @Multipart
    @POST("/upload-screenshot")
    suspend fun uploadScreenshot(
        @Header("Authorization") token: String,
        @retrofit2.http.Part file: okhttp3.MultipartBody.Part
    ): TransactionResponse
}
