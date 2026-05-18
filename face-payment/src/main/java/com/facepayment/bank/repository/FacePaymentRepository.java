package com.facepayment.bank.repository;

import com.facepayment.bank.entity.FacePayment;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface FacePaymentRepository extends JpaRepository<FacePayment, Long> {
    Optional<FacePayment> findByUserId(Long userId);
}
