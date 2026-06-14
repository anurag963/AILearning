FROM eclipse-temurin:21-jdk-alpine

WORKDIR /workspace

COPY gradlew settings.gradle build.gradle gradle.properties testng.xml sonar-project.properties ./
COPY gradle ./gradle
COPY src ./src

RUN chmod +x gradlew

ENTRYPOINT ["./gradlew"]
CMD ["clean", "test"]
