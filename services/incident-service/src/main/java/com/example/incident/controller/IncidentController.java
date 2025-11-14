package com.example.incident.controller;

import com.example.incident.model.Incident;
import com.example.incident.repository.IncidentRepository;
import io.micrometer.observation.annotation.Observed;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/incidents")
public class IncidentController {

    private final IncidentRepository incidentRepository;

    public IncidentController(IncidentRepository incidentRepository) {
        this.incidentRepository = incidentRepository;
    }

    @GetMapping
    @Observed(name = "incident.list", contextualName = "list-incidents")
    public List<Incident> getAll() {
        return incidentRepository.findAll();
    }

    @GetMapping("/{id}")
    @Observed(name = "incident.detail", contextualName = "incident-detail")
    public ResponseEntity<Incident> getOne(@PathVariable Long id) {
        return incidentRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}