package com.skkuse.greenserver.code;

import lombok.Data;
import lombok.Getter;

import java.util.Base64;

@Getter
public class FileData {
    private String fileRelativePath;
    private String fileB64Encoded;

    public FileData(String fileRelativePath, String fileB64Encoded) {
        this.fileRelativePath = fileRelativePath;
        this.fileB64Encoded = fileB64Encoded;
    }

    public String getFileRelativePath() {
        return fileRelativePath;
    }

    public String base64ToJavaCode() {
        byte[] decodedBytes = Base64.getDecoder().decode(fileB64Encoded);
        return new String(decodedBytes);
    }
}
