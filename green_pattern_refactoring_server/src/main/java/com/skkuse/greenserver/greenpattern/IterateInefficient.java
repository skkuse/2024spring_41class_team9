package com.skkuse.greenserver.greenpattern;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class IterateInefficient implements CodeAnalyzer {
    // 제공받은 코드의 로직 사용, 코드 개선과정에서 유저의 원 코드 유지하도록 약간의 코드 수정
    @Override
    public AnalyzeResult analyze(String buggyCode) {
        StringBuilder fixedCodeBuilder = new StringBuilder();
        boolean isDetected = false;

        try {
            // 코드 분할
            String[] codes = buggyCode.split("\n");
            ArrayList<String> lines = new ArrayList<>(Arrays.asList(codes));

            // 검출
            int buggyLine = -1;
            String arrayListVariableName = "";
            int lineSize = lines.size();

            for (int i = 0; i < lineSize; i++) {
                String line = codes[i];

                Pattern pattern = Pattern.compile("\\bArrayList\\s*<[^>]*>\\s+([a-zA-Z0-9_]+)\\s*=");

                Matcher matcher = pattern.matcher(line);
                if (matcher.find()) {
                    arrayListVariableName = matcher.group(1);

                    for (int j = i; j < codes.length; j++) {
                        String line2 = codes[j];
                        Pattern sizeMethodPattern = Pattern.compile("\\b" + arrayListVariableName + "\\.size\\(\\)");

                        Matcher sizeMethodMatcher = sizeMethodPattern.matcher(line2);
                        if (sizeMethodMatcher.find()) {
//                            System.out.println("ArrayList 객체 변수명: " + arrayListVariableName);
//                            System.out.println("해당 변수를 사용하여 size() 메서드를 호출함");
                            buggyLine = j;
                            isDetected = true;
                            break;
                        }
                    }
                }
            }

            // 수정
            if (isDetected) {
                int count = countLeadingSpaces(lines.get(buggyLine));
                String indent = " ".repeat(count);

                lines.set(buggyLine, lines.get(buggyLine).replace(arrayListVariableName + ".size()", arrayListVariableName + "Size"));

                StringBuilder builder = new StringBuilder();
                builder.append(indent).append("int ").append(arrayListVariableName).append("Size = ").append(arrayListVariableName).append(".size();\n");
                lines.add(buggyLine, builder.toString());
            }

            // 수정된 코드를 문자열로 변환
            for (String line : lines) {
                fixedCodeBuilder.append(line).append("\n");
            }
        } catch (Exception e) {
            System.out.println(e);
        }
        String fixedCode = fixedCodeBuilder.toString();
        return new AnalyzeResult(fixedCode, isDetected);
    }

    private static int countLeadingSpaces(String text) {
        int count = 0;
        for (int i = 0; i < text.length(); i++) {
            if (text.charAt(i) == ' ') {
                count++;
            } else {
                break;
            }
        }
        return count;
    }
}
