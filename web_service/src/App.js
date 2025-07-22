import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeRaw from 'rehype-raw';
import LeftSidebar from './LeftSidebar';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatrooms, setChatrooms] = useState([]);
  const [currentChatroom, setCurrentChatroom] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // 채팅방 목록 불러오기
  useEffect(() => {
    fetchChatrooms();
  }, []);

  // 현재 채팅방 변경 시 메시지 불러오기
  useEffect(() => {
    if (currentChatroom) {
      fetchMessages(currentChatroom.id);
    } else {
      setMessages([]);
    }
  }, [currentChatroom]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchChatrooms = async () => {
    try {
      const response = await axios.get('/chatrooms');
      setChatrooms(response.data);
    } catch (err) {
      console.error('채팅방 목록 불러오기 실패:', err);
    }
  };

  const fetchMessages = async (chatroomId) => {
    try {
      const response = await axios.get(`/chatrooms/${chatroomId}/messages`);
      const formattedMessages = response.data.map(msg => ({
        type: msg.role,
        content: msg.content,
        sources: msg.sources
      }));
      setMessages(formattedMessages);
    } catch (err) {
      console.error('메시지 불러오기 실패:', err);
    }
  };

  const createNewChatroom = async () => {
    try {
      const response = await axios.post('/chatrooms');
      const newChatroom = response.data;
      setChatrooms([newChatroom, ...chatrooms]);
      setCurrentChatroom(newChatroom);
      setMessages([]);
      setIsSidebarOpen(false);
    } catch (err) {
      console.error('채팅방 생성 실패:', err);
    }
  };

  const deleteChatroom = async (chatroomId) => {
    if (!window.confirm('이 채팅방을 삭제하시겠습니까?')) return;
    
    try {
      await axios.delete(`/chatrooms/${chatroomId}`);
      setChatrooms(chatrooms.filter(room => room.id !== chatroomId));
      if (currentChatroom?.id === chatroomId) {
        setCurrentChatroom(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('채팅방 삭제 실패:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || loading) return;

    // 현재 채팅방이 없으면 새로 생성
    let chatroomId = currentChatroom?.id;
    if (!chatroomId) {
      const response = await axios.post('/chatrooms', null, {
        params: { title: inputMessage.substring(0, 30) + '...' }
      });
      const newChatroom = response.data;
      setChatrooms([newChatroom, ...chatrooms]);
      setCurrentChatroom(newChatroom);
      chatroomId = newChatroom.id;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    
    // 사용자 메시지 추가
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post('/search', {
        query: userMessage,
        top_k: 10,
        chatroom_id: chatroomId
      });
      
      // AI 응답 추가
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: response.data.llm_response,
        sources: response.data.results
      }]);
      
      // 첫 번째 메시지인 경우 채팅방 제목 업데이트
      if (messages.length === 0) {
        const newTitle = userMessage.length > 30 ? userMessage.substring(0, 30) + '...' : userMessage;
        await axios.put(`/chatrooms/${chatroomId}/title?title=${encodeURIComponent(newTitle)}`);
        
        // 채팅방 제목 업데이트 후 애니메이션 효과를 위해 채팅방 목록 갱신
        setChatrooms(prev => prev.map(room => 
          room.id === chatroomId 
            ? { ...room, title: newTitle, isUpdating: true }
            : room
        ));
        
        // 애니메이션 완료 후 isUpdating 플래그 제거
        setTimeout(() => {
          setChatrooms(prev => prev.map(room => 
            room.id === chatroomId 
              ? { ...room, isUpdating: false }
              : room
          ));
        }, 1500);
      }
      
      // 채팅방 목록 갱신 (업데이트 시간 반영)
      fetchChatrooms();
    } catch (err) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e) => {
    setInputMessage(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  return (
    <div className="app-container">
      <LeftSidebar
        chatrooms={chatrooms}
        currentChatroom={currentChatroom}
        onSelectChatroom={setCurrentChatroom}
        onNewChat={createNewChatroom}
        onDeleteChat={deleteChatroom}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
      
      <div className="chat-container">
        <div className="chat-header">
          <button className="menu-button" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            ☰
          </button>
          <h1>창원대학교 공지사항 AI 어시스턴트</h1>
          <p>컴퓨터공학과 공지사항에 대해 무엇이든 물어보세요</p>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>안녕하세요! 👋</h2>
              <p>창원대학교 컴퓨터공학과 공지사항에 대해 궁금한 것을 물어보세요.</p>
              <div className="example-questions">
                <p>예시 질문:</p>
                <button onClick={() => setInputMessage('2025년 1학기 수강신청 일정이 어떻게 되나요?')}>
                  2025년 1학기 수강신청 일정이 어떻게 되나요?
                </button>
                <button onClick={() => setInputMessage('졸업요건에 대해 알려주세요')}>
                  졸업요건에 대해 알려주세요
                </button>
                <button onClick={() => setInputMessage('장학금 신청 방법을 알려주세요')}>
                  장학금 신청 방법을 알려주세요
                </button>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <React.Fragment key={index}>
              <div className={`message-wrapper ${message.type}`}>
                <div className={`message ${message.type}`}>
                  {message.type === 'assistant' && (
                    <div className="message-avatar">
                      <span>AI</span>
                    </div>
                  )}
                  
                  <div className="message-content">
                    {message.type === 'assistant' ? (
                      <>
                        <div className="markdown-content">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkBreaks]}
                            rehypePlugins={[rehypeRaw]}
                            components={{
                              a: ({node, ...props}) => <a target="_blank" rel="noopener noreferrer" {...props} />
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        {message.sources && message.sources.length > 0 && (
                          <div className="sources">
                            <hr className="sources-divider" />
                            <details>
                              <summary>📚 관련 문서 ({message.sources.length}개) → 클릭하여 자세히 보기</summary>
                              <div className="sources-list">
                                {message.sources.map((source, idx) => (
                                  <div key={idx} className={`source-card ${source.score >= 0.8 ? 'high-relevance' : ''}`}>
                                    <div className="source-header">
                                      <span className="source-rank">[{idx + 1}]</span>
                                      <span className="source-score">관련도: {source.score.toFixed(3)}</span>
                                    </div>
                                    <div className="source-title">
                                      <a 
                                        href={source.metadata.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                      >
                                        {source.metadata.number} - {source.metadata.author}
                                      </a>
                                    </div>
                                    <div className="source-meta">
                                      <span className="source-date">📅 {source.metadata.date}</span>
                                      <span className="source-views">👁 조회수: {source.metadata.views || '0'}</span>
                                    </div>
                                    <div className="source-preview">
                                      {source.content.substring(0, 200)}...
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </details>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="message-text">{message.content}</div>
                    )}
                  </div>

                  {message.type === 'user' && (
                    <div className="message-avatar">
                      <span>U</span>
                    </div>
                  )}
                </div>
              </div>
              {index < messages.length - 1 && <div className="message-divider" />}
            </React.Fragment>
          ))}

          {loading && (
            <div className="message-wrapper assistant">
              <div className="message assistant loading">
                <div className="message-avatar">
                  <span>AI</span>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-input-form">
          <div className="chat-input-container">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="메시지를 입력하세요..."
              className="chat-input"
              rows="1"
              disabled={loading}
            />
            <button 
              type="submit" 
              className="send-button" 
              disabled={!inputMessage.trim() || loading}
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;