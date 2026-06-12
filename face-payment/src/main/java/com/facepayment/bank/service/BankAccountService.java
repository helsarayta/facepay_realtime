package com.facepayment.bank.service;

import com.facepayment.bank.entity.BankAccount;
import com.facepayment.bank.repository.BankAccountRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
@RequiredArgsConstructor
public class BankAccountService {

    private final BankAccountRepository bankAccountRepository;

    public BankAccount getByUserId(Long userId) {
        return bankAccountRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("ACCOUNT_NOT_FOUND: Bank account not found"));
    }

    @Transactional
    public BankAccount deductBalance(Long userId, BigDecimal amount) {
        BankAccount account = getByUserId(userId);
        if (account.getBalance().compareTo(amount) < 0) {
            throw new IllegalArgumentException("INSUFFICIENT_BALANCE: Insufficient balance");
        }
        account.setBalance(account.getBalance().subtract(amount));
        return bankAccountRepository.save(account);
    }

    @Transactional
    public BankAccount topUp(Long userId, BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("INVALID_AMOUNT: Amount must be greater than zero");
        }
        BankAccount account = getByUserId(userId);
        account.setBalance(account.getBalance().add(amount));
        return bankAccountRepository.save(account);
    }
}
