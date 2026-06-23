package com.example.financegpt.network

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST

interface ApiService {
    @POST("/chat")
    suspend fun sendChatMessage(
        @Header("Authorization") token: String,
        @Body request: ChatRequest
    ): TransactionResponse

    @GET("/dashboard")
    suspend fun getDashboard(
        @Header("Authorization") token: String
    ): DashboardResponse

    @retrofit2.http.Multipart
    @POST("/upload-screenshot")
    suspend fun uploadScreenshot(
        @Header("Authorization") token: String,
        @retrofit2.http.Part file: okhttp3.MultipartBody.Part
    ): TransactionResponse
}
