package com.framework.listeners;

import com.framework.config.ConfigManager;
import lombok.extern.log4j.Log4j2;
import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * Retries a failed test up to {@code retry.count} times (default: 2),
 * configurable via {@code -Dretry.count=}.
 */
@Log4j2
public class RetryAnalyzer implements IRetryAnalyzer {

    private final AtomicInteger attempts = new AtomicInteger(0);

    @Override
    public boolean retry(ITestResult result) {
        int maxRetries = ConfigManager.config().retryCount();
        if (attempts.getAndIncrement() < maxRetries) {
            log.warn("Retrying '{}' ({}/{})", result.getName(), attempts.get(), maxRetries);
            return true;
        }
        return false;
    }
}
