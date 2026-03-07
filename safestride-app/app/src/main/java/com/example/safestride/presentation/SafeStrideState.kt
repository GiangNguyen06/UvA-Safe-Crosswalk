package com.example.safestride.presentation

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

// A Singleton object that acts as a bridge between the Service and the UI
object SafeStrideState {
    private val _currentStatus = MutableStateFlow("Waiting...")
    val currentStatus: StateFlow<String> = _currentStatus

    fun updateStatus(newStatus: String) {
        _currentStatus.value = newStatus
    }
}