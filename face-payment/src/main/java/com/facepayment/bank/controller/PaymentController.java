package com.facepayment.bank.controller;

import com.facepayment.bank.dto.request.PaymentRequest;
import com.facepayment.bank.dto.response.PaymentResponse;
import com.facepayment.bank.service.PaymentService;
import com.facepayment.common.ApiResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/payment")
@RequiredArgsConstructor
public class PaymentController {

    private final PaymentService paymentService;
    private final ObjectMapper objectMapper;

    @PostMapping(value = "/pay", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ApiResponse<PaymentResponse>> pay(
            @RequestPart("data") String dataJson,
            @RequestPart("face") MultipartFile faceImage) throws Exception {
        PaymentRequest request = objectMapper.readValue(dataJson, PaymentRequest.class);
        PaymentResponse response = paymentService.pay(request, faceImage);
        return ResponseEntity.ok(ApiResponse.success("Payment successful", response));
    }
}
