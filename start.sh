#!/bin/bash

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 창원대학교 공지사항 검색 서비스 시작 ===${NC}"

# 백엔드 서버 시작
echo -e "${YELLOW}[1/2] FastAPI 백엔드 서버 시작 (포트: 22222)...${NC}"
python3 search_api.py &
BACKEND_PID=$!
echo -e "${GREEN}백엔드 서버 PID: $BACKEND_PID${NC}"

# 백엔드가 완전히 시작될 때까지 대기
echo -e "${YELLOW}백엔드 서버가 준비될 때까지 기다리는 중...${NC}"
while ! curl -s http://localhost:22222/health > /dev/null; do
    echo -n "."
    sleep 2
done
echo -e "\n${GREEN}백엔드 서버가 준비되었습니다!${NC}"

# 프론트엔드 서버 시작
echo -e "${YELLOW}[2/2] React 프론트엔드 서버 시작 (포트: 11111)...${NC}"
cd web_service && npm start &
FRONTEND_PID=$!
echo -e "${GREEN}프론트엔드 서버 PID: $FRONTEND_PID${NC}"

echo -e "${GREEN}=== 서비스가 시작되었습니다! ===${NC}"
echo -e "${GREEN}프론트엔드: http://localhost:11111${NC}"
echo -e "${GREEN}백엔드 API: http://localhost:22222${NC}"
echo ""
echo -e "${YELLOW}종료하려면 Ctrl+C를 누르세요.${NC}"

# Ctrl+C 시그널 처리
trap "echo -e '\n${RED}서비스를 종료합니다...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# 프로세스가 종료될 때까지 대기
wait