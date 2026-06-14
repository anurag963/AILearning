# API Test Automation Framework - Restful Booker

Enterprise-grade REST API automation framework built with Java 21, Gradle, REST Assured,
TestNG, Allure, Log4j2 and Lombok, targeting the
[Restful Booker](https://restful-booker.herokuapp.com/apidoc/index.html) playground API.

## Stack

| Layer             | Technology                                |
|-------------------|--------------------------------------------|
| Language          | Java 21                                     |
| Build Tool        | Gradle 8.10 (Groovy DSL, wrapper included)  |
| HTTP / Assertions | REST Assured 5.5 + JSON Schema Validator    |
| Test Runner       | TestNG 7.10                                 |
| Reporting         | Allure 2.29 (allure-testng)                 |
| Logging           | Log4j2 2.23                                 |
| Serialization     | Jackson 2.17 (+ JSR310)                     |
| Boilerplate       | Lombok 1.18                                 |
| Config            | Owner 1.0                                   |
| Test Data         | Java Faker 1.0                              |
| Soft Assertions   | AssertJ 3.26                                |

## Project Structure

```
src/main/java/com/framework/
├── auth/         AuthStrategy + BearerTokenAuth, OAuth2Auth, ApiKeyAuth
├── client/       ApiClient, RequestBuilder, ResponseValidator, RequestResponseLoggingFilter
├── config/       AppConfig (Owner), ConfigManager (singleton)
├── constants/     Endpoints
├── models/        request/ and response/ Lombok POJOs
└── utils/         JsonUtils, FileUtils, TestDataManager (Faker)

src/main/resources/
├── log4j2.xml
└── config/{dev,qa,staging,prod}.properties

src/test/java/
├── com/framework/base/BaseApiTest.java
├── com/framework/listeners/RetryAnalyzer.java, RetryListener.java
└── com/tests/{auth,booking,ping}/...CRUD test classes

src/test/resources/schemas/   JSON Schema files for response validation
testng.xml                    parallel="methods", thread-count=4
```

## Prerequisites

- JDK 21 (the project's Gradle toolchain targets 21)
- The bundled Gradle wrapper requires Gradle's own JVM to be JDK 21 or lower.
  If your default `java` is newer (e.g. JDK 26), point `JAVA_HOME` at a JDK 21
  install before running `./gradlew`:
  ```bash
  export JAVA_HOME=$(/usr/libexec/java_home -v 21)
  ```

## Run & Verify

```bash
# Run tests locally (dev environment, Restful Booker public API)
./gradlew clean test -Denv=dev

# Run with custom retry and thread count
./gradlew clean test -Denv=staging -Dretry.count=3 -Dthread.count=8

# Generate Allure report
./gradlew allureReport && ./gradlew allureServe

# Run in Docker
docker-compose up --build

# Run SonarQube analysis (requires a running SonarQube server)
./gradlew jacocoTestReport sonar -Dsonar.projectKey=api-framework
```

## Environments

`-Denv=` selects `src/main/resources/config/<env>.properties` (default: `dev`).
All four environment files point at the single public Restful Booker host
(`https://restful-booker.herokuapp.com`) since it does not expose separate
qa/staging/prod deployments; the switch is wired end-to-end for when a real
multi-environment target is configured.

## Authentication

`auth.type` in each environment properties file selects the strategy resolved by
`ConfigManager.authStrategy()`:

- `TOKEN` (default) - `BearerTokenAuth` calls `POST /auth` with `auth.username`/`auth.password`
  and supplies the resulting token as `Cookie: token=<value>` on PUT/PATCH/DELETE booking calls.
- `OAUTH2` - `OAuth2Auth` performs a generic client-credentials flow against `oauth2.token.url`
  (not used by Restful Booker; provided for extensibility to other APIs).
- `API_KEY` - `ApiKeyAuth` adds a static `apikey.header.name: apikey.value` header
  (not used by Restful Booker; provided for extensibility to other APIs).

## Test Coverage

| Class                                    | Endpoint                  |
|-------------------------------------------|---------------------------|
| `com.tests.ping.HealthCheckTest`          | `GET /ping`                |
| `com.tests.auth.CreateAuthTokenTest`      | `POST /auth`               |
| `com.tests.booking.CreateBookingTest`     | `POST /booking`            |
| `com.tests.booking.GetBookingTest`        | `GET /booking`, `GET /booking/:id` |
| `com.tests.booking.UpdateBookingTest`     | `PUT /booking/:id`         |
| `com.tests.booking.PartialUpdateBookingTest` | `PATCH /booking/:id`    |
| `com.tests.booking.DeleteBookingTest`     | `DELETE /booking/:id`      |

## Top 5 Troubleshooting

1. **Allure results not appearing** - ensure `build/allure-results` exists after `./gradlew test`;
   `allureReport` reads from this directory and fails silently if it's empty (no tests ran).
2. **Owner config not resolving environment** - `-Denv=qa` must be passed as a JVM system
   property to the *test* JVM. The `test` task in `build.gradle` forwards it via
   `systemProperty 'env', System.getProperty('env', 'dev')`; passing `-Denv=qa` only as a
   Gradle project property (without `-D`) will not reach `ConfigManager`.
3. **TestNG parallel execution thread-safety** - `ApiClient` uses `ThreadLocal<RequestSpecification>`
   so each TestNG worker thread builds its own spec; never cache a `RequestSpecification`
   in a static/shared field outside `ApiClient`.
4. **Log4j2 `StatusConsoleListener` warnings at startup** - usually indicates two `log4j2.xml`
   files on the classpath (e.g. from a transitive dependency); confirm only
   `src/main/resources/log4j2.xml` is packaged via `jar tf` on the test classpath.
5. **Docker container not finding test resources** - schemas and config properties must be
   under `src/main/resources` / `src/test/resources` so Gradle copies them to
   `build/resources/**` on the classpath; verify with `./gradlew processResources processTestResources`
   inside the container.
