package br.com.nathanfiorito.finances.infrastructure.card.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "invoice_predictions")
@Getter
@Setter
@NoArgsConstructor
public class InvoicePredictionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "card_id", nullable = false)
    private int cardId;

    @Column(name = "invoice_month", nullable = false)
    private LocalDate invoiceMonth;

    @Column(name = "predicted_total", nullable = false, precision = 10, scale = 2)
    private BigDecimal predictedTotal;

    @Column(name = "prediction_data", columnDefinition = "jsonb")
    private String predictionData;

    @Column(name = "generated_at", nullable = false)
    private LocalDateTime generatedAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (generatedAt == null) {
            generatedAt = LocalDateTime.now();
        }
    }
}
