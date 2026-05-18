package com.facepayment.bank.controller;

import com.facepayment.bank.dto.request.PaymentRequest;
import com.facepayment.bank.dto.response.PaymentResponse;
import com.facepayment.bank.service.PaymentService;
import com.facepayment.common.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/payment")
@RequiredArgsConstructor
public class PaymentController {

    private final PaymentService paymentService;

    @PostMapping("/pay")
    public ResponseEntity<ApiResponse<PaymentResponse>> pay(@Valid @RequestBody PaymentRequest request) {
        PaymentResponse response = paymentService.pay(request);
        return ResponseEntity.ok(ApiResponse.success("Payment successful", response));
    }
}
