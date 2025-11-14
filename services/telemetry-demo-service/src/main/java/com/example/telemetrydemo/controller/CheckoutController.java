package com.example.telemetrydemo.controller;

import com.example.telemetrydemo.service.CheckoutService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/checkout")
public class CheckoutController {

    private final CheckoutService checkoutService;

    public CheckoutController(CheckoutService checkoutService) {
        this.checkoutService = checkoutService;
    }

    /**
     * GET /checkout?scenario=normal|slow|error
     */
    @GetMapping
    public ResponseEntity<String> checkout(
            @RequestParam(name = "scenario", defaultValue = "normal") String scenario) {

        String result = checkoutService.performCheckout(scenario);
        return ResponseEntity.ok(result);
    }
}