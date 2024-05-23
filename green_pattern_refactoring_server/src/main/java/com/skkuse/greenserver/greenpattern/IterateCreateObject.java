package com.skkuse.greenserver.greenpattern;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class IterateCreateObject implements CodeAnalyzer {
    @Override
    public String analyze(String buggyCode) {
        int objectCreationIndex = 0;
        int loopCreationIndex = 0;

        StringBuilder fixedCodeBuilder = new StringBuilder();

        try {
            // 코드 분할
            String[] codes = buggyCode.split("\n");
            ArrayList<String> lines = new ArrayList<>(Arrays.asList(codes));

            // 검출
            int lineSize = lines.size();

            // 객체 생성 확인
            for (int i = 0; i < lineSize; i++) {
                String line = codes[i];

                Pattern objectPattern = Pattern.compile("\\b[A-Z]\\w*\\s+[a-z]\\w*\\s*=\\s*new\\s+[A-Z]\\w*\\s*\\(\\s*\\)\\s*;");
                Matcher objectMatcher = objectPattern.matcher(line);
                if (objectMatcher.find()) {
                    objectCreationIndex = i;
                    break;
                }
            }

            // 반복문 확인
            for (int i = 0; i < lineSize; i++) {
                String line = codes[i];

                Pattern forPattern = Pattern.compile("\\b(?:for|while)\\s*\\(.*?\\)\\s*\\{");
                Matcher forMatcher = forPattern.matcher(line);
                if (forMatcher.find()) {
                    loopCreationIndex = i;
                    break;
                }
            }

            // 수정
            if (objectCreationIndex != 0) {
                String fixedContent = lines.get(objectCreationIndex);
                int count = countLeadingSpaces(lines.get(objectCreationIndex));
                String indent = " ".repeat(count);

                lines.set(objectCreationIndex, "##MUSTDELETE##");
                lines.add(loopCreationIndex, indent + fixedContent);

                lines.removeIf(item -> item.equals("##MUSTDELETE##"));

                // 수정된 코드를 문자열로 변환
                for (String line : lines) {
                    fixedCodeBuilder.append(line).append("\n");
                }
            } else {
                // 객체 생성이 발견되지 않은 경우 원본 코드를 그대로 반환
                fixedCodeBuilder.append(buggyCode);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return fixedCodeBuilder.toString();
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
