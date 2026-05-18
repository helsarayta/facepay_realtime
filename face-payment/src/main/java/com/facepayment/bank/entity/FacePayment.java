package com.facepayment.bank.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "face_payment")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FacePayment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "file_path", length = 255)
    private String filePath;

    @Column(nullable = false, length = 20)
    @Builder.Default
    private String status = "INACTIVE";

    @Column(name = "activated_at")
    private LocalDateTime activatedAt;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
