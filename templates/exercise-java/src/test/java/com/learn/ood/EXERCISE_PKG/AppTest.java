package com.learn.ood.EXERCISE_PKG;

import com.learn.ood.common.Stopwatch;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AppTest {
    @Test
    void appClassInstantiates() {
        App app = new App();
        assertEquals("app", app.id());
    }

    @Test
    void canUseCommonModule() {
        Stopwatch sw = new Stopwatch();
        sw.start();
        sw.stop();
        assertTrue(sw.elapsedMillis() >= 0);
    }
}

