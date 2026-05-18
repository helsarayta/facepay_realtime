package com.facepayment.bank.controller;

import com.facepayment.bank.dto.request.RegisterRequest;
import com.facepayment.bank.dto.response.RegisterResponse;
import com.facepayment.bank.service.UserService;
import com.facepayment.common.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<RegisterResponse>> register(@Valid @RequestBody RegisterRequest request) {
        RegisterResponse response = userService.register(request);
        return ResponseEntity.ok(ApiResponse.success("User registered successfully", response));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<RegisterResponse>> getProfile(@PathVariable Long id) {
        RegisterResponse response = userService.getProfile(id);
        return ResponseEntity.ok(ApiResponse.success(response));
    }
}
