package com.facepayment.bank.service;

import com.facepayment.bank.dto.request.RegisterRequest;
import com.facepayment.bank.dto.response.RegisterResponse;
import com.facepayment.bank.entity.BankAccount;
import com.facepayment.bank.entity.FacePayment;
import com.facepayment.bank.entity.User;
import com.facepayment.bank.repository.BankAccountRepository;
import com.facepayment.bank.repository.FacePaymentRepository;
import com.facepayment.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Random;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final BankAccountRepository bankAccountRepository;
    private final FacePaymentRepository facePaymentRepository;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public RegisterResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("EMAIL_EXISTS: Email already registered");
        }

        User user = userRepository.save(User.builder()
                .fullName(request.getFullName())
                .email(request.getEmail())
                .phone(request.getPhone())
                .password(passwordEncoder.encode(request.getPassword()))
                .build());

        String accountNumber = generateAccountNumber(user.getId());
        BankAccount account = bankAccountRepository.save(BankAccount.builder()
                .user(user)
                .accountNumber(accountNumber)
                .accountType(request.getAccountType())
                .balance(request.getInitialBalance())
                .build());

        facePaymentRepository.save(FacePayment.builder()
                .user(user)
                .status("INACTIVE")
                .build());

        return RegisterResponse.builder()
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phone(user.getPhone())
                .accountNumber(account.getAccountNumber())
                .accountType(account.getAccountType())
                .balance(account.getBalance())
                .facePaymentStatus("INACTIVE")
                .build();
    }

    public RegisterResponse getProfile(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("USER_NOT_FOUND: User not found"));

        BankAccount account = bankAccountRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("ACCOUNT_NOT_FOUND: Bank account not found"));

        FacePayment facePayment = facePaymentRepository.findByUserId(userId)
                .orElse(null);

        return RegisterResponse.builder()
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phone(user.getPhone())
                .accountNumber(account.getAccountNumber())
                .accountType(account.getAccountType())
                .balance(account.getBalance())
                .facePaymentStatus(facePayment != null ? facePayment.getStatus() : "INACTIVE")
                .build();
    }

    private String generateAccountNumber(Long userId) {
        int random = new Random().nextInt(900000) + 100000;
        return String.format("FP%05d%d", userId, random);
    }
}
