package com.skkuse.greenserver.controller;

import com.skkuse.greenserver.code.Fixed;
import com.skkuse.greenserver.greenpattern.GreenPatternProcessor;
import com.skkuse.greenserver.code.Buggy;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/green_pattern")
@RequiredArgsConstructor
public class GreenPatternController {
    private final GreenPatternProcessor greenPatternProcessor;

    //@ResponseBody
    @PostMapping
    public Fixed processGreenPattern(@RequestBody Buggy buggy) {
        return greenPatternProcessor.getGreenPattern(buggy);
    }
 
/*    @PostMapping
    public String processGreenPattern(HttpServletRequest request) throws IOException {
        // 요청 본문 내용을 읽어들임
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(request.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
        }
        String requestBody = sb.toString();

        // 요청 본문 내용을 콘솔에 출력
        System.out.println("Request Body: " + requestBody);

        // 요청 본문 내용을 그대로 반환
        return requestBody;
    }*/
}
