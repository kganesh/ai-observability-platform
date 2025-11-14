package com.example.telemetry.config;

@Configuration
public class OpenTelemetryConfig {

    @Bean
    public OpenTelemetry openTelemetry() {
        return SdkTracerProvider.builder().build();
    }
}
