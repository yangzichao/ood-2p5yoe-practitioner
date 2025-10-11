package com.learn.ood.common;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CommonSmokeTest {

    @Test
    void stopwatchStartsAndStops() throws InterruptedException {
        Stopwatch sw = new Stopwatch();
        assertFalse(sw.isRunning());
        sw.start();
        assertTrue(sw.isRunning());
        Thread.sleep(5);
        sw.stop();
        assertFalse(sw.isRunning());
        assertTrue(sw.elapsedMillis() >= 0);
    }
}

