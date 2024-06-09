import { DiffEditor, Editor } from "@monaco-editor/react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  Typography,
  AppBar,
  Toolbar,
  Backdrop,
} from "@mui/material";
import React, { useCallback, useEffect, useRef } from "react";
import { firestore } from "../../lib/firebase";
import { DocumentSnapshot, doc, onSnapshot } from "firebase/firestore";

const defaultCode = `// Write down your code here
// Your class name must be Main

public class Main {
    public static void main(String[] args) {
        boolean cond1 = checkCond1();
        boolean cond2 = checkCond2();
        boolean cond3 = checkCond3();

        if(cond1) {
            if(cond2) {
                if(cond3) {
                    System.out.println("Hello");
                }
            }
        }
    }

    public static boolean checkCond1() {
        int sum = 0;
        for(int i=0; i<10000; i++) {
            sum += i;
        }
        return sum > 50000;
    }

    public static boolean checkCond2() {
        int sum = 0;
        for(int i=0; i<10000; i++) {
            sum *= i;
        }
        return sum > 50000;
    }

    public static boolean checkCond3() {
        int sum = 0;
        for(int i=0; i<10000; i++) {
            sum *= i;
        }
        return sum > 50000;
    }
}

  `;
const POLLING_TIMEOUT_MS = 60000;

const HTTP_SERVER_MEASURE_ENDPOINT =
  "https://http-server-dot-swe-team9.du.r.appspot.com/user/measure_carbonEmission";
// "http://localhost:8080/user/measure_carbonEmission";

const HTTP_SERVER_REFACTORING_ENDPOINT =
  "https://http-server-dot-swe-team9.du.r.appspot.com/user/refactoring_code";
// "http://localhost:8080/user/refactoring_code";

const CARBON_EMISSION_BACKGROUND_COLOR = "#ffffff";

type State = {
  currentCode: string;
  submittedOriginalCode?: string;
  greenPatternRefactoringCode?: string;
  job?: Job;
  loading?: boolean;
};

type JobStatus =
  | "COMPILE_ENQUEUED"
  | "COMPILING"
  | "MEASURE_ENQUEUED"
  | "MEASURING"
  | "DONE"
  | "ERROR";

const JOB_STATUS_READABLE: Record<JobStatus, string> = {
  COMPILE_ENQUEUED: "컴파일 대기 중",
  COMPILING: "컴파일 중",
  MEASURE_ENQUEUED: "탄소배출량 측정 대기 중",
  MEASURING: "탄소배출량 측정 중",
  DONE: "완료",
  ERROR: "에러 발생",
};

type Job = {
  status: JobStatus;
  error?: Error;
  carbonEmission?: number;
};

function MainPage() {
  const [state, setState] = React.useState<State>({
    currentCode: defaultCode,
  });
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleEditorChange = useCallback((value: any) => {
    setState((state) => ({ ...state, currentCode: value }));
  }, []);

  const startJobPolling = useCallback(
    (job_id: string) => {
      const jobRef = doc(firestore, "jobs", job_id);

      // Listen to the document.
      const unsubscribe = onSnapshot(
        jobRef,
        (doc: DocumentSnapshot): void => {
          console.log("Current data: ", doc.data());
          const data = doc.data();
          if (data) {
            if (data.status === "DONE" || data.status === "ERROR") {
              // clear timeout
              if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
              }
            }
            setState((state) => ({
              ...state,
              job: {
                ...state.job!,
                status: data.status,
                carbonEmission: data.carbonEmission,
              },
            }));
          }
        },
        (error) => {
          console.error("Listen failed: ", error);
          setState((state) => ({
            ...state,
            job: {
              ...state.job!,
              status: "ERROR",
              error,
            },
          }));
        }
      );

      unsubscribeRef.current = unsubscribe;

      // Unsubscribe after N seconds
      timeoutRef.current = setTimeout(() => {
        // set error if not done or error
        if (state.job?.status !== "DONE" && state.job?.status !== "ERROR") {
          console.log("Timeout");
          setState((state) => ({
            ...state,
            job: {
              ...state.job!,
              status: "ERROR",
              error: new Error("Timeout"),
            },
          }));
        }
        unsubscribe();
      }, POLLING_TIMEOUT_MS);

      return unsubscribe;
    },
    [state.job?.status]
  );

  // Unsubscribe when component unmounts
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, []);

  return (
    <Box>
      <AppBar position="sticky">
        <Toolbar>
          <Typography variant="h5" sx={{ flexGrow: 1 }}>
            Earth Saver
          </Typography>
          <Typography variant="h6" sx={{ mr: 2 }}>
            SWE Team9
          </Typography>
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
        </Toolbar>
      </AppBar>

      {state.loading && (
        <Backdrop
          open={state.loading}
          sx={{
            zIndex: 1000,
          }}
        >
          <CircularProgress />
        </Backdrop>
      )}

      <Box sx={{ padding: "24px" }}>
        <Box
          sx={{
            width: "100%",
            height: "360px",
            marginBottom: "24px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            textAlign: "center",
            backgroundColor: "#f0f0f0",
            borderRadius: "8px",
          }}
        >
          <Typography variant="h4">
            Image로 서비스 소개하기.
            <br />
            JAVA CODE -- Measure / Green Pattern Refactoring
          </Typography>
        </Box>
        <Stack direction="row" spacing={4}>
          <Box sx={{ width: "768px" }}>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              justifyContent="space-between"
              marginBottom="16px"
            >
              <Box>
                <Typography variant="h5" fontWeight="bold">
                  사용해 보기
                </Typography>
                <Typography variant="subtitle1">
                  JAVA 코드를 입력하고 Submit 버튼을 누르면 코드의 탄소배출량을
                  측정하고 Green Pattern Refactoring 제안을 받을 수 있습니다.
                </Typography>
              </Box>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={async () => {
                  console.log("submit code: ", state.currentCode);
                  // network call
                  let codeB64Encoded = btoa(state.currentCode);
                  console.log("codeB64Encoded: ", codeB64Encoded);

                  setState((state) => ({
                    ...state,
                    loading: true,
                  }));

                  const measure_response = await fetch(
                    HTTP_SERVER_MEASURE_ENDPOINT,
                    {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                      },
                      body: JSON.stringify({
                        files: [
                          {
                            fileRelativePath: "Main.java",
                            fileB64Encoded: codeB64Encoded,
                          },
                        ],
                      }),
                    }
                  );
                  if (!measure_response.ok) {
                    console.error(measure_response.statusText);
                    setState((state) => ({
                      ...state,
                      job: {
                        status: "ERROR",
                        error: new Error("HTTP Error from measure"),
                      },
                      loading: false,
                    }));
                    return;
                  }

                  const refactoring_response = await fetch(
                    HTTP_SERVER_REFACTORING_ENDPOINT,
                    {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                      },
                      body: JSON.stringify({
                        files: [
                          {
                            fileRelativePath: "Main.java",
                            fileB64Encoded: codeB64Encoded,
                          },
                        ],
                      }),
                    }
                  );
                  if (!refactoring_response.ok) {
                    console.error(refactoring_response.statusText);
                    setState((state) => ({
                      ...state,
                      job: {
                        status: "ERROR",
                        error: new Error("HTTP Error from refactoring"),
                      },
                      loading: false,
                    }));
                    return;
                  }

                  const { job_id } = await measure_response.json();
                  console.log("response data from measure: ", job_id);

                  const data = await refactoring_response.json();
                  console.log("response data from refactoring: ", data);

                  if (data.files.length === 0) {
                    console.error("No refactoring result");
                    setState((state) => ({
                      ...state,
                      job: {
                        status: "ERROR",
                        error: new Error("No refactoring result"),
                      },
                      loading: false,
                    }));
                    return;
                  }

                  setState((state) => ({
                    ...state,
                    submittedOriginalCode: state.currentCode,
                    greenPatternRefactoringCode: atob(
                      data.files[0].fileB64Encoded
                    ),
                    loading: false,
                  }));

                  // start polling job status
                  startJobPolling(job_id);
                }}
              >
                Submit
              </Button>
            </Stack>
            <Box
              sx={{
                width: "100%",
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
          <Box sx={{ width: "600px", height: "512px" }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                width: "100%",
                height: "106px",
              }}
            >
              <Box sx={{ flexGrow: 1 }}>
                {state.job?.status === "DONE" ? (
                  <Alert sx={{ height: "fit-content" }} severity="success">
                    {JOB_STATUS_READABLE[state.job.status]}
                  </Alert>
                ) : state.job?.status === "ERROR" ? (
                  <Alert sx={{ height: "fit-content" }} severity="error">
                    {`에러 발생: ${state.job.error?.message}`}
                  </Alert>
                ) : !state.job ? (
                  <Alert sx={{ height: "fit-content" }} severity="info">
                    결과를 확인하려면 Submit 버튼을 눌러주세요.
                  </Alert>
                ) : (
                  <Alert
                    sx={{ height: "fit-content" }}
                    severity="info"
                    icon={<CircularProgress size={22} />}
                  >
                    {JOB_STATUS_READABLE[state.job.status]}
                  </Alert>
                )}
              </Box>
            </Box>
            <JobResult job={state.job} />
          </Box>
        </Stack>
        <Box mt="24px">
          <Typography variant="h5" fontWeight="bold">
            Green Pattern Refactoring 결과
          </Typography>
          <Typography variant="subtitle1" marginBottom="16px">
            탄소배출량을 줄이기 위한 코드 리팩토링 결과를 확인할 수 있습니다.
          </Typography>
          <Box
            sx={{
              width: "100%",
              height: "512px",
            }}
          >
            {state.greenPatternRefactoringCode && (
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
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

type JobResultProps = {
  job?: Job;
};

function JobResult({ job }: JobResultProps) {
  return (
    <Stack direction="column" spacing={1}>
      <Box
        sx={{
          backgroundColor: CARBON_EMISSION_BACKGROUND_COLOR,
          border: "1px solid #e0e0e0",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <Stack
          sx={{
            width: "100%",
          }}
          direction="row"
          spacing={8}
          alignItems="center"
        >
          <Typography variant="h6" fontWeight="bold">
            탄소배출량 (C kg)
          </Typography>
          <Typography variant="h6">
            {job?.status === "DONE" ? job.carbonEmission : "-"}
          </Typography>
        </Stack>
      </Box>
      <Box
        sx={{
          backgroundColor: CARBON_EMISSION_BACKGROUND_COLOR,
          border: "1px solid #e0e0e0",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <Stack
          sx={{
            width: "100%",
          }}
          direction="row"
          spacing={8}
          alignItems="center"
        >
          <img
            src="car.webp"
            alt="car"
            width="100"
            height="100"
            style={{ marginRight: "8px" }}
          />
          <Typography variant="h6">
            {job?.status === "DONE"
              ? `자동차로 ${job.carbonEmission}km 이동`
              : ""}
          </Typography>
        </Stack>
      </Box>
      <Box
        sx={{
          backgroundColor: CARBON_EMISSION_BACKGROUND_COLOR,
          border: "1px solid #e0e0e0",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <Stack
          sx={{
            width: "100%",
          }}
          direction="row"
          spacing={8}
          alignItems="center"
        >
          <img
            src="airplane.webp"
            alt="airplane"
            width="100"
            height="100"
            style={{ marginRight: "8px" }}
          />
          <Typography variant="h6">
            {job?.status === "DONE"
              ? `비행기로 ${job.carbonEmission}km 이동`
              : ""}
          </Typography>
        </Stack>
      </Box>
      <Box
        sx={{
          backgroundColor: CARBON_EMISSION_BACKGROUND_COLOR,
          border: "1px solid #e0e0e0",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <Stack
          sx={{
            width: "100%",
          }}
          direction="row"
          spacing={8}
          alignItems="center"
        >
          <img
            src="tree.webp"
            alt="tree"
            width="100"
            height="100"
            style={{ marginRight: "8px" }}
          />
          <Typography variant="h6">
            {job?.status === "DONE"
              ? `나무 ${Math.round(
                  job.carbonEmission ?? 0
                )}그루가 1년 동안 흡수`
              : ""}
          </Typography>
        </Stack>
      </Box>
    </Stack>
  );
}

export default MainPage;
