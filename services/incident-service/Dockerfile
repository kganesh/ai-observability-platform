# Build stage
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Package stage
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=build /app/target/incident-service-0.0.1-SNAPSHOT.jar .
EXPOSE 8080
CMD ["java", "-jar", "incident-service-0.0.1-SNAPSHOT.jar"]
