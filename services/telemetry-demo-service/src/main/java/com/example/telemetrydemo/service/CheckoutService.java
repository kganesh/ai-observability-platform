package com.example.telemetrydemo.service;

import io.micrometer.observation.annotation.Observed;
import org.springframework.stereotype.Service;

import java.util.Random;

@Service
public class CheckoutService {

    private final Random random = new Random();

    /**
     * Simulates a checkout operation.
     * @param scenario normal | slow | error
     */
    @Observed(name = "checkout.operation", contextualName = "checkout-flow")
    public String performCheckout(String scenario) {
        long start = System.currentTimeMillis();

        try {
            if ("slow".equalsIgnoreCase(scenario)) {
                // Simulate latency spike
                Thread.sleep(800 + random.nextInt(400));
            } else if ("error".equalsIgnoreCase(scenario)) {
                // Simulate error
                throw new RuntimeException("Simulated checkout failure");
            } else {
                // Normal behavior with small jitter
                Thread.sleep(50 + random.nextInt(50));
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        long duration = System.currentTimeMillis() - start;
        return "Checkout completed in " + duration + " ms (scenario=" + scenario + ")";
    }
}