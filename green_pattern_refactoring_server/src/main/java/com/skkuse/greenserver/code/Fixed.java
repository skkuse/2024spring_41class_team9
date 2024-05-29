package com.skkuse.greenserver.code;


import lombok.Getter;

import java.util.List;

@Getter
public class Fixed {

    private List<FileData> files;

    public Fixed(List<FileData> files) {
        this.files = files;
    }
}
