export default `
:host {
  display: block;
  height: 100vh;
  font-family: system-ui, sans-serif;
}

.container {
  display: flex;
  width: 100%;
  height: 100%;
  min-width: 0;
  background: #f5f5f5;
}

.sidebar {
  display: flex;
  flex: 0 0 clamp(220px, 32%, 350px);
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: white;
  border-right: 1px solid #e0e0e0;
}

.sidebar-header {
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.question-select {
  width: 100%;
  margin-bottom: 12px;
  padding: 8px;
}

.evidence-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.chunks-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty {
  padding: 16px;
  color: #777;
  text-align: center;
}

.chunk-item {
  margin-bottom: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
}

.chunk-item:hover {
  border-color: #4313c8;
  box-shadow: 0 2px 4px rgba(67, 19, 200, 0.1);
}

.chunk-item.evidence {
  background: #f8f7ff;
  border-left: 4px solid #4313c8;
}

.chunk-header,
.badges,
.chunk-scores {
  display: flex;
  align-items: center;
}

.chunk-header {
  justify-content: space-between;
  margin-bottom: 8px;
}

.chunk-title {
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.badges {
  gap: 4px;
}

.badge {
  padding: 2px 8px;
  border-radius: 12px;
  background: #e0e0e0;
  color: #666;
  font-size: 11px;
  font-weight: 600;
}

.badge.evidence {
  background: #4313c8;
  color: white;
}

.chunk-text {
  display: -webkit-box;
  overflow: hidden;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.chunk-scores {
  gap: 12px;
  margin-top: 8px;
  color: #888;
  font-size: 11px;
}

.viewer {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: #525252;
}

.viewer-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.viewer-controls button {
  padding: 6px 12px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.viewer-controls button:disabled {
  cursor: default;
  opacity: 0.45;
}

.page-info {
  color: #666;
  font-size: 14px;
}

.viewer-content {
  display: flex;
  flex: 1;
  align-items: flex-start;
  justify-content: center;
  overflow: auto;
  padding: 20px;
}

.page-container {
  position: relative;
  flex: none;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.page-canvas {
  display: block;
}

.page-highlights {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.highlight {
  position: absolute;
  z-index: 1;
  background: transparent;
  border: 1px solid rgba(67, 19, 200, 0.35);
  border-radius: 2px;
  pointer-events: auto;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.highlight:hover {
  background: rgba(67, 19, 200, 0.2);
  border-color: rgba(67, 19, 200, 0.75);
}

.highlight.evidence {
  border-color: #4313c8;
}

.highlight.evidence:hover {
  background: rgba(67, 19, 200, 0.3);
}

.message {
  margin: auto;
  color: #eee;
  font-size: 14px;
}

.message.error {
  color: #fecaca;
}
`;
