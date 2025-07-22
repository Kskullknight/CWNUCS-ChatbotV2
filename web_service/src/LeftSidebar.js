import React from 'react';
import './LeftSidebar.css';

function LeftSidebar({ 
  chatrooms, 
  currentChatroom, 
  onSelectChatroom, 
  onNewChat, 
  onDeleteChat,
  isOpen,
  onToggle 
}) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 24 * 60 * 60 * 1000) {
      // 오늘
      return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    } else if (diff < 7 * 24 * 60 * 60 * 1000) {
      // 이번 주
      return date.toLocaleDateString('ko-KR', { weekday: 'short' });
    } else {
      // 그 외
      return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <>
      {/* 모바일 오버레이 */}
      {isOpen && <div className="sidebar-overlay" onClick={onToggle} />}
      
      {/* 사이드바 */}
      <div className={`left-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>채팅 목록</h3>
          <button className="close-button" onClick={onToggle}>
            ✕
          </button>
        </div>
        
        <button className="new-chat-button" onClick={onNewChat}>
          <span className="plus-icon">+</span>
          새 대화
        </button>
        
        <div className="chatroom-list">
          {chatrooms.length === 0 ? (
            <div className="empty-state">
              <p>채팅방이 없습니다</p>
              <p className="empty-hint">새 대화를 시작해보세요</p>
            </div>
          ) : (
            chatrooms.map(room => (
              <div
                key={room.id}
                className={`chatroom-item ${currentChatroom?.id === room.id ? 'active' : ''} ${room.isUpdating ? 'updating' : ''}`}
                onClick={() => onSelectChatroom(room)}
              >
                <div className="chatroom-info">
                  <div className="chatroom-title">
                    {room.isUpdating ? (
                      <span className="title-updating">{room.title}</span>
                    ) : (
                      room.title
                    )}
                  </div>
                  <div className="chatroom-date">{formatDate(room.updated_at)}</div>
                </div>
                <button
                  className="delete-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteChat(room.id);
                  }}
                >
                  🗑️
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}

export default LeftSidebar;