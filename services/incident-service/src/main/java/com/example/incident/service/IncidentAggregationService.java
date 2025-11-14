package com.example.incident.service;

import com.example.incident.model.Anomaly;
import com.example.incident.model.Incident;
import com.example.incident.repository.AnomalyRepository;
import com.example.incident.repository.IncidentRepository;
import io.micrometer.observation.annotation.Observed;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.Duration;
import java.util.List;

@Service
public class IncidentAggregationService {

    private final IncidentRepository incidentRepository;
    private final AnomalyRepository anomalyRepository;

    public IncidentAggregationService(IncidentRepository incidentRepository,
                                      AnomalyRepository anomalyRepository) {
        this.incidentRepository = incidentRepository;
        this.anomalyRepository = anomalyRepository;
    }

    /**
     * Periodically groups recent anomalies into incidents.
     */
    @Observed(name = "incident.aggregation", contextualName = "incident-aggregation-job")
    @Scheduled(fixedDelayString = "15000")  // every 15 seconds
    public void aggregateIncidents() {
        Instant now = Instant.now();
        Instant windowStart = now.minus(Duration.ofMinutes(5));

        List<Anomaly> recent = anomalyRepository.findByIncidentIsNullAndTimestampBetween(
                windowStart, now
        );

        if (recent.isEmpty()) {
            return;
        }

        // For MVP, just create one incident per batch.
        Incident incident = new Incident();
        incident.setTitle("Auto-detected incident (" + recent.size() + " anomalies)");
        incident.setServiceName(recent.get(0).getServiceName());
        incident.setStatus("open");
        incident.setFirstSeen(recent.stream()
                .map(Anomaly::getTimestamp)
                .min(Instant::compareTo)
                .orElse(now));
        incident.setLastSeen(now);

        incident = incidentRepository.save(incident);

        for (Anomaly anomaly : recent) {
            anomaly.setIncident(incident);
        }
        anomalyRepository.saveAll(recent);
    }
}