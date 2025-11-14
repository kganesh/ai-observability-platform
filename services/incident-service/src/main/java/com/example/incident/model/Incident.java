package com.example.incident.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.List;

@Entity
@Table(name = "incidents")
public class Incident {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String title;

    @Column(name = "service_name")
    private String serviceName;

    private String status;   // open, investigating, resolved

    @Column(name = "first_seen")
    private Instant firstSeen;

    @Column(name = "last_seen")
    private Instant lastSeen;

    @Column(name = "rca_text", columnDefinition = "TEXT")
    private String rcaText;

    @OneToMany(mappedBy = "incident", fetch = FetchType.LAZY)
    private List<Anomaly> anomalies;

    // getters and setters omitted for brevity, but you should generate them
    // (or use Lombok if you prefer)
    
    // ...getters & setters...
}