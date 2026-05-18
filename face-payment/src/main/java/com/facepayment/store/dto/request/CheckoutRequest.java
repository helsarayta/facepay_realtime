package com.facepayment.store.dto.request;

import jakarta.validation.constraints.*;
import lombok.Data;
import java.util.List;

@Data
public class CheckoutRequest {

    @NotNull(message = "User ID is required")
    private Long userId;

    @NotEmpty(message = "Items cannot be empty")
    private List<CheckoutItem> items;

    @Data
    public static class CheckoutItem {
        @NotNull(message = "Product ID is required")
        private Long productId;

        @NotNull(message = "Quantity is required")
        @Min(value = 1, message = "Quantity must be at least 1")
        private Integer quantity;
    }
}
