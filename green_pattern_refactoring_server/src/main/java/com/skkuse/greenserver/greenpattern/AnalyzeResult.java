package com.skkuse.greenserver.greenpattern;

public class AnalyzeResult {
    private String fixedCode;
    private boolean isfixed;

    public AnalyzeResult(String fixedCode, boolean isfixed) {
        this.fixedCode = fixedCode;
        this.isfixed = isfixed;
    }

    public String getFixedCode() {
        return fixedCode;
    }

    public boolean getIsfixed() {
        return isfixed;
    }
}
