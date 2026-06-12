package com.facepayment.bank.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class FaceService {

    private final RestTemplate restTemplate;

    @Value("${face.service.url}")
    private String faceServiceUrl;

    public boolean enrollFace(Long userId, MultipartFile[] files) {
        try {
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("user_id", userId.toString());
            for (MultipartFile file : files) {
                final byte[] bytes = file.getBytes();
                body.add("files", new ByteArrayResource(bytes) {
                    @Override public String getFilename() { return "face.jpg"; }
                });
            }
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            Map response = restTemplate.postForObject(
                    faceServiceUrl + "/enroll", new HttpEntity<>(body, headers), Map.class);
            if (response != null && Boolean.TRUE.equals(response.get("success"))) {
                log.info("Face enrolled for user {} ({} samples)", userId, response.get("samples"));
                return true;
            }
        } catch (Exception e) {
            log.error("Face enrollment failed for user {}: {}", userId, e.getMessage());
        }
        return false;
    }

    public FaceVerifyResult verifyFace(Long userId, MultipartFile file) {
        try {
            final byte[] bytes = file.getBytes();
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("user_id", userId.toString());
            body.add("file", new ByteArrayResource(bytes) {
                @Override public String getFilename() { return "face.jpg"; }
            });
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            Map response = restTemplate.postForObject(
                    faceServiceUrl + "/verify", new HttpEntity<>(body, headers), Map.class);
            if (response != null) {
                boolean match = Boolean.TRUE.equals(response.get("match"));
                double score = response.get("score") != null
                        ? ((Number) response.get("score")).doubleValue() : 0.0;
                log.info("Face verify user {}: match={}, score={}", userId, match, score);
                return new FaceVerifyResult(match, score);
            }
        } catch (Exception e) {
            log.error("Face verification failed for user {}: {}", userId, e.getMessage());
        }
        return new FaceVerifyResult(false, 0.0);
    }

    public record FaceVerifyResult(boolean match, double score) {}
}
