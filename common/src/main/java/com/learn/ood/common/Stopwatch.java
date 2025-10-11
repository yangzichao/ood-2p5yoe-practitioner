package com.learn.ood.common;

public class Stopwatch {
    private long startNanos = -1L;
    private long elapsedNanos = 0L;
    private boolean running = false;

    public void start() {
        if (!running) {
            running = true;
            startNanos = System.nanoTime();
        }
    }

    public void stop() {
        if (running) {
            long now = System.nanoTime();
            elapsedNanos += Math.max(0L, now - startNanos);
            running = false;
        }
    }

    public void reset() {
        running = false;
        startNanos = -1L;
        elapsedNanos = 0L;
    }

    public long elapsedMillis() {
        long nanos = elapsedNanos;
        if (running) {
            nanos += Math.max(0L, System.nanoTime() - startNanos);
        }
        return nanos / 1_000_000L;
    }

    public boolean isRunning() {
        return running;
    }
}

