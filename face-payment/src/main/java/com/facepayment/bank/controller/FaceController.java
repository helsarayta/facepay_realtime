package com.facepayment.bank.controller;

import com.facepayment.bank.dto.response.ActivateFaceResponse;
import com.facepayment.bank.entity.FacePayment;
import com.facepayment.bank.repository.FacePaymentRepository;
import com.facepayment.bank.repository.UserRepository;
import com.facepayment.bank.service.FaceService;
import com.facepayment.common.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/face")
@RequiredArgsConstructor
public class FaceController {

    private final FaceService faceService;
    private final FacePaymentRepository facePaymentRepository;
    private final UserRepository userRepository;

    @PostMapping(value = "/activate/{userId}", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ApiResponse<ActivateFaceResponse>> activate(
            @PathVariable Long userId,
            @RequestParam("files") MultipartFile[] files) {

        if (!userRepository.existsById(userId)) {
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("USER_NOT_FOUND", "User not found"));
        }

        FacePayment facePayment = facePaymentRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("USER_NOT_FOUND: User not found"));

        boolean enrolled = faceService.enrollFace(userId, files);
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
