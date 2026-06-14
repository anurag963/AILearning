# Session Summary - API Test Automation Framework

## Task
Built an enterprise API test automation framework for the [Restful Booker](https://restful-booker.herokuapp.com/apidoc/index.html) API, based on the RICE-PT skill spec in `Task2_ApiFrameworkJavaRestAssured/apiTestFramework.md`, scaffolded inside `Task2_ApiFrameworkJavaRestAssured/ApiTestFrameworkJava/`.

## Stack
Java 21, Gradle 8.10 (wrapper), REST Assured 5.5 + JSON Schema Validator, TestNG 7.10, Allure 2.29, Log4j2 2.23, Jackson 2.17, Lombok 1.18, Owner 1.0 (config), Java Faker 1.0, AssertJ 3.26, JaCoCo + SonarQube plugins.

## What Was Built
- **Config layer**: `AppConfig` (Owner interface, `classpath:config/${env}.properties`), `ConfigManager` singleton, per-env properties (`dev/qa/staging/prod`) all pointing to the public Restful Booker host.
- **Auth layer**: `AuthStrategy` interface with `BearerTokenAuth` (Restful Booker's `POST /auth` + `Cookie: token=...`), plus extensible `OAuth2Auth` and `ApiKeyAuth` (not used by this API).
- **Client layer**: `ApiClient` (ThreadLocal-based, thread-safe for `parallel="methods"`), `RequestBuilder`, `ResponseValidator`, `RequestResponseLoggingFilter` (Log4j2 debug logging of req/res).
- **Models**: Lombok request/response POJOs for booking, auth, partial updates.
- **Utils**: `JsonUtils` (shared Jackson ObjectMapper), `FileUtils`, `TestDataManager` (Faker-based test data).
- **Tests**: 7 test classes / 8 `@Test` methods covering `GET /ping`, `POST /auth`, and full booking CRUD (`POST/GET/PUT/PATCH/DELETE /booking`), each with JSON schema validation.
- **Infra**: `testng.xml` (parallel, retry listener, Allure listener), `Jenkinsfile`, GitHub Actions workflow (matrix dev/qa/staging), `Dockerfile`, `docker-compose.yml`, `README.md`, `.gitignore`.

## Verification
- `./gradlew clean test` (with `JAVA_HOME` set to JDK 21) → **BUILD SUCCESSFUL**, all 7 test classes `failures="0" errors="0"` against the live Restful Booker API.
- `./gradlew allureReport` → Allure HTML report generated successfully.

## Bugs Found & Fixed
1. **Gradle daemon JDK mismatch** ("Unsupported class file major version 70") — default `java` was JDK 26; fixed by exporting `JAVA_HOME` to a JDK 21 install before running `./gradlew`. Documented in README Prerequisites.
2. **Owner config `baseURI cannot be null`** — `@Config.Sources({"system:properties", "classpath:config/${env}.properties"})` broke `${env}` variable substitution for `baseUrl()`. Fixed by removing `"system:properties"`, leaving only `@Config.Sources({"classpath:config/${env}.properties"})`. System property overrides still work via `ConfigFactory.create(AppConfig.class, System.getProperties())`.
3. **Log4j2/RestAssured `ClassCastException`** in `RequestResponseLoggingFilter` — parameterized `{}`-style logging broke under RestAssured's Groovy filter context. Fixed by switching to plain string concatenation in all `log.debug(...)` calls.

## How to Run
```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
./gradlew clean test -Denv=dev
./gradlew allureReport && ./gradlew allureServe
docker-compose up --build
```

## Status
Framework complete, all 18 skill-mandated files present, end-to-end verified against the live API. No outstanding tasks.
