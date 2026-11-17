# syntax=docker/dockerfile:1.7
FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml ./pom.xml
# Maven Central puede responder 429 (demasiadas peticiones) a los runners compartidos de CI: hasta 4 intentos.
RUN for i in 1 2 3 4; do mvn -B -ntp dependency:go-offline && exit 0; \
      echo "Maven Central no respondió (intento $i de 4); reintento en $((i * 20)) s"; sleep $((i * 20)); done; exit 1
COPY src ./src
RUN mvn -B -ntp verify

FROM eclipse-temurin:21-jre-jammy AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=build --chown=10001:10001 /build/target/order-api.jar ./order-api.jar
USER 10001:10001
EXPOSE 8080 9090
ENTRYPOINT ["java", "-XX:+ExitOnOutOfMemoryError", "-jar", "/app/order-api.jar"]
