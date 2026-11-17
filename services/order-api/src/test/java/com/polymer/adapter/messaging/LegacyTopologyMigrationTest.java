package com.polymer.adapter.messaging;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Envelope;
import com.rabbitmq.client.GetResponse;
import java.io.IOException;
import java.util.Properties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.amqp.core.AmqpAdmin;
import org.springframework.amqp.rabbit.core.ChannelCallback;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

/** Migración de hexaorders.* a polymer.*: traslada con confirmación, no pierde mensajes y es idempotente. */
class LegacyTopologyMigrationTest {
    private final AmqpAdmin admin = mock(AmqpAdmin.class);
    private final RabbitTemplate rabbit = mock(RabbitTemplate.class);
    private final Channel channel = mock(Channel.class);
    private final LegacyTopologyMigration migration = new LegacyTopologyMigration(admin, rabbit, 5000);

    @BeforeEach
    @SuppressWarnings("unchecked")
    void channelCallbacksRunAgainstTheMockChannel() {
        when(rabbit.execute(any(ChannelCallback.class)))
                .thenAnswer(call -> ((ChannelCallback<Object>) call.getArgument(0)).doInRabbit(channel));
    }

    private static GetResponse message(long tag, String routingKey, String body) {
        return new GetResponse(new Envelope(tag, false, EventContract.LEGACY_EXCHANGE, routingKey),
                new AMQP.BasicProperties.Builder().messageId("evt-" + tag).build(), body.getBytes(), 0);
    }

    private void queues(String... existing) {
        for (String queue : existing) when(admin.getQueueProperties(queue)).thenReturn(new Properties());
    }

    @Test
    void freshInstallHasNothingToMigrate() {
        assertThat(migration.migrate()).isZero();
        assertThat(migration.isDone()).isTrue();
        verify(rabbit, never()).execute(any(ChannelCallback.class));
        verify(admin, never()).deleteQueue(anyString(), anyBoolean(), anyBoolean());
    }

    @Test
    void movesPendingMessagesWithConfirmsThenDeletesTheLegacyTopology() throws Exception {
        queues(EventContract.LEGACY_NOTIFICATIONS_QUEUE, EventContract.LEGACY_NOTIFICATIONS_DLQ,
               EventContract.NOTIFICATIONS_QUEUE, EventContract.NOTIFICATIONS_DLQ);
        when(channel.basicGet(EventContract.LEGACY_NOTIFICATIONS_QUEUE, false))
                .thenReturn(message(1, "order.created", "a"), message(2, "payment.confirmed", "b"), null);
        when(channel.basicGet(EventContract.LEGACY_NOTIFICATIONS_DLQ, false)).thenReturn(message(3, "notifications.dead", "c"), null);

        assertThat(migration.migrate()).isEqualTo(3);

        verify(channel).basicPublish(eq(EventContract.EXCHANGE), eq("order.created"), eq(false), any(), eq("a".getBytes()));
        verify(channel).basicPublish(eq(EventContract.EXCHANGE), eq("payment.confirmed"), eq(false), any(), eq("b".getBytes()));
        verify(channel).basicPublish(eq(""), eq(EventContract.NOTIFICATIONS_DLQ), eq(false), any(), eq("c".getBytes()));
        verify(channel).basicAck(1, false);
        verify(channel).basicAck(2, false);
        verify(channel).basicAck(3, false);
        verify(admin).deleteQueue(EventContract.LEGACY_NOTIFICATIONS_QUEUE, false, true);
        verify(admin).deleteQueue(EventContract.LEGACY_NOTIFICATIONS_DLQ, false, true);
        verify(admin).deleteExchange(EventContract.LEGACY_EXCHANGE);
        verify(admin).deleteExchange(EventContract.LEGACY_DEAD_LETTER_EXCHANGE);
        assertThat(migration.migrate()).as("idempotente: la segunda vez no hace nada").isZero();
    }

    @Test
    void aFailedPublishReturnsTheMessageToTheLegacyQueueAndKeepsIt() throws Exception {
        queues(EventContract.LEGACY_NOTIFICATIONS_QUEUE, EventContract.NOTIFICATIONS_QUEUE);
        when(channel.basicGet(EventContract.LEGACY_NOTIFICATIONS_QUEUE, false)).thenReturn(message(7, "order.created", "x"));
        doThrow(new IOException("broker caído")).when(channel).waitForConfirmsOrDie(anyLong());

        assertThatThrownBy(migration::migrate).hasMessageContaining("broker caído");

        verify(channel).basicNack(7, false, true);
        verify(channel, never()).basicAck(anyLong(), anyBoolean());
        verify(admin, never()).deleteQueue(anyString(), anyBoolean(), anyBoolean());
        assertThat(migration.isDone()).isFalse();
    }

    @Test
    void waitsUntilTheNewQueueExistsBeforeMovingAnything() {
        queues(EventContract.LEGACY_NOTIFICATIONS_QUEUE);
        assertThatThrownBy(migration::migrate).hasMessageContaining(EventContract.NOTIFICATIONS_QUEUE);
        verify(rabbit, never()).execute(any(ChannelCallback.class));
        assertThat(migration.isDone()).isFalse();
    }
}
