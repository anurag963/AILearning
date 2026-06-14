package com.framework.utils;

import lombok.extern.log4j.Log4j2;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Classpath resource helpers for loading static test fixtures (JSON bodies, schemas).
 */
@Log4j2
public final class FileUtils {

    private FileUtils() {
    }

    public static String readResourceAsString(String classpathLocation) {
        try (InputStream stream = FileUtils.class.getClassLoader().getResourceAsStream(classpathLocation)) {
            if (stream == null) {
                throw new IllegalArgumentException("Resource not found on classpath: " + classpathLocation);
            }
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            log.error("Failed to read classpath resource '{}'", classpathLocation, e);
            throw new IllegalStateException("Unable to read resource " + classpathLocation, e);
        }
    }
}
