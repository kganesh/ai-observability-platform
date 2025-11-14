package com.example.incident.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "anomalies")
public class Anomaly {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "service_name")
    private String serviceName;

    @Column(name = "metric_name")
    private String metricName;

    private String severity;

    private Double value;

    @Column(name = "baseline")
    private Double baseline;

    @Column(name = "timestamp")
    private Instant timestamp;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "incident_id")
    private Incident incident;

    // getters & setters...
}