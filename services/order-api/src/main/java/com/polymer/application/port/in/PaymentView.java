package com.polymer.application.port.in;

import com.polymer.domain.payment.PaymentStatus;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * Estado de pago de un pedido para la interfaz. status null = aún sin intentos. Para Yape/Plin pendiente:
 * qrPayload, expiresAt y remainingSeconds (TTL). Nunca incluye datos completos de tarjeta.
 * ttlSeconds: vigencia total de una solicitud Yape/Plin (PaymentPolicy.WALLET_TTL), para que la interfaz no la repita.
 */
public record PaymentView(UUID orderId, String paymentMethod, boolean online, BigDecimal amount, String currency, UUID paymentId,
                          PaymentStatus status, String method, Instant expiresAt, long remainingSeconds, String qrPayload,
                          String reference, String cardBrand, String cardLast4, String failureCode, Instant paidAt, String receipt,
                          int declinedAttempts, boolean sandbox, long ttlSeconds) {}
