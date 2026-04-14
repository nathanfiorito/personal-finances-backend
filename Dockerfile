# ---- Build stage ----
FROM maven:3.9-eclipse-temurin-25 AS build
WORKDIR /build

# Cache dependencies before copying source
COPY app/pom.xml .
RUN mvn -B dependency:go-offline --no-transfer-progress

COPY app/src ./src
RUN mvn -B package -DskipTests --no-transfer-progress

# ---- Runtime stage ----
FROM eclipse-temurin:25-jre-noble
WORKDIR /app

RUN groupadd --system finbot && useradd --system --gid finbot finbot

COPY --from=build /build/target/finances-*.jar app.jar

USER finbot
EXPOSE 8080

ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-jar", "app.jar"]
