package com.skkuse.greenserver.greenpattern;

import com.skkuse.greenserver.code.Buggy;
import com.skkuse.greenserver.code.FileData;
import com.skkuse.greenserver.code.Fixed;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
@RequiredArgsConstructor
public class GreenPatternProcessor {
    private final List<CodeAnalyzer> codeAnalyzers;
    private final IndentationFormatter indentationFormatter;

    public Fixed getGreenPattern(Buggy buggy) {
        List<FileData> files = buggy.getFiles();
        List<FileData> fixedFiles = new ArrayList<>();
        for (FileData file : files) {
            String buggyCode = file.base64ToJavaCode();
            String indentation = detectIndentationStyle(buggyCode);
            for (CodeAnalyzer codeAnalyzer : codeAnalyzers) {
                AnalyzeResult analyzeResult = codeAnalyzer.analyze(buggyCode, indentation);
                if (analyzeResult.getIsFixed()) {
                    buggyCode = analyzeResult.getFixedCode();
                    buggyCode = indentationFormatter.formatCode(buggyCode, indentation);
                    buggyCode = removeTrailingNewline(buggyCode);
                }
                //buggyCode = analyzeResult.getFixedCode();
            }
            FileData fixedFile = new FileData(file.getFileRelativePath(), javaCodeToBase64(buggyCode));
            fixedFiles.add(fixedFile);
        }
        return new Fixed(fixedFiles);
    }

    private String javaCodeToBase64(String javaCode) {

        return Base64.getEncoder().encodeToString(javaCode.getBytes());
        // return Base64.getEncoder().encodeToString(javaCode.getBytes(StandardCharsets.UTF_8)); <- UTF8 인코딩 명시
    }

    public static String detectIndentationStyle(String code) {
        String[] lines = code.split("\n");
        String classDefinition = "\\b(public|private|protected)?\\s*class\\s+\\w+";
        Pattern classDefinitionPattern = Pattern.compile(classDefinition);

        String whiteSpace = "^([\\t\\s]*)[^\\t\\s]+.*";
        Pattern whiteSpacePattern = Pattern.compile(whiteSpace);

        String defaultIndentation = "    ";

        boolean flag = false;
        for (String line : lines) {
            if(flag) {
                Matcher whiteSpaceMatcher = whiteSpacePattern.matcher(line);
                if(whiteSpaceMatcher.find()) {
                    return whiteSpaceMatcher.group(1);
                }
            }
            else {
                Matcher classDefinitionMatcher = classDefinitionPattern.matcher(line);
                if(classDefinitionMatcher.find()) {
                    flag = true;
                }
            }
        }
        return defaultIndentation; // indentation 발견에 실패한 경우
    }

    public static String removeTrailingNewline(String code) {
        if (code != null && code.endsWith("\n")) {
            return code.substring(0, code.length() - 1);
        }
        return code;
    }
}
