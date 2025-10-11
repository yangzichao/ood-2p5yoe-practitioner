package com.learn.ood.common;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class ConsoleIO {
    private final BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));

    public void println(String s) {
        System.out.println(s);
    }

    public void print(String s) {
        System.out.print(s);
    }

    public String readLine() {
        try {
            return reader.readLine();
        } catch (IOException e) {
            throw new RuntimeException("Failed to read from console", e);
        }
    }
}

