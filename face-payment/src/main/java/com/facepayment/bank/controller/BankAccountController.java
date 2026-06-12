package com.facepayment.bank.controller;

import com.facepayment.bank.dto.response.RegisterResponse;
import com.facepayment.bank.entity.BankAccount;
import com.facepayment.bank.service.BankAccountService;
import com.facepayment.bank.service.UserService;
import com.facepayment.common.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.Map;

@RestController
@RequestMapping("/api/bank")
@RequiredArgsConstructor
public class BankAccountController {

    private final BankAccountService bankAccountService;
    private final UserService userService;

    @GetMapping("/account/{userId}")
    public ResponseEntity<ApiResponse<RegisterResponse>> getAccount(@PathVariable Long userId) {
        RegisterResponse profile = userService.getProfile(userId);
        return ResponseEntity.ok(ApiResponse.success(profile));
    }

    @PostMapping("/account/topup")
    public ResponseEntity<ApiResponse<Map<String, Object>>> topUp(@RequestBody Map<String, Object> body) {
        Long userId = Long.valueOf(body.get("userId").toString());
        BigDecimal amount = new BigDecimal(body.get("amount").toString());
        BankAccount account = bankAccountService.topUp(userId, amount);
        return ResponseEntity.ok(ApiResponse.success("Top-up successful", Map.of(
                "balance", account.getBalance(),
                "accountNumber", account.getAccountNumber()
        )));
    }
}
