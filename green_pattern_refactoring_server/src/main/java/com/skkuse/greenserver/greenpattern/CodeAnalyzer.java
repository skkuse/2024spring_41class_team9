package com.skkuse.greenserver.greenpattern;

public interface CodeAnalyzer {
    AnalyzeResult analyze(String buggyCode, String indentation);
}
