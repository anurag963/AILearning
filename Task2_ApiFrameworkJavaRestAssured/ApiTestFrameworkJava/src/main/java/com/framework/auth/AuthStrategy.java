package com.framework.auth;

import java.util.Map;

/**
 * Contract for resolving the HTTP headers required to authenticate a request.
 * Implementations resolve credentials lazily and cache them for the lifetime
 * of the JVM/suite where applicable.
 */
public interface AuthStrategy {

    /**
     * @return headers to be merged into the shared {@code RequestSpecification}.
     */
    Map<String, String> getHeaders();
}
