package com.facepayment.bank.dto.response;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ActivateFaceResponse {
    private Long userId;
    private String facePaymentStatus;
    private String message;
}
