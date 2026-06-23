package com.example.financegpt.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.financegpt.network.RetrofitClient
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

@Composable
fun ScreenshotUploadScreen(token: String) {
    var imageUri by remember { mutableStateOf<Uri?>(null) }
    var uploadStatus by remember { mutableStateOf("") }
    var isUploading by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    val galleryLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        imageUri = uri
        uploadStatus = ""
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = "Scan UPI Screenshot", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(32.dp))

        if (imageUri != null) {
            Text(text = "Image Selected!", color = MaterialTheme.colorScheme.primary)
            Spacer(modifier = Modifier.height(16.dp))
        } else {
            Text(text = "No image selected", color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(modifier = Modifier.height(16.dp))
        }

        Button(onClick = { galleryLauncher.launch("image/*") }) {
            Text(text = "Pick Screenshot from Gallery")
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                imageUri?.let { uri ->
                    isUploading = true
                    uploadStatus = "Uploading and analyzing..."
                    coroutineScope.launch {
                        try {
                            val inputStream = context.contentResolver.openInputStream(uri)
                            val bytes = inputStream?.readBytes() ?: ByteArray(0)
                            inputStream?.close()

                            val requestFile = bytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
                            val body = MultipartBody.Part.createFormData("file", "screenshot.jpg", requestFile)

                            val response = RetrofitClient.apiService.uploadScreenshot("Bearer $token", body)
                            uploadStatus = "Success!\nAmount: ₹${response.amount}\nCategory: ${response.category}\nDesc: ${response.description}"
                        } catch (e: Exception) {
                            uploadStatus = "Error: ${e.message}"
                        } finally {
                            isUploading = false
                        }
                    }
                }
            },
            enabled = imageUri != null && !isUploading
        ) {
            if (isUploading) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Processing...")
            } else {
                Text(text = "Upload to AI")
            }
        }

        Spacer(modifier = Modifier.height(24.dp))
        
        if (uploadStatus.isNotEmpty()) {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(text = uploadStatus, modifier = Modifier.padding(16.dp))
            }
        }
    }
}
