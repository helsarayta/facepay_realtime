package com.facepayment.bank.controller;

import com.facepayment.bank.dto.response.ActivateFaceResponse;
import com.facepayment.bank.entity.FacePayment;
import com.facepayment.bank.repository.FacePaymentRepository;
import com.facepayment.bank.repository.UserRepository;
import com.facepayment.bank.service.FaceService;
import com.facepayment.common.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/face")
@RequiredArgsConstructor
public class FaceController {

    private final FaceService faceService;
    private final FacePaymentRepository facePaymentRepository;
    private final UserRepository userRepository;

    @PostMapping("/activate/{userId}")
    public ResponseEntity<ApiResponse<ActivateFaceResponse>> activate(@PathVariable Long userId) {
        if (!userRepository.existsById(userId)) {
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("USER_NOT_FOUND", "User not found"));
        }

        FacePayment facePayment = facePaymentRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("USER_NOT_FOUND: User not found"));

        if ("ACTIVE".equals(facePayment.getStatus())) {
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("FACE_ALREADY_ACTIVE", "Face payment already activated"));
        }

        boolean enrolled = faceService.enrollFace(userId);
        if (!enrolled) {
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("ENROLL_FAILED", "Face enrollment failed. Please try again."));
        }

        facePayment.setFilePath("face_dataset/" + userId + ".npy");
        facePayment.setStatus("ACTIVE");
        facePayment.setActivatedAt(LocalDateTime.now());
        facePaymentRepository.save(facePayment);

        return ResponseEntity.ok(ApiResponse.success(ActivateFaceResponse.builder()
                .userId(userId)
                .facePaymentStatus("ACTIVE")
                .message("Face payment activated successfully")
                .build()));
    }

    @GetMapping("/status/{userId}")
    public ResponseEntity<ApiResponse<ActivateFaceResponse>> status(@PathVariable Long userId) {
        FacePayment facePayment = facePaymentRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("USER_NOT_FOUND: User not found"));

        return ResponseEntity.ok(ApiResponse.success(ActivateFaceResponse.builder()
                .userId(userId)
                .facePaymentStatus(facePayment.getStatus())
                .build()));
    }
}
