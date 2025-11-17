FROM eclipse-temurin:21-jdk-alpine

WORKDIR /app

# Copy the fat JAR built by Maven (check the name under target/)
COPY target/incident-service-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8081

# Wait for the collector to be ready on port 4318, then start the application
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
