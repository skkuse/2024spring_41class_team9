package com.skkuse.greenserver.greenpattern;

public interface CodeAnalyzer {
    AnalyzeResult analyze(String buggyCode, String indentation);

    // valid한 코드인지 확인하는 메소드
    // prettier 구현하는 코드 (전처리 전 코드 확보)
}
