package com.facepayment.store.dto.response;

import lombok.Builder;
import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

@Data
@Builder
public class OrderResponse {
    private Long orderId;
    private Long userId;
    private String status;
    private List<OrderItemDetail> items;
    private BigDecimal totalAmount;
    private BigDecimal remainingBalance;

    @Data
    @Builder
    public static class OrderItemDetail {
        private String productName;
        private Integer quantity;
        private BigDecimal unitPrice;
        private BigDecimal subtotal;
    }
}
