package com.facepayment.bank.service;

import com.facepayment.bank.dto.request.PaymentRequest;
import com.facepayment.bank.dto.response.PaymentResponse;
import com.facepayment.bank.entity.BankAccount;
import com.facepayment.bank.entity.FacePayment;
import com.facepayment.bank.repository.FacePaymentRepository;
import com.facepayment.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
@RequiredArgsConstructor
public class PaymentService {

    private final UserRepository userRepository;
    private final FacePaymentRepository facePaymentRepository;
    private final BankAccountService bankAccountService;
    private final FaceService faceService;

    @Transactional
    public PaymentResponse pay(PaymentRequest request, MultipartFile faceImage) {
        if (!userRepository.existsById(request.getUserId())) {
            throw new IllegalArgumentException("USER_NOT_FOUND: User not found");
        }

        FacePayment facePayment = facePaymentRepository.findByUserId(request.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("FACE_NOT_ACTIVE: Face payment not activated"));

        if (!"ACTIVE".equals(facePayment.getStatus())) {
            throw new IllegalArgumentException("FACE_NOT_ACTIVE: Please activate face payment first");
        }

        BankAccount account = bankAccountService.getByUserId(request.getUserId());
        if (account.getBalance().compareTo(request.getAmount()) < 0) {
            throw new IllegalArgumentException("INSUFFICIENT_BALANCE: Insufficient balance");
        }

        FaceService.FaceVerifyResult result = faceService.verifyFace(request.getUserId(), faceImage);
        if (!result.match()) {
            throw new IllegalArgumentException("FACE_MISMATCH: Face verification failed. Transaction rejected.");
        }

        BankAccount updated = bankAccountService.deductBalance(request.getUserId(), request.getAmount());

        return PaymentResponse.builder()
                .userId(request.getUserId())
                .amount(request.getAmount())
                .remainingBalance(updated.getBalance())
                .description(request.getDescription())
                .build();
    }
}
