package com.facepayment.store.controller;

import com.facepayment.common.ApiResponse;
import com.facepayment.store.dto.request.CheckoutRequest;
import com.facepayment.store.dto.response.OrderResponse;
import com.facepayment.store.service.OrderService;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/store/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;
    private final ObjectMapper objectMapper;
    private final Validator validator;

    @PostMapping(value = "/checkout", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ApiResponse<OrderResponse>> checkout(
            @RequestPart("data") String dataJson,
            @RequestPart("face") MultipartFile faceImage) throws Exception {
        CheckoutRequest request = objectMapper.readValue(dataJson, CheckoutRequest.class);
        Set<ConstraintViolation<CheckoutRequest>> violations = validator.validate(request);
        if (!violations.isEmpty()) {
            String msg = violations.stream().map(ConstraintViolation::getMessage).collect(Collectors.joining(", "));
            return ResponseEntity.badRequest().body(ApiResponse.error("VALIDATION_ERROR", msg));
        }
        OrderResponse response = orderService.checkout(request, faceImage);
        return ResponseEntity.ok(ApiResponse.success("Order successful", response));
    }

    @GetMapping("/{userId}")
    public ResponseEntity<ApiResponse<List<OrderResponse>>> history(@PathVariable Long userId) {
        return ResponseEntity.ok(ApiResponse.success(orderService.getOrderHistory(userId)));
    }
}
