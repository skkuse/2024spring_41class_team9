package com.skkuse.greenserver.greenpattern;

import org.springframework.stereotype.Component;

@Component
public class IndentationFormatter {
    public static String formatCode(String code, String indentation) {
        String[] lines = code.split("\n");
        StringBuilder formattedCode = new StringBuilder();
        int indentLevel = 0;

        for (String line : lines) {
            line = line.trim();
            if (line.endsWith("}")) {
                indentLevel--;
            }

            formattedCode.append(String.valueOf(indentation).repeat(Math.max(0, indentLevel)));

            formattedCode.append(line).append("\n");

            if (line.endsWith("{")) {
                indentLevel++;
            }
        }

        return formattedCode.toString();
    }
}
