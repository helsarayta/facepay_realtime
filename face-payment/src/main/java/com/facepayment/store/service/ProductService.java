package com.facepayment.store.service;

import com.facepayment.store.dto.response.ProductResponse;
import com.facepayment.store.entity.Product;
import com.facepayment.store.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    public List<ProductResponse> getAllAvailable() {
        return productRepository.findByStockGreaterThan(0)
                .stream()
                .map(ProductResponse::from)
                .toList();
    }

    public ProductResponse getById(Long id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("PRODUCT_NOT_FOUND: Product not found"));
        return ProductResponse.from(product);
    }

    public ProductResponse addProduct(Product product) {
        return ProductResponse.from(productRepository.save(product));
    }
}
