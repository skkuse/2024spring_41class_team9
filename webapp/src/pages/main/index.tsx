import { DiffEditor, Editor } from "@monaco-editor/react";
import { Box, Button, Stack, Typography } from "@mui/material";
import React, { useCallback, useRef } from "react";

const defaultCode =
  'public class Main {\n\tpublic static void main(String[] args) {\n\t\tSystem.out.println("Hello, World!");\n\t}\n}\n';

type State = {
  currentCode: string;
  submittedOriginalCode?: string;
  greenPatternRefactoringCode?: string;
  job?: Job;
};

type Job = {
  id: string;
  status: "pending" | "running" | "done" | "error";
  error?: Error;
  carbonEmission: number;
};

function MainPage() {
  const [state, setState] = React.useState<State>({
    currentCode: defaultCode,
  });
  const handleEditorChange = useCallback((value: any) => {
    setState((state) => ({ ...state, currentCode: value }));
  }, []);

  return (
    <Box>
      <Box
        // transparant app bar with title Earth Saver on the top left
        sx={{
          width: "100%",
          height: "64px",
          marginBottom: "16px",
          display: "flex",
          justifyContent: "start",
        }}
      >
        <Stack direction="row" spacing={2} alignItems="flex-end">
          <Typography variant="h3">Earth Saver</Typography>
          <Typography variant="h6">SWE Team9</Typography>
          {/* public/github-mark.svg button */}
          <img
            style={{
              cursor: "pointer",
            }}
            onClick={() => {
              window.open(
                "https://github.com/skkuse/2024spring_41class_team9",
                "_blank"
              );
            }}
            src="github-mark.svg"
            alt="github-mark"
            width="32"
            height="32"
          />
        </Stack>
      </Box>

      <Box
        sx={{
          margin: "0 24px",
        }}
      >
        <Box
          sx={{
            width: "100%",
            height: "360px",
            margin: "24px 0",
            textAlign: "center",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontSize: "36px",
          }}
        >
          Image로 서비스 소개하기.
          <br />
          JAVA CODE -- Measure / Green Pattern Refactoring
        </Box>
        <Box sx={{ width: "768px" }}>
          <Stack
            direction="row"
            spacing={2}
            alignItems="center"
            justifyContent="space-between"
          >
            <Box>
              <Typography variant="h4" fontWeight="bold">
                사용해 보기
              </Typography>
              <Typography variant="h6">
                JAVA 코드를 입력하고 Submit 버튼을 누르면 코드의 탄소배출량을
                측정하고 Green Pattern Refactoring 제안을 받을 수 있습니다.
              </Typography>
            </Box>
            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={() => {
                console.log("submit code: ", state.currentCode);
                // network call
                setState((state) => ({
                  ...state,
                  submittedOriginalCode: state.currentCode,
                  greenPatternRefactoringCode: state.currentCode,
                  job: {
                    id: "test",
                    status: "pending",
                    carbonEmission: 100,
                  },
                }));
              }}
            >
              Submit
            </Button>
          </Stack>
          <Box
            sx={{
              width: "768px",
              height: "512px",
            }}
          >
            <Editor
              height="100%"
              defaultValue={defaultCode}
              options={{
                fontSize: 15,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
              }}
              theme="vs-dark"
              language="java"
              onChange={handleEditorChange}
            />
          </Box>
        </Box>
        {state.greenPatternRefactoringCode && (
          <Box mt="24px">
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              justifyContent="space-between"
            >
              <Box>
                <Typography variant="h4" fontWeight="bold">
                  Green Pattern Refactoring 결과
                </Typography>
                <Typography variant="h6">
                  탄소배출량을 줄이기 위한 코드 리팩토링 결과를 확인할 수
                  있습니다.
                </Typography>
              </Box>
            </Stack>
            <Box
              sx={{
                width: "1536px",
                height: "512px",
              }}
            >
              <DiffEditor
                height="100%"
                options={{
                  fontSize: 15,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  originalEditable: false,
                  readOnly: true,
                }}
                theme="vs-dark"
                language="java"
                original={state.submittedOriginalCode}
                modified={state.greenPatternRefactoringCode}
              />
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}

export default MainPage;
