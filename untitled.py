# PyQt5 Video player
#!/usr/bin/env python

from PyQt5.QtCore              import QDir, Qt, QUrl, QSizeF, QRect
from PyQt5.QtMultimedia        import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets           import QApplication, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget
from PyQt5.QtWidgets           import QMainWindow,QWidget, QPushButton, QAction, QLineEdit, QGraphicsOpacityEffect
from PyQt5.QtGui               import QIcon, QPixmap
from parse                     import *
from bs4                       import BeautifulSoup
import sys
import pafy
import urllib.request
import urllib.parse
import random


class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.first = True
        # -추가 : 양팡관련
        self.YangPang_play = False
        self.YangPang_first = 0

        global player
        
        # 제목 표시줄
        self.setWindowTitle("PyQt Video Player Widget Example - pythonprogramminglanguage.com") 

        # 비디오 파일 재생 위젯 생성
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # 비디오 출력 프레임 부분 위젯 생성
        self.videoWidget = QVideoWidget()

        # 플레이버튼 생성
        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)
    
        # 플레이용 수평 슬라이드 바 생성
        self.positionSlider = QSlider(Qt.Horizontal)

        # 0부터 0까지 칸 수 만큼 슬라이드 할 수 있는 바 생성
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        # - 추가 : 사운드 이미지 라벨 생성
        self.soundImage = QPushButton()
        self.soundImage.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.soundImage.clicked.connect(self.sound)
        
        # - 추가 : 사운드용 수평 슬라이드 바 생성
        self.soundpositionSlider = QSlider(Qt.Horizontal)
        self.soundpositionSlider.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # - 추가 : 0부터 100까지 칸 수 만큼 슬라이드 할 수 있는 바 생성
        self.soundpositionSlider.setRange(0, 100)
        self.soundpositionSlider.setValue(100)
        self.soundpositionSlider.sliderMoved.connect(self.setsoundPosition)
        
        # - 추가 : 링크기능
        self.textLink   = QLineEdit()
        self.buttonLink = QPushButton()
        self.textLink.setObjectName("link")
        self.buttonLink.setText("연결")
        self.buttonLink.clicked.connect(self.connect_video)
        self.buttonLink.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # 에러 Label 생성
        self.errorLabel = QLabel()

        # sizepolicy 정리
        # http://mitk.org/images/5/5e/BugSquashingSeminars%2414-04-30-bugsquashing-Qt-Size-Policy.pdf
        # https://stackoverflow.com/questions/4553304/understanding-form-layout-mechanisms-in-qt
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # 메뉴의 open 생성
        openAction = QAction(QIcon('open.png'), '&Open', self)        
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        # 메뉴의 exit 생성
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        # 메뉴바 및 메뉴 생성
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')

        # 메뉴 목록 추가
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        # centralwidget 부분 추가
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # -추가 : 양팡관련
        self.YB = QPushButton()
        self.YB.setText("양팡 Start")
        self.YB.clicked.connect(self.YangPang)

        # 레이아웃을 생성하고 위에서 만들었던 Widget 수평으로 순서대로 추가
        controlLayout = QHBoxLayout()
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.soundImage)
        controlLayout.addWidget(self.soundpositionSlider)

        # 링크 부분 레이아웃 생성
        linkLayout = QHBoxLayout()
        linkLayout.addWidget(self.textLink)
        linkLayout.addWidget(self.buttonLink)

        # controlLayout 바깥으로 여백 추가 (left, right, up, down)
        controlLayout.setContentsMargins(0, 0, 0, 0)

        # 레이아웃을 생성하고 이 래이아웃들을 수직 순서대로 추가
        layout = QVBoxLayout()
        layout.addWidget(self.videoWidget)
        layout.addLayout(controlLayout)
        layout.addLayout(linkLayout)
        # -추가 : 양팡관련
        layout.addWidget(self.YB)
        layout.addWidget(self.errorLabel)

        # CentralWidget에 layout 넣기
        wid.setLayout(layout)

        # 미디어 위젯에 비디오를 출력 시킴
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        # 미디어 위젯의 플레이 상태가 바뀔 때
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)

        # 미디어 위젯의 슬라이드바의 위치가 바뀔 때
        self.mediaPlayer.positionChanged.connect(self.positionChanged)

        # 미디어 위젯의 영상이 바뀌어 슬라이드바의 총 나눔이 달라질 때
        self.mediaPlayer.durationChanged.connect(self.durationChanged)

        # 미디어 위젯에 오류가 났을 때
        self.mediaPlayer.error.connect(self.handleError)

        # - 추가 : 영상 1/3 나누어서 5초 앞 / 시작 or 정지 / 5초 뒤 투명한 버튼 생성
        hide_layout       = QHBoxLayout()
        self.before       = QPushButton()
        self.state_change = QPushButton()
        self.after        = QPushButton()
        self.before.setEnabled(False)
        self.state_change.setEnabled(False)
        self.after.setEnabled(False)
        self.before.clicked.connect(self.before_f)
        self.state_change.clicked.connect(self.play)
        self.after.clicked.connect(self.after_f)
        self.before.setShortcut('left')
        self.state_change.setShortcut('space')
        self.after.setShortcut('right')
        hide_layout.addWidget(self.before)
        hide_layout.addWidget(self.state_change)
        hide_layout.addWidget(self.after)
        self.before.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.state_change.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.after.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.videoWidget.setLayout(hide_layout)


    # 파일 불러오기
    def openFile(self):
        # QFileDialog.getOpenFileName(self, "제목 표시줄", QDir.homePath())
        # 이 함수를 통해 filename엔 파일의 전체 경로와 어떤 종류로 가져 왔는지 변수로 줌(ex. All Files (*))
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie", QDir.homePath())
        # -추가 : 양팡관련
        self.YangPang_play = False
        self.YangPang_first = 0
        # 위에서 받아온 경로의 파일을 미디어위젯에 대입
        if fileName != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)
            self.check_url = False
            self.best = None

    # 윈도우 종료 함수
    def exitCall(self):
        sys.exit(app.exec_())


    # - 추가 : 링크로 연결 (유튜브 주소만 호환)
    def connect_video(self):
        # -추가 : 양팡관련
        if not self.YangPang_play:
            self.textValue = self.textLink.text()
            self.YangPang_first = 0
        url = self.textValue
        if self.textLink.text() != "":
            self.YangPang_play = False

        play_link = pafy.new(url)
        self.best = play_link.getbest()
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.best.url)))
        self.playButton.setEnabled(True)
        self.check_url = True

    
    # 플레이 버튼 함수
    def play(self):
        # 현재 미디어 위젯의 플레이 상태가 재생중일 때이거나 다른 경우
        # PlayingState는 Q미디어플레이어.play() 인듯 = 1
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
        
        
    # - 추가 : 사운드 버튼 함수
    def sound(self):
        if self.mediaPlayer.isMuted():
            self.mediaPlayer.setMuted(False)
            self.soundImage.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        else:
            self.mediaPlayer.setMuted(True)
            self.soundImage.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))


    # 플레이 버튼 모양 변경
    def mediaStateChanged(self, state):
        # 현재 미디어 위젯의 플레이 상태가 재생중일 때이거나 다른 경우
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        if self.mediaPlayer.state() == QMediaPlayer.StoppedState:
            if self.YangPang_play:
                self.YangPang()


    # 영상의 진행 정도에 따른 슬라이드 바 위치 변경
    def positionChanged(self, position):
        self.positionSlider.setValue(position)
        self.position = position


    # 영상의 길이만큼 슬라이드 바의 최대값 설정
    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

        # - 추가 : 슬라이드 이동 간격 설정
        self.mediaPlayer.setNotifyInterval(1)

        # - 추가 : 자동으로 영상크기만큼 윈도우 크기 조절
        if self.mediaPlayer.metaData("Resolution") != None:
            if not self.check_url:
                player.resize(self.mediaPlayer.metaData("Resolution"))
        else:
            if self.best != None:
                x, y = parse("{}x{}", self.best.resolution)
                player.resize(int(x), int(y))

        # - 추가 : 영상 추가시 버튼 활성화
        self.before.setEnabled(True)
        self.state_change.setEnabled(True)
        self.after.setEnabled(True)
                
        
    # - 추가 : 5초 앞
    def before_f(self):
        self.mediaPlayer.setPosition(self.position - 5000)


    # - 추가 : 5초 뒤
    def after_f(self):
        self.mediaPlayer.setPosition(self.position + 5000)

        
    # 영상 슬라이드 바 위치에 따른 화면 변경
    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)


    # 에러 출력 함수
    def handleError(self):
        self.playButton.setEnabled(False)
        self.before.setEnabled(False)
        self.state_change.setEnabled(False)
        self.after.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


    # - 추가 : 사운드 슬라이드 바 위치에 따른 소리 크기 변경
    def setsoundPosition(self, position):
        self.mediaPlayer.setVolume(position)


    # - 추가 : 양팡 유튜브 영상 재생
    def YangPang(self):
#        if not self.YangPang_play:
        if self.YangPang_first == 1:
            web_url = self.textValue

            with urllib.request.urlopen(web_url) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')
                yp_find = soup.find_all("a")

            self.yp_find_list = list()
            for info in yp_find:
                if parse("/watch?v={}", info["href"]) != None:
                    if str(info.find("span",{"class":"stat attribution"})).count('양팡 YangPang') > 0:
                        self.yp_find_list.append(info["href"])
                        break

        if self.YangPang_first != 1:
            web_url = "https://www.youtube.com/channel/UCMVC92EOs9yDJG5JS-CMesQ/videos"
            self.YangPang_first = 1 

            with urllib.request.urlopen(web_url) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')
                yp_find = soup.find_all("a")

            self.yp_find_list = list()
            for info in yp_find:
                if parse("/watch?v={}", info["href"]) != None:
                    self.yp_find_list.append(info["href"])

        self.YangPang_play = True
        cnt = len(self.yp_find_list) - 1
        
        self.textValue = "https://www.youtube.com/" + str(self.yp_find_list[random.randint(0, cnt)])
        self.setWindowTitle("양팡플레이어") 
        self.connect_video()
        self.play()



# 메인함수
if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())