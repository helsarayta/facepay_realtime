package com.facepayment.bank.controller;

import com.facepayment.auth.JwtUtil;
import com.facepayment.bank.dto.request.LoginRequest;
import com.facepayment.bank.dto.response.LoginResponse;
import com.facepayment.bank.entity.User;
import com.facepayment.bank.repository.UserRepository;
import com.facepayment.common.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;
    private final UserRepository userRepository;

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<LoginResponse>> login(@Valid @RequestBody LoginRequest request) {
        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword())
            );
        } catch (BadCredentialsException e) {
            return ResponseEntity.status(401)
                    .body(ApiResponse.error("INVALID_CREDENTIALS", "Invalid email or password"));
        }

        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new IllegalArgumentException("USER_NOT_FOUND: User not found"));

        String token = jwtUtil.generateToken(user.getEmail(), user.getId());

        return ResponseEntity.ok(ApiResponse.success("Login successful",
                LoginResponse.builder()
                        .token(token)
                        .type("Bearer")
                        .userId(user.getId())
                        .fullName(user.getFullName())
                        .email(user.getEmail())
                        .build()));
    }
}
