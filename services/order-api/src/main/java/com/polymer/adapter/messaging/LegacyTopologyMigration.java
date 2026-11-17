package com.polymer.adapter.messaging;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.GetResponse;
import java.util.function.Function;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.AmqpAdmin;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.scheduling.annotation.Scheduled;

/**
 * Migra la mensajería de una instalación anterior (HexaOrders) a los nombres de POLYMER sin perder mensajes:
 * cada mensaje pendiente de hexaorders.notifications (y de su DLQ) se vuelve a publicar en polymer.* con
 * confirmación del broker y solo entonces se confirma (ack) en la cola vieja; si algo falla se devuelve a la
 * cola vieja y se reintenta más tarde. Cuando las colas viejas quedan vacías se eliminan, junto con sus exchanges.
 * En una instalación nueva no hay nada que migrar y termina en la primera ejecución.
 */
public class LegacyTopologyMigration {
    private static final Logger LOG = LoggerFactory.getLogger(LegacyTopologyMigration.class);

    private final AmqpAdmin admin;
    private final RabbitTemplate rabbit;
    private final long confirmTimeoutMillis;
    private volatile boolean done;
    private long lastWarning;

    public LegacyTopologyMigration(AmqpAdmin admin, RabbitTemplate rabbit, long confirmTimeoutMillis) {
        this.admin = admin;
        this.rabbit = rabbit;
        this.confirmTimeoutMillis = confirmTimeoutMillis;
    }

    @Scheduled(fixedDelayString = "${polymer.events.legacy-migration-interval-ms:30000}",
               initialDelayString = "${polymer.events.legacy-migration-initial-delay-ms:8000}")
    public void tick() {
        if (done) return;
        try {
            migrate();
        } catch (RuntimeException failure) {
            long now = System.currentTimeMillis();
            if (now - lastWarning > 300_000) {
                LOG.warn("Migración de las colas heredadas pendiente (se reintentará): {}", failure.getMessage());
                lastWarning = now;
            }
        }
    }

    public boolean isDone() { return done; }

    /** @return mensajes trasladados en esta ejecución. */
    public synchronized int migrate() {
        if (done) return 0;
        int moved = 0;
        if (exists(EventContract.LEGACY_NOTIFICATIONS_QUEUE)) {
            requireQueue(EventContract.NOTIFICATIONS_QUEUE);
            // Directo a la cola nueva (exchange por defecto): no depende de la clave de enrutamiento con la que llegó
            // el mensaje, que podría no coincidir con order.#, delivery.# ni payment.# y se descartaría en el exchange.
            moved += drain(EventContract.LEGACY_NOTIFICATIONS_QUEUE, "", got -> EventContract.NOTIFICATIONS_QUEUE);
            admin.deleteQueue(EventContract.LEGACY_NOTIFICATIONS_QUEUE, false, true);
        }
        if (exists(EventContract.LEGACY_NOTIFICATIONS_DLQ)) {
            requireQueue(EventContract.NOTIFICATIONS_DLQ);
            moved += drain(EventContract.LEGACY_NOTIFICATIONS_DLQ, "", got -> EventContract.NOTIFICATIONS_DLQ);
            admin.deleteQueue(EventContract.LEGACY_NOTIFICATIONS_DLQ, false, true);
        }
        admin.deleteExchange(EventContract.LEGACY_EXCHANGE);
        admin.deleteExchange(EventContract.LEGACY_DEAD_LETTER_EXCHANGE);
        done = true;
        if (moved > 0) LOG.info("RabbitMQ: {} mensajes trasladados de las colas hexaorders.* a polymer.*", moved);
        LOG.info("RabbitMQ: mensajería con los nombres de POLYMER (polymer.events, polymer.notifications)");
        return moved;
    }

    private boolean exists(String queue) { return admin.getQueueProperties(queue) != null; }

    private void requireQueue(String queue) {
        // Sin la cola de destino declarada, el mensaje republicado no tendría a dónde ir: se espera al siguiente intento.
        if (!exists(queue)) throw new IllegalStateException("la cola " + queue + " todavía no existe");
    }

    private int drain(String source, String exchange, Function<GetResponse, String> routingKey) {
        Integer moved = rabbit.execute((Channel channel) -> {
            channel.confirmSelect();
            int count = 0;
            GetResponse got;
            while ((got = channel.basicGet(source, false)) != null) {
                long tag = got.getEnvelope().getDeliveryTag();
                try {
                    channel.basicPublish(exchange, routingKey.apply(got), false, got.getProps(), got.getBody());
                    channel.waitForConfirmsOrDie(confirmTimeoutMillis);
                    channel.basicAck(tag, false);
                    count++;
                } catch (Exception failure) {
                    channel.basicNack(tag, false, true); // vuelve a la cola vieja: no se pierde
                    throw failure;
                }
            }
            return count;
        });
        return moved == null ? 0 : moved;
    }
}
