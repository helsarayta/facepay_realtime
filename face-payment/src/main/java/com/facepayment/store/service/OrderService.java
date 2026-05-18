package com.facepayment.store.service;

import com.facepayment.bank.entity.BankAccount;
import com.facepayment.bank.entity.FacePayment;
import com.facepayment.bank.entity.User;
import com.facepayment.bank.repository.BankAccountRepository;
import com.facepayment.bank.repository.FacePaymentRepository;
import com.facepayment.bank.repository.UserRepository;
import com.facepayment.bank.service.BankAccountService;
import com.facepayment.bank.service.FaceService;
import com.facepayment.store.dto.request.CheckoutRequest;
import com.facepayment.store.dto.response.OrderResponse;
import com.facepayment.store.entity.Order;
import com.facepayment.store.entity.OrderItem;
import com.facepayment.store.entity.Product;
import com.facepayment.store.repository.OrderRepository;
import com.facepayment.store.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OrderService {

    private final UserRepository userRepository;
    private final FacePaymentRepository facePaymentRepository;
    private final ProductRepository productRepository;
    private final OrderRepository orderRepository;
    private final BankAccountRepository bankAccountRepository;
    private final BankAccountService bankAccountService;
    private final FaceService faceService;

    @Transactional
    public OrderResponse checkout(CheckoutRequest request) {
        User user = userRepository.findById(request.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("USER_NOT_FOUND: User not found"));

        FacePayment facePayment = facePaymentRepository.findByUserId(request.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("FACE_NOT_ACTIVE: Face payment not activated"));

        if (!"ACTIVE".equals(facePayment.getStatus())) {
            throw new IllegalArgumentException("FACE_NOT_ACTIVE: Please activate face payment first");
        }

        // Validate products and calculate total
        List<OrderItem> orderItems = new ArrayList<>();
        BigDecimal total = BigDecimal.ZERO;

        for (CheckoutRequest.CheckoutItem item : request.getItems()) {
            Product product = productRepository.findById(item.getProductId())
                    .orElseThrow(() -> new IllegalArgumentException("PRODUCT_NOT_FOUND: Product not found: " + item.getProductId()));

            if (product.getStock() < item.getQuantity()) {
                throw new IllegalArgumentException("OUT_OF_STOCK: Insufficient stock for: " + product.getName());
            }

            BigDecimal subtotal = product.getPrice().multiply(BigDecimal.valueOf(item.getQuantity()));
            total = total.add(subtotal);

            orderItems.add(OrderItem.builder()
                    .product(product)
                    .quantity(item.getQuantity())
                    .price(product.getPrice())
                    .build());
        }

        // Check balance
        BankAccount account = bankAccountService.getByUserId(request.getUserId());
        if (account.getBalance().compareTo(total) < 0) {
            throw new IllegalArgumentException("INSUFFICIENT_BALANCE: Insufficient balance");
        }

        // Face verification
        FaceService.FaceVerifyResult verifyResult = faceService.verifyFace(request.getUserId());

        // Save order first (captures intent regardless of result)
        Order order = orderRepository.save(Order.builder()
                .user(user)
                .totalAmount(total)
                .status(verifyResult.match() ? "SUCCESS" : "FAILED")
                .build());

        // Link items to order
        for (OrderItem item : orderItems) {
            item.setOrder(order);
        }
        order.setItems(orderItems);
        orderRepository.save(order);

        if (!verifyResult.match()) {
            throw new IllegalArgumentException("FACE_MISMATCH: Face verification failed. Order rejected.");
        }

        // Deduct balance and reduce stock
        BankAccount updated = bankAccountService.deductBalance(request.getUserId(), total);
        for (CheckoutRequest.CheckoutItem item : request.getItems()) {
            Product product = productRepository.findById(item.getProductId()).get();
            product.setStock(product.getStock() - item.getQuantity());
            productRepository.save(product);
        }

        // Build response
        List<OrderResponse.OrderItemDetail> itemDetails = orderItems.stream()
                .map(i -> OrderResponse.OrderItemDetail.builder()
                        .productName(i.getProduct().getName())
                        .quantity(i.getQuantity())
                        .unitPrice(i.getPrice())
                        .subtotal(i.getPrice().multiply(BigDecimal.valueOf(i.getQuantity())))
                        .build())
                .toList();

        return OrderResponse.builder()
                .orderId(order.getId())
                .userId(request.getUserId())
                .status("SUCCESS")
                .items(itemDetails)
                .totalAmount(total)
                .remainingBalance(updated.getBalance())
                .build();
    }

    public List<OrderResponse> getOrderHistory(Long userId) {
        return orderRepository.findByUserIdOrderByCreatedAtDesc(userId)
                .stream()
                .map(order -> OrderResponse.builder()
                        .orderId(order.getId())
                        .userId(userId)
                        .status(order.getStatus())
                        .totalAmount(order.getTotalAmount())
                        .build())
                .toList();
    }
}
