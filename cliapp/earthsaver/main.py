#!/usr/bin/env python3

import click
import os
import base64
import requests
import sys
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
from typing import Literal, TypedDict
from enum import Enum
import firebase_admin
from firebase_admin import credentials, firestore
import threading

console = Console()

# 전역함수

# 로컬에서 모든 파일 불러와 list of dic 형태로 저장, 바이너리로 읽음
def readFiles():
    files_data = []
    for root, _, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                file_content = f.read()
            files_data.append({
                "fileRelativePath": file_path[2:],
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
    max_scroll = 0 # 화면이 너무 내려가지 않게 조절
    layout_height = 0
    layout_width = max(console.size.width/2 -5,1)

    # 서버로부터 받아온 그린코드 중 java파일만 골라서 디코딩
    @staticmethod
    def decodingRefactorCode():
        for file in Code.refactoredCode:
            if file["fileRelativePath"].endswith("java"):
                Code.decodedRefactoredCode.append({
                        "fileRelativePath": file["fileRelativePath"], 
                        "fileB64Decoded": base64.b64decode(file["fileB64Encoded"]) 
                    })

    # 리펙토링을 수행해 받아오는 헬퍼함수
    @staticmethod
    def codeRefactoring(request_body):
        console.print("Sending Project for Green Code...")
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


    # 화면에 diff하여 최종 화면을 출력하는 함수
    @staticmethod
    def displayDiff(file_memory):
        
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
        def add_real_line_number(lines): # 각 줄의 맨 앞에 몇번째 줄인지 번호 붙이는 함수
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
        
        def expand_tabs(line, tab_size=4): # indentation 통일시키는 함수. tab을 4개의 space로 쪼갬
            return line.replace('\t', ' ' * tab_size)

        def wrap_lines_char(lines, width): # 화면 크기에 따라 줄을 잘라서 내리는 함수, 줄번호는 바뀌지 않음
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
        

        def display(file_path): # diff를 최종 화면에 맞게 구성하는 함수
            
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

            diff = list(difflib.ndiff(original_content.splitlines(), refactored_content.splitlines())) # 양쪽 파일을 읽어서 diff시킴


            original_diff_lines = []
            refactored_diff_lines = []

            left_line_buffer = []
            right_line_buffer = []

            for line in diff: #diff 결과에서 +, -를 기준으로 왼쪽, 오른쪽, 혹은 양쪽에 줄을 추가
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

            # 줄에 번호 붙이기
            numbered_origin_llines = add_real_line_number(original_diff_lines)
            numbered_refactored_llines = add_real_line_number(refactored_diff_lines)

            # 화면 크기에 맞게 편집
            original_wrapped_lines = wrap_lines_char(numbered_origin_llines, Code.layout_width)
            refactored_wrapped_lines = wrap_lines_char(numbered_refactored_llines, Code.layout_width)
            
            Code.max_scroll = max(len(original_wrapped_lines), len(refactored_wrapped_lines)) - int(Code.layout_height) + 3

            while len(original_wrapped_lines) < len(refactored_wrapped_lines):
                original_wrapped_lines.append("    : ")

            while len(refactored_wrapped_lines) < len(original_wrapped_lines):
                refactored_wrapped_lines.append("     : ")

            

            originalText = Text()
            refactorText = Text()

            # 화면에 띄울 line들을 text에 추가
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

            # Text를 panel에 담기
            panel1 = Panel(originalText, title="Original Code", expand=True)
            panel2 = Panel(refactorText, title="Refactored Code", expand=True)
            
            # 최종 화면구성
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
            if len(file_paths) == 0:
                console.print("No java code here", style = "bold red")
                Code.loophandler = False
            elif files_data[file_paths[Code.current_index]] == decoded_data[file_paths[Code.current_index]]:
                nextfile()
            if Code.loophandler == False :
                console.print("Nothing changed")
            if Code.loophandler == True:
                console.print("Getting Diff", style ="bold blue")
                time.sleep(1)
                with Live(display(file_paths[Code.current_index]), refresh_per_second=144, console=console, screen=True) as live:
                    while True:
                        if Code.loophandler == False:
                            live.stop()
                            break
                        time.sleep(1/144)
                        
                        if Code.current_index < len(file_paths):
                            live.update(display(file_paths[Code.current_index]))
                        Code.layout_height = live.console.size.height
                        Code.layout_width = max(live.console.size.width/2 -5,1)
            listener.stop()

        except KeyboardInterrupt:
            pass

        for syntax in syntax_logs:
            console.print(syntax)

# 탄소배출량을 측정하는 Class
class Carbon:
    carbonEmission = -0.1
    job_id = "" # http 서버로부터 받은 job id로 이를 통해 db polling함
    job_status = "COMPILE_ENQUEUED" # 진행 상황에 따라 db로부터 다른 값을 받아와 갱신
    carbonCar = -0.1
    carbonPlane = -0.1
    carbonTree = -0.1
    text = "" #진행상황 출력용 text
    run_monitor = True

    # 탄소배출량 측정을 위한 헬퍼함수
    @staticmethod
    def setCarbonEmission(request_body):
        console.print("Sending Project for Measuring...")
        job_id = submitCode(request_body, True)
        if job_id:
            Carbon.job_id = job_id
            console.print(f"Wait for measuring amount of Carbon Emission!", style="bold blue")
            Carbon.dbPolling()
        else:
            console.print("Failed to start measuring.", style="bold red")

    # db로부터 값을 갱신해오는 함수
    @staticmethod
    def dbPolling():
        def on_snapshot(doc_snapshot, changes, read_time):
            try:
                for doc in doc_snapshot:
                    status = doc.get('status')
                    if status != "ERROR" and status != "COMPILE_ENQUEUED":
                        Carbon.text += " success!\n"
                    if status == "ERROR":
                        Carbon.text += "\n"
                    if status != "COMPILE_ENQUEUED" and status != "DONE":
                        Carbon.text += f"{status}"

                    time.sleep(1/36)
                    Carbon.job_status = status
                    Carbon.carbonEmission = doc.get('carbonEmission')
            except Exception as e:
                print(f"An error occurred in on_snapshot: {e}")
                
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
                
        json_key_path = os.path.join(base_path, 'swe-team9-d7676333b6f8.json')
        if not firebase_admin._apps:
            cred = credentials.Certificate(json_key_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()

        callback_done = threading.Event()

        col_query = db.collection('jobs').document(Carbon.job_id)
        query_watch = col_query.on_snapshot(on_snapshot)
        text_anime = []
        text_anime.append(".")
        text_anime.append("..")
        text_anime.append("...")
        text_anime.append("....")
        text_anime.append(".....")
        text_anime.append("......")
        
        Carbon.text += Carbon.job_status
        
        with Live(console=console, refresh_per_second=144) as live:
            count = 0
            while Carbon.job_status != "DONE" and Carbon.job_status != "ERROR":
                
                displaytext = Text(f"{Carbon.text}{text_anime[count//12]}")
                live.update(displaytext)
                count += 1
                count = count % 72
                time.sleep(1/144)
            live.stop()

        if Carbon.job_status == "ERROR":
            console.print("ERROR!!",style = "bold red")
        if Carbon.job_status == "DONE":
            console.print("Measure DONE!!",style = "bold green")



    # 측정값을 다양한 단위로 환산하여 최종 출력하는 함수
    @staticmethod
    def emissionConvert():
        Carbon.carbonCar = (Carbon.carbonEmission / 166.0)
        Carbon.carbonPlane = 0.05 * (Carbon.carbonEmission / (34 * 19.956))
        Carbon.carbonTree = 7.16 * Carbon.carbonEmission /1000000
        console.print(f"\nYour project emits carbon {Carbon.carbonEmission:.6f} C g, same amount as",style = "bold green")
        console.print(f"Car: {Carbon.carbonCar:.6f} km / Plane: {Carbon.carbonPlane:.6f} km / Tree: {Carbon.carbonTree:.6f} 그루\n", style="bold green")

# 명령어로 실행
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
        
        for task in tasks: #둘 다 끝나나서 출력단으로 진행
            task.result()

        if refactor:
            Code.displayDiff(file_memory) # diff 출력
        if measure:
            if Carbon.job_status != "ERROR":
                Carbon.emissionConvert() # Emission 출력


if __name__ == "__main__":
    earthsaver()