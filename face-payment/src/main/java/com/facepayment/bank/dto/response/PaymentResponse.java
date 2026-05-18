package com.facepayment.bank.dto.response;

import lombok.Builder;
import lombok.Data;
import java.math.BigDecimal;

@Data
@Builder
public class PaymentResponse {
    private Long userId;
    private BigDecimal amount;
    private BigDecimal remainingBalance;
    private String description;
}
