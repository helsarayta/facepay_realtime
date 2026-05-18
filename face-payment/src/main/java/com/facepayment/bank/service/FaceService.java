package com.facepayment.bank.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class FaceService {

    private final RestTemplate restTemplate;

    @Value("${face.service.url}")
    private String faceServiceUrl;

    public boolean enrollFace(Long userId) {
        try {
            String url = faceServiceUrl + "/enroll";
            Map<String, Object> body = Map.of("user_id", userId);
            Map response = restTemplate.postForObject(url, body, Map.class);
            if (response != null && Boolean.TRUE.equals(response.get("success"))) {
                log.info("Face enrolled successfully for user {}", userId);
                return true;
            }
        } catch (Exception e) {
            log.error("Face enrollment failed for user {}: {}", userId, e.getMessage());
        }
        return false;
    }

    public FaceVerifyResult verifyFace(Long userId) {
        try {
            String url = faceServiceUrl + "/verify";
            Map<String, Object> body = Map.of("user_id", userId);
            Map response = restTemplate.postForObject(url, body, Map.class);
            if (response != null) {
                boolean match = Boolean.TRUE.equals(response.get("match"));
                double score = response.get("score") != null
                        ? ((Number) response.get("score")).doubleValue() : 0.0;
                log.info("Face verify result for user {}: match={}, score={}", userId, match, score);
                return new FaceVerifyResult(match, score);
            }
        } catch (Exception e) {
            log.error("Face verification failed for user {}: {}", userId, e.getMessage());
        }
        return new FaceVerifyResult(false, 0.0);
    }

    public record FaceVerifyResult(boolean match, double score) {}
}
