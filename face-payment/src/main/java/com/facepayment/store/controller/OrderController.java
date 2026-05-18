package com.facepayment.store.controller;

import com.facepayment.common.ApiResponse;
import com.facepayment.store.dto.request.CheckoutRequest;
import com.facepayment.store.dto.response.OrderResponse;
import com.facepayment.store.service.OrderService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/store/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    @PostMapping("/checkout")
    public ResponseEntity<ApiResponse<OrderResponse>> checkout(@Valid @RequestBody CheckoutRequest request) {
        OrderResponse response = orderService.checkout(request);
        return ResponseEntity.ok(ApiResponse.success("Order successful", response));
    }

    @GetMapping("/{userId}")
    public ResponseEntity<ApiResponse<List<OrderResponse>>> history(@PathVariable Long userId) {
        return ResponseEntity.ok(ApiResponse.success(orderService.getOrderHistory(userId)));
    }
}
