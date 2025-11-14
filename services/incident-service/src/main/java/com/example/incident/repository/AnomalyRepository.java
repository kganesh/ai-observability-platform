package com.example.incident.repository;

import com.example.incident.model.Anomaly;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;

public interface AnomalyRepository extends JpaRepository<Anomaly, Long> {

    List<Anomaly> findByIncidentIsNullAndTimestampBetween(Instant from, Instant to);
}