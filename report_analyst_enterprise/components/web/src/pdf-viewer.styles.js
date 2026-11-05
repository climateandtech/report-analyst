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

.annotations-section {
  max-height: 34%;
  overflow-y: auto;
  padding: 12px 8px;
  border-bottom: 1px solid #e0e0e0;
}

.annotations-section h3 {
  margin: 0 8px 8px;
  color: #333;
  font-size: 14px;
}

.annotations-list {
  display: grid;
  gap: 6px;
}

.source-annotation-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  width: 100%;
  border: 1px solid #f0b429;
  border-radius: 6px;
  background: #fffbeb;
  color: #333;
}

.source-annotation-item:hover {
  border-color: #d97706;
  background: #fef3c7;
}

.source-annotation-item.is-active {
  border-color: #b45309;
  box-shadow: inset 3px 0 0 #b45309;
}

.source-annotation-open {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 9px 10px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.source-annotation-delete {
  align-self: center;
  margin-right: 8px;
  padding: 5px 7px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #b42318;
  cursor: pointer;
}

.source-annotation-delete:hover {
  background: #fee4e2;
}

.source-annotation-title {
  font-size: 12px;
  font-weight: 700;
}

.source-annotation-text {
  display: -webkit-box;
  overflow: hidden;
  color: #666;
  font-size: 12px;
  line-height: 1.35;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
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

.source-guide {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background: #f8f7ff;
  border-bottom: 1px solid #ddd6fe;
  color: #555;
  font-size: 13px;
}

.source-guide strong {
  color: #4313c8;
  white-space: nowrap;
}

.viewer-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.selection-status {
  flex: 1;
  overflow: hidden;
  color: #666;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.viewer-controls .save-selection:not(:disabled) {
  border-color: #4313c8;
  background: #4313c8;
  color: white;
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
  --scale-round-x: 1px;
  --scale-round-y: 1px;
  position: relative;
  flex: none;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.page-canvas {
  display: block;
}

.page-highlights,
.source-annotations-layer,
.text-layer {
  position: absolute;
  inset: 0;
}

.page-highlights,
.source-annotations-layer {
  pointer-events: none;
}

.page-highlights {
  z-index: 1;
}

.source-annotations-layer {
  z-index: 2;
}

.text-layer {
  --min-font-size-inv: calc(1 / var(--min-font-size));
  --text-scale-factor: calc(var(--total-scale-factor) * var(--min-font-size));
  z-index: 3;
  overflow: clip;
  line-height: 1;
  transform-origin: 0 0;
}

.text-layer :is(span, br) {
  position: absolute;
  color: transparent;
  cursor: text;
  transform-origin: 0% 0%;
  white-space: pre;
}

.text-layer > :not(.markedContent),
.text-layer .markedContent span:not(.markedContent) {
  --rotate: 0deg;
  --scale-x: 1;
  z-index: 1;
  font-size: calc(var(--text-scale-factor) * var(--font-height));
  transform: rotate(var(--rotate)) scaleX(var(--scale-x)) scale(var(--min-font-size-inv));
}

.text-layer .markedContent {
  display: contents;
}

.text-layer[data-main-rotation="90"] {
  transform: rotate(90deg) translateY(-100%);
}

.text-layer[data-main-rotation="180"] {
  transform: rotate(180deg) translate(-100%, -100%);
}

.text-layer[data-main-rotation="270"] {
  transform: rotate(270deg) translateX(-100%);
}

.text-layer .end-of-content {
  position: absolute;
  inset: 100% 0 0;
  z-index: 0;
  cursor: default;
  user-select: none;
}

.text-layer.selecting .end-of-content {
  top: 0;
}

.text-layer ::selection {
  background: rgba(37, 99, 235, 0.35);
}

.highlight {
  position: absolute;
  z-index: 1;
  background: transparent;
  border: 1px solid rgba(67, 19, 200, 0.35);
  border-radius: 2px;
}

.highlight.evidence {
  border-color: #4313c8;
}

.highlight.is-hovered {
  background: rgba(67, 19, 200, 0.2);
  border-color: rgba(67, 19, 200, 0.75);
}

.source-highlight {
  position: absolute;
  box-sizing: border-box;
  border: 1px solid rgba(217, 119, 6, 0.9);
  border-radius: 2px;
  background: rgba(250, 204, 21, 0.28);
}

.source-highlight.is-focused {
  z-index: 1;
  scroll-margin: 20px;
  border: 2px solid #b45309;
  background: rgba(245, 158, 11, 0.5);
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
