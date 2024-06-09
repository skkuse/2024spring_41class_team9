#!/usr/bin/env python3

import click
import os
import base64
import requests
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.style import Style
import time
import keyboard 
import difflib
from pynput import mouse
from typing import Literal,TypedDict
from enum import Enum
import firebase_admin
from firebase_admin import credentials, firestore
import threading
import json
console = Console()

# 로컬에서 모든 파일 불러와 list of dic 형태로 저장, 바이너리로 읽음
def readFiles():
    files_data = []
    for root, _, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                file_content = f.read()
            files_data.append({
                "fileRelativePath": file_path,
                "filememory": file_content
            })
    return files_data

# 바이너리를 b64인코딩해서 내용만 바꿈
def encodingJavaCode(files_data):
    encoded_files = []
    for file in files_data:
        encodedCode = base64.b64encode(file["filememory"]).decode('utf-8')
        encoded_files.append({
            "fileRelativePath": file["fileRelativePath"],
            "fileB64Encoded": encodedCode
        })
        
    request_body = {
        "files": encoded_files
    }
        
    return request_body

# HTTP 서버에 request를 보내는 함수. 명령어에 따라 엔드포인트와 리턴 구분
def submitCode(request_body, Carbon):
    if Carbon:
        url = 'https://http-server-dot-swe-team9.appspot.com/user/measure_carbonEmission' 
    else:
        url = 'https://http-server-dot-swe-team9.appspot.com/user/refactoring_code' 
        
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=request_body)
    response.raise_for_status()
 
    try:
        if Carbon:    
            return response.json().get('job_id')
        else:
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data to server: {e}")
        print(f"Response status code: {response.status_code if response else 'No response'}")
        print(f"Response text: {response.text if response else 'No response text'}")
        return None

# 리팩토링 관련 클래스
class Code:
    refactoredCode = [] # 받아온 그린코드
    decodedRefactoredCode = [] # 디코딩된 그린코드

    loophandler = True # 모든 파일에 대해 diff가 끝나면 False
    current_index = 0 # 파일 하나씩 넘기기
    scroll_offset = 0 # 아래는 레이아웃 밑 스크롤 
    max_scroll = 0
    layout_height = 0
    layout_width = max(console.size.width/2 -5,1)

    # 서버로부터 받아온 그린코드 중 java파일만 골라서 디코딩
    @staticmethod
    def decodingRefactorCode():
        for file in Code.refactoredCode:
            if file["fileRelativePath"].endswith("java"):
                Code.decodedRefactoredCode.append({
                        "fileRelativePath": file["fileRelativePath"], #design doc 대로면 fileGreenB64가 맞는것 같은데 그냥 둬도 될거같아요
                        "fileB64Decoded": base64.b64decode(file["fileB64Encoded"]) # base64.b64decode(file["fileGreenB64Encoded"])
                    })
        console.print("Decode success", style="bold green")

    # 리펙토링 명령어에 반응해 수행하는 중추 프로세스
    @staticmethod
    def codeRefactoring(request_body):
        response = submitCode(request_body, False)
        if response is None:
            console.print("Failed to refactor code.", style="bold red")
            return
        if isinstance(response, dict) and 'files' in response:
            Code.refactoredCode = response['files']
        else:
            console.print("Unexpected response format.", style="bold red")
            return
        Code.decodingRefactorCode()
        console.print("Refactoring Done!!", style="bold green")


    # 화면에 diff를 띄우는 함수
    @staticmethod
    def displayDiff(file_memory):
        console.print("Getting Diff", style="bold blue")
        
        # 기존파일과 디코딩된 그린코드를 불러옴
        files_data = {file['fileRelativePath']: file['filememory'] for file in file_memory}
        decoded_data = {file['fileRelativePath']: file['fileB64Decoded'] for file in Code.decodedRefactoredCode}
        
        file_paths = list(decoded_data.keys())
        Code.current_index = 0
        syntax_logs = [] # saved, not saved를 저장했다 화면 출력

        # 다음파일 넘기기, 두 파일이 동일하면 skip
        def nextfile():
            Code.current_index += 1
            Code.scroll_offset = 0
            Code.max_scroll = 0
            while Code.current_index != len(file_paths) and files_data[file_paths[Code.current_index]] == decoded_data[file_paths[Code.current_index]]:
                Code.current_index += 1
            if Code.current_index == len(file_paths):
                Code.loophandler = False
            Code.firsttime = 0

        # 아래는 280 줄까지 화면출력
        def add_real_line_number(lines):
            numbered_lines = []
            blank = 0
            for i, line in enumerate(lines):
                if line.startswith(' '):
                    numbered_lines.append(f"{i-blank:4d}: {line[2:]}")
                if line.startswith('+'):
                    numbered_lines.append(f"{i-blank:4d}+ {line[2:]}")
                if line.startswith('-'):
                    numbered_lines.append(f"{i-blank:4d}- {line[2:]}")
                if line.startswith('!'):
                    numbered_lines.append("   /: ")
                    blank += 1
            return numbered_lines         
        
        def expand_tabs(line, tab_size=4):
            return line.replace('\t', ' ' * tab_size)

        def wrap_lines_char(lines, width):
            if not isinstance(width, int):
                width = int(width)
            wrapped_lines = []
            for line in lines:
                expanded_line = expand_tabs(line)   
                if line[4]== ':':
                    for i in range(5, len(expanded_line), width-5):
                        if i == 5 :
                            wrapped_lines.append(f"{expanded_line[0:width]}")
                        else :
                            wrapped_lines.append(f"    : {expanded_line[i:i + width-5]}")
                if line[4]== '+':
                    for i in range(5, len(expanded_line), width-5):
                        if i == 5 :
                            wrapped_lines.append(f"{expanded_line[0:width]}")
                        else :
                            wrapped_lines.append(f"    + {expanded_line[i:i + width-5]}")
                if line[4]== '-':
                    for i in range(5, len(expanded_line), width-5):
                        if i == 5 :
                            wrapped_lines.append(f"{expanded_line[0:width]}")
                        else :
                            wrapped_lines.append(f"    - {expanded_line[i:i + width-5]}")
                while(len(wrapped_lines[len(wrapped_lines)-1])<width):
                    wrapped_lines[len(wrapped_lines)-1] = wrapped_lines[len(wrapped_lines)-1] + " "



            return wrapped_lines
        

        def display(file_path):
            
            layout = Layout(name="root")
            layout.split_column(
                Layout(name="main", ratio=1),
                Layout(name="footer", size=1)
            )
            layout["main"].split_row(
                Layout(name="left", ratio=1),
                Layout(name="right", ratio=1)
            )
            
            original_content = files_data[file_path].decode('utf-8')
            refactored_content = decoded_data[file_path].decode('utf-8')

            diff = list(difflib.ndiff(original_content.splitlines(), refactored_content.splitlines()))


            original_diff_lines = []
            refactored_diff_lines = []

            left_line_buffer = []
            right_line_buffer = []

            for line in diff:
                if line.startswith(' '):
                    # 같은 줄
                    original_diff_lines.extend(left_line_buffer)
                    refactored_diff_lines.extend(right_line_buffer)
                    left_line_buffer = []
                    right_line_buffer = []
                    while(len(original_diff_lines)<len(refactored_diff_lines)):
                        original_diff_lines.append('! ')
                    while(len(original_diff_lines)>len(refactored_diff_lines)):
                        refactored_diff_lines.append('! ')
                    original_diff_lines.append(line)
                    refactored_diff_lines.append(line)
                elif line.startswith('-'):
                    # 왼쪽에만 있는 줄
                    left_line_buffer.append(line)
                elif line.startswith('+'):
                    # 오른쪽에만 있는 줄
                    right_line_buffer.append(line)

            # 남아 있는 줄 추가
            original_diff_lines.extend(left_line_buffer)
            refactored_diff_lines.extend(right_line_buffer)

            numbered_origin_llines = add_real_line_number(original_diff_lines)
            numbered_refactored_llines = add_real_line_number(refactored_diff_lines)

            original_wrapped_lines = wrap_lines_char(numbered_origin_llines, Code.layout_width)
            refactored_wrapped_lines = wrap_lines_char(numbered_refactored_llines, Code.layout_width)
            
            Code.max_scroll = max(len(original_wrapped_lines), len(refactored_wrapped_lines)) - int(Code.layout_height) + 3

            while len(original_wrapped_lines) < len(refactored_wrapped_lines):
                original_wrapped_lines.append("    : ")

            while len(refactored_wrapped_lines) < len(original_wrapped_lines):
                refactored_wrapped_lines.append("     : ")

            

            originalText = Text()
            refactorText = Text()

            for line in original_wrapped_lines[Code.scroll_offset:]:
                if line[4] == ':':
                    originalText.append(line + '\n')
                elif line[4] == '-':
                    originalText.append(line + '\n', style = Style(bgcolor="#400000"))

            for line in refactored_wrapped_lines[Code.scroll_offset:]:
                if line[4] == ':':
                    refactorText.append(line + '\n')
                elif line[4] == '+':
                    refactorText.append(line + '\n', style = Style(bgcolor="#003200"))
     
            panel1 = Panel(originalText, title="Original Code", expand=True)
            panel2 = Panel(refactorText, title="Refactored Code", expand=True)
            
            layout["left"].update(panel1)
            layout["right"].update(panel2)
            footer_text = Text("Do you want to Accept change and Save? (y/n) ", style = "bold red")
            layout["footer"].update(footer_text)

            return layout

        # 키보드, 마우스를 통해 파일 넘기기 또는 스크롤 기능
        def on_key_event(event):

            if event.name == 'y':
                with open(file_paths[Code.current_index], 'wb') as f:
                    f.write(decoded_data[file_paths[Code.current_index]])
                syntax_logs.append(Text(f"File Saved - {file_paths[Code.current_index]}", style="bold green"))
                nextfile()
            elif event.name == 'n':
                syntax_logs.append(Text(f"Not  Saved - {file_paths[Code.current_index]}", style="bold red"))
                nextfile()
            elif event.name == 'up':
                if Code.scroll_offset > 0:
                    Code.scroll_offset -= 1
            elif event.name == 'down':
                if Code.scroll_offset < Code.max_scroll :
                    Code.scroll_offset += 1

        def on_scroll(x, y, dx, dy):
            if dy < 0:
                if Code.scroll_offset < Code.max_scroll :
                    Code.scroll_offset += 1
            if dy > 0:
                if Code.scroll_offset > 0:
                    Code.scroll_offset -= 1

        # 실제로 화면을 띄우는 곳, rich Live를 통해 임시 화면을 띄우며 Live가 종료되면 기존 화면으로 돌아감
        try:
            keyboard.on_press(on_key_event)
            listener = mouse.Listener(
                on_scroll=on_scroll)
            listener.start()
            if files_data[file_paths[Code.current_index]] == decoded_data[file_paths[Code.current_index]]:
                nextfile()
            if Code.loophandler == True:            
                with Live(display(file_paths[Code.current_index]), refresh_per_second=60, console=console, screen=True) as live:                
                    while True:
                        if Code.loophandler == False:
                            live.stop()
                            break
                        time.sleep(1/60)
                        
                        if Code.current_index < len(file_paths):
                            live.update(display(file_paths[Code.current_index]))
                        Code.layout_height = live.console.size.height
                        Code.layout_width = max(live.console.size.width/2 -5,1)

        except KeyboardInterrupt:
            pass

        for syntax in syntax_logs:
            console.print(syntax)

# 미완성
class Carbon:
    class JobStatus(Enum):
        COMPILE_ENQUEUED = "COMPILE_ENQUEUED"
        COMPILING = "COMPILING"
        MEASURE_ENQUEUED = "MEASURE_ENQUEUED"
        MEASURING = "MEASURING"
        DONE = "DONE"
        ERROR = "ERROR"
        IDLE = "IDLE"

    carbonEmission = -0.1
    job_id = ""
    job_status = JobStatus["IDLE"]
    carbonCar = -0.1
    carbonPlane = -0.1
    carbonTree = -0.1

    @staticmethod
    def setCarbonEmission(request_body):
        job_id = submitCode(request_body, True)
        if job_id:
            Carbon.job_id = job_id
            console.print(f"Start measuring with job_id: {job_id}", style="bold blue")
            Carbon.dbPolling()
        else:
            console.print("Failed to start measuring.", style="bold red")

    @staticmethod
    def dbPolling():
        def on_snapshot(doc_snapshot, changes, read_time):
            for doc in doc_snapshot:
                job_id = doc.id
                status = doc.get('status')
                Carbon.status = status
                status_code, response_text = send_request(job_id, status)
            callback_done.set()

        def send_request(job_id):
            url = 'https://swe-team9.web.app/status_request' 
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({'job_id': job_id})
            response = requests.post(url, headers=headers, data=data)
            return response.status_code, response.text

        cred = credentials.Certificate('./swe-team9-d7676333b6f8.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()



        callback_done = threading.Event()

        col_query = db.collection("jobs").where("job_id", "==", Carbon.job_id)

        query_watch = col_query.on_snapshot(on_snapshot)

        callback_done.wait()

    
        while Carbon.job_status != Carbon.JobStatus["DONE"] or Carbon.JobStatus["ERROR"] :
            time.sleep(250)
            try:
                print("...")
            except Exception as e:
               print(f"An error occurred: {e}")
        return

    @staticmethod
    def emissionConvert():
        Carbon.carbonCar = 10 * Carbon.carbonEmission / (30.1 * 19.731 / 1000)
        Carbon.carbonPlane = 0.05 * Carbon.carbonEmission / (34 * 19.956 / 1000)
        Carbon.carbonTree = 6 * Carbon.carbonEmission * 44 / (12*1000)
        console.print(f"\nYour project emits carbon {Carbon.carbonEmission:.6f} C kg, same amount as",style = "bold green")
        console.print(f"Car: {Carbon.carbonCar:.6f} km, Plane: {Carbon.carbonPlane:.6f} km, Tree: {Carbon.carbonTree:.6f} 그루", style="bold green")
        # TODO

# 명령어 생성
@click.command()
@click.option('--measure','-m', is_flag=True, help="Measure the carbon footprint using Carbon class")
@click.option('--refactor','-r', is_flag=True, help="Refactor the code using Code class")

# 중추 프로세스
def earthsaver(measure, refactor):
    if not measure and not refactor:
        console.print("Please specify an option: --measure , --refactor or both", style="bold red")
        return
    tasks = []
    
    with ThreadPoolExecutor() as executor: # 병렬처리
        file_memory = readFiles()
        request_body = encodingJavaCode(file_memory)

        if measure:
            tasks.append(executor.submit(Carbon.setCarbonEmission, request_body)) # 탄소배출량 측정
        if refactor:
            tasks.append(executor.submit(Code.codeRefactoring, request_body)) # 그린코드 생성
        
        for task in tasks: #둘 다 끝나면 for문을 탈출
            task.result()

        if refactor:
            Code.displayDiff(file_memory) # diff 출력
        if measure:
            Carbon.emissionConvert() # Emission 출력


if __name__ == "__main__":
    earthsaver()
