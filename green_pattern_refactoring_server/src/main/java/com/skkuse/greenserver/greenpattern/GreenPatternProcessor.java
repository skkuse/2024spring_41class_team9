package com.skkuse.greenserver.greenpattern;

import com.skkuse.greenserver.code.Buggy;
import com.skkuse.greenserver.code.FileData;
import com.skkuse.greenserver.code.Fixed;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

@Component
@RequiredArgsConstructor
public class GreenPatternProcessor {
    private final List<CodeAnalyzer> codeAnalyzers;

    public Fixed getGreenPattern(Buggy buggy) {
        List<FileData> files = buggy.getFiles();
        List<FileData> fixedFiles = new ArrayList<>();
        for (FileData file : files) {
            String buggyCode = file.base64ToJavaCode();
            for (CodeAnalyzer codeAnalyzer : codeAnalyzers) {
                AnalyzeResult analyzeResult = codeAnalyzer.analyze(buggyCode);
                buggyCode = analyzeResult.getFixedCode();
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
}
