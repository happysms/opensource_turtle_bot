# opensource_turtle_bot

## 설명
- 용도: 트레이딩 알고리즘 봇

- 사용된 알고리즘: "터틀트레이딩"(마이클 코벨 저)의 터틀트레이딩 전략을 알고리즘화 한 것이다. 시장 진입과 이탈을 결정하는 가격 주기를 설정하여 적절히 Long포지션 혹은 Short포지션에 진입한다.
  - ex) 진입 주기가 5일이고 이탈 주기가 3일이라면 당일 이전 5일 동안의 최고점/최저점을 돌파할 시 long/short포지션 진입, long 포지션이라면 이전 3일 동안의 최저점을 하향 돌파시 포지션 이탈, short 포지션이라면 3일 동안의 최고점을 상향 돌파시 포지션 이탈

- 거래소: binance

- 기초자산: binance 선물 거래소에 상장된 암호화폐, 적절히 백테스팅하여 시장 진입&이탈 주기를 설정하여 config.json 파일에 기재 요함

## 사용법 순서
1. 바이낸스 거래소 계좌 등록 후 바이낸스 선물 거래소로 자산(USDT)을 옮긴다.
2. config.json 파일에 거래 종목, 진입 주기, 이탈 주기, 현재 포지션 정보, 할당 usdt량을 형식에 맞추어 기입한다.(파일에 기재되어 있는 것처럼 기입)
3. price_monitoring.py 파일에 바이낸스 거래소 api key를 입력한다. (secret과 api_key로 나뉘어짐, 코드 내에 "입력!" 부분에 기입)
4. trade_util.py의 add_record_log 함수에 본인의 데이터베이스 정보를 입력한다.(코드 내에 "입력!"부분에 기입) 거래 내역을 기록하지 않는다면 뛰어넘어도 무관하지만 파일 내 함수 사용 부분을 모두 삭제해야한다.
5. 앞의 과정을 모두 마친 뒤 "python price_monitoring.py" 명령어를 입력하여 파일을 실행한다.

## 백테스트
- real_turtle_test.ipynb 파일에 구현된 함수를 사용하여 직접 테스트하고 시각화할 수 있다.

## 주의사항
- 봇 이용 전 종목 leverage 정보를 반드시 확인하기! 
