# Earthsaver

# 배포는 earthsaver.deb으로 합니다.
# 리눅스환경을 가정하고 있습니다. 설치는 
#
# sudo apt-get install ./earthsaver.deb
#
# 또는
#
# sudo dpkg -i earthsaver.deb
# sudo apt-get install -f
#
# 으로 하면 됩니다.
# 실행할 때는 프로젝트 루트 디렉토리에서
#
# sudo earthsaver -r -m
# 
# 의 형태로 하면 됩니다. sudo권한 있어야 합니다. 삭제할 때에도
#
# sudo apt-get remove earthsaver
#
# 로 하면 됩니다. 
#
# 파이썬으로 직접 설치하려면 여기 Root 디렉토리에서 pip3 install . 로 설치할 수 있습니다. 
# python3 랑 pip3 있어야 합니다.
# pip3 install -e . 로 에딧모드로 설치할 수 있습니다. 에딧모드는 저장하면 바로 반영돼요. 안그러면 매번 재설치해야합니다
# 코드는 현재 디렉토리에서 sdk를 찾아서 사용하도록 되어있고, 실행파일 생성할 때 귀속되는 형태입니다
# 그래서 지금 python으로 실행은 어려워요
