package br.com.nathanfiorito.finances.infrastructure.card.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;

@Entity
@Table(name = "credit_cards")
@Getter
@Setter
@NoArgsConstructor
public class CardEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 100)
    private String alias;

    @Column(nullable = false, length = 100)
    private String bank;

    @Column(name = "last_four_digits", nullable = false, length = 4)
    @JdbcTypeCode(SqlTypes.CHAR)
    private String lastFourDigits;

    @Column(name = "closing_day", nullable = false)
    @JdbcTypeCode(SqlTypes.SMALLINT)
    private int closingDay;

    @Column(name = "due_day", nullable = false)
    @JdbcTypeCode(SqlTypes.SMALLINT)
    private int dueDay;

    @Column(nullable = false)
    private boolean active;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
