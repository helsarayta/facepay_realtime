package com.facepayment.bank.dto.response;

import lombok.Builder;
import lombok.Data;
import java.math.BigDecimal;

@Data
@Builder
public class RegisterResponse {
    private Long userId;
    private String fullName;
    private String email;
    private String phone;
    private String accountNumber;
    private String accountType;
    private BigDecimal balance;
    private String facePaymentStatus;
}
