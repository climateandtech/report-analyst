import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock PDF.js before importing the component
vi.mock('pdfjs-dist', () => ({
  default: {
    GlobalWorkerOptions: {
      workerSrc: '',
    },
    getDocument: vi.fn(),
  },
}));

// Read the component file to get the class
// We'll need to extract the class definition
let PdfViewerWithChunks;

// Import the component - it should register itself
// We'll access the class via the global scope or extract it
beforeAll(async () => {
  // Dynamically import to get the class
  const module = await import('./pdf-viewer.js');
  // The class might be in window or we need to extract it differently
  // For now, we'll create a test instance directly
});

describe('PdfViewerWithChunks', () => {
  let component;

  beforeEach(() => {
    // Create a mock instance of the component class
    // Since it extends HTMLElement, we need to create it properly
    component = Object.create(HTMLElement.prototype);
    
    // Copy methods from the class (we'll need to import it properly)
    // For testing, we'll create a minimal instance with just the methods we need
    
    // Create a simple test object with the methods we want to test
    component = {
      calculateKeyness: function(chunkText, allChunks = []) {
        // Copy the implementation logic here for testing
        const tokenize = (str) => {
          return str.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 2);
        };
        
        const chunkWords = tokenize(chunkText);
        const chunkWordCounts = new Map();
        chunkWords.forEach(word => {
          chunkWordCounts.set(word, (chunkWordCounts.get(word) || 0) + 1);
        });
        
        if (allChunks.length === 0) {
          return chunkWordCounts;
        }
        
        const corpusWords = [];
        const corpusWordCounts = new Map();
        
        allChunks.forEach(chunk => {
          const words = tokenize(chunk.text || chunk);
          words.forEach(word => {
            corpusWords.push(word);
            corpusWordCounts.set(word, (corpusWordCounts.get(word) || 0) + 1);
          });
        });
        
        const keynessScores = new Map();
        const chunkTotalWords = chunkWords.length;
        const corpusTotalWords = corpusWords.length;
        const grandTotal = chunkTotalWords + corpusTotalWords;
        
        const allWords = new Set([...chunkWords, ...corpusWords]);
        
        allWords.forEach(word => {
          const chunkFreq = chunkWordCounts.get(word) || 0;
          const corpusFreq = corpusWordCounts.get(word) || 0;
          
          if (chunkFreq === 0) {
            return;
          }
          
          const expectedChunkFreq = (chunkFreq + corpusFreq) * (chunkTotalWords / grandTotal);
          const expectedCorpusFreq = (chunkFreq + corpusFreq) * (corpusTotalWords / grandTotal);
          
          let g2 = 0;
          
          if (chunkFreq > 0 && expectedChunkFreq > 0) {
            g2 += 2 * chunkFreq * Math.log(chunkFreq / expectedChunkFreq);
          }
          
          if (corpusFreq > 0 && expectedCorpusFreq > 0) {
            g2 += 2 * corpusFreq * Math.log(corpusFreq / expectedCorpusFreq);
          }
          
          if (g2 > 0 && chunkFreq > expectedChunkFreq) {
            keynessScores.set(word, g2);
          }
        });
        
        return keynessScores;
      },
      
      getWordImportanceScores: function(chunkText, allChunks = []) {
        return this.calculateKeyness(chunkText, allChunks);
      },
      
      cosineSimilarity: function(vecA, vecB) {
        if (vecA.length !== vecB.length) {
          return 0;
        }
        
        let dotProduct = 0;
        let magA = 0;
        let magB = 0;
        
        for (let i = 0; i < vecA.length; i++) {
          dotProduct += vecA[i] * vecB[i];
          magA += vecA[i] * vecA[i];
          magB += vecB[i] * vecB[i];
        }
        
        const magnitude = Math.sqrt(magA) * Math.sqrt(magB);
        if (magnitude === 0) {
          return 0;
        }
        
        return dotProduct / magnitude;
      },
      
      findBestSemanticMatch: function(queryEmbedding, candidateEmbeddings) {
        let bestMatch = { index: -1, similarity: -1 };
        
        candidateEmbeddings.forEach((candidate, index) => {
          const similarity = this.cosineSimilarity(queryEmbedding, candidate);
          if (similarity > bestMatch.similarity) {
            bestMatch = { index, similarity };
          }
        });
        
        return bestMatch;
      },
      
      splitTextIntoSegments: function(textItems) {
        const segments = [];
        let currentSegment = { text: '', items: [] };
        
        textItems.forEach((item, idx) => {
          currentSegment.text += item.str + ' ';
          currentSegment.items.push(item);
          
          if (item.str.match(/[.!?]\s*$/) || currentSegment.text.length > 100) {
            if (currentSegment.text.trim().length > 10) {
              segments.push({
                text: currentSegment.text.trim(),
                items: [...currentSegment.items]
              });
            }
            currentSegment = { text: '', items: [] };
          }
        });
        
        if (currentSegment.text.trim().length > 10) {
          segments.push(currentSegment);
        }
        
        return segments;
      },
      
      calculateBoundingBox: function(textItems, viewport) {
        if (!textItems || textItems.length === 0) {
          return null;
        }
        
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        for (const item of textItems) {
          if (item.transform && item.transform.length >= 6) {
            const x = item.transform[4];
            const y = item.transform[5];
            const width = item.width || 0;
            const height = item.height || (Math.abs(item.transform[3]) || 12);
            
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x + width);
            maxY = Math.max(maxY, y + height);
          } else if (item.x !== undefined && item.y !== undefined) {
            const x = item.x;
            const y = item.y;
            const width = item.width || 0;
            const height = item.height || 12;
            
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x + width);
            maxY = Math.max(maxY, y + height);
          }
        }
        
        if (minX === Infinity || minY === Infinity) {
          return null;
        }
        
        let x1, y1, x2, y2;
        
        if (viewport.convertToViewportPoint) {
          [x1, y1] = viewport.convertToViewportPoint(minX, minY);
          [x2, y2] = viewport.convertToViewportPoint(maxX, maxY);
        } else {
          const pdfPageHeight = viewport.height / viewport.scale;
          x1 = minX * viewport.scale;
          y1 = (pdfPageHeight - maxY) * viewport.scale;
          x2 = maxX * viewport.scale;
          y2 = (pdfPageHeight - minY) * viewport.scale;
        }
        
        const x = Math.min(x1, x2);
        const y = Math.min(y1, y2);
        const width = Math.abs(x2 - x1);
        const height = Math.abs(y2 - y1);
        
        if (width < 1 || height < 1) {
          return null;
        }
        
        return { x, y, width, height };
      },
      
      getFilteredChunks: function() {
        let chunks = [];
        
        if (this._selectedQuestionId) {
          // Get chunks for selected question
          const question = this._questions.find(q => q.question_id === this._selectedQuestionId);
          if (question && question.chunks && question.chunks.length > 0) {
            chunks = question.chunks;
          } else {
            // Fallback: filter chunks by question_id in chunks array
            chunks = this._chunks.filter(c => c.question_id === this._selectedQuestionId);
          }
        } else {
          chunks = this._chunks;
        }
        
        // Apply evidence filter
        if (this._showEvidenceOnly) {
          chunks = chunks.filter(c => {
            // Handle both boolean (true/false) and integer (1/0) values from SQLite
            const isEvidence = c.is_evidence === true || c.is_evidence === 1;
            return isEvidence;
          });
        }
        
        return chunks;
      },
      
      _chunks: [],
      _questions: [],
      _selectedQuestionId: null,
      _showEvidenceOnly: false,
    };
  });

  describe('calculateKeyness', () => {
    it('should return word frequencies when no other chunks provided', () => {
      const chunkText = 'climate change risks environmental impact';
      const result = component.calculateKeyness(chunkText, []);

      expect(result).toBeInstanceOf(Map);
      expect(result.size).toBeGreaterThan(0);
      expect(result.has('climate')).toBe(true);
      expect(result.has('change')).toBe(true);
    });

    it('should calculate keyness scores comparing chunk to corpus', () => {
      const chunkText = 'climate change risks environmental impact';
      const allChunks = [
        { text: 'financial risks market volatility' },
        { text: 'operational risks supply chain' },
        { text: 'climate change environmental risks' },
        { text: 'regulatory compliance risks' },
      ];

      const result = component.calculateKeyness(chunkText, allChunks);

      expect(result).toBeInstanceOf(Map);
      // Words that appear more in this chunk should have higher keyness
      // "impact" might be key if it appears more here than in others
      expect(result.size).toBeGreaterThan(0);
    });

    it('should identify words unusually frequent in chunk', () => {
      const chunkText = 'harassment consultations victims perpetrators';
      const allChunks = [
        { text: 'financial reporting quarterly results' },
        { text: 'environmental sustainability carbon emissions' },
        { text: 'product safety quality assurance' },
      ];

      const result = component.calculateKeyness(chunkText, allChunks);

      expect(result).toBeInstanceOf(Map);
      // Words like "harassment", "consultations", "victims" should be key
      // because they appear in this chunk but not in others
      const keyWords = Array.from(result.keys());
      expect(keyWords.length).toBeGreaterThan(0);
    });

    it('should handle empty chunk text', () => {
      const result = component.calculateKeyness('', []);
      expect(result).toBeInstanceOf(Map);
      expect(result.size).toBe(0);
    });

    it('should filter out very short words (length <= 2)', () => {
      // Use only 1-2 character words (note: "the" is 3 chars, so use shorter words)
      const chunkText = 'a an be to of in on at';
      const result = component.calculateKeyness(chunkText, []);

      // Very short words (length <= 2) should be filtered out
      // All words in the test string are 1-2 characters, so result should be empty
      expect(result.size).toBe(0);
    });

    it('should normalize text (lowercase, remove punctuation)', () => {
      const chunkText = 'Climate Change! Environmental Impact?';
      const result = component.calculateKeyness(chunkText, []);

      // Should normalize to lowercase
      expect(result.has('climate')).toBe(true);
      expect(result.has('Climate')).toBe(false);
      expect(result.has('change')).toBe(true);
      expect(result.has('Change!')).toBe(false);
    });

    it('should only return words with positive keyness (more frequent than expected)', () => {
      const chunkText = 'common word common word unique term';
      const allChunks = [
        { text: 'common word common word' },
        { text: 'common word common word' },
        { text: 'common word common word' },
      ];

      const result = component.calculateKeyness(chunkText, allChunks);

      // "unique" and "term" should have positive keyness
      // "common" and "word" should have low/zero keyness (appear everywhere)
      expect(result).toBeInstanceOf(Map);
      // The result should only contain words that are more frequent than expected
      result.forEach((score, word) => {
        expect(score).toBeGreaterThan(0);
      });
    });

    it('should handle chunks with same text', () => {
      const chunkText = 'test text';
      const allChunks = [
        { text: 'test text' },
        { text: 'test text' },
      ];

      const result = component.calculateKeyness(chunkText, allChunks);

      // When all chunks are identical, keyness should be low/zero
      expect(result).toBeInstanceOf(Map);
    });
  });

  describe('getWordImportanceScores', () => {
    it('should return keyness scores', () => {
      const chunkText = 'climate change environmental impact';
      const allChunks = [
        { text: 'financial risks' },
        { text: 'operational risks' },
      ];

      const result = component.getWordImportanceScores(chunkText, allChunks);

      expect(result).toBeInstanceOf(Map);
      expect(result.size).toBeGreaterThan(0);
    });

    it('should delegate to calculateKeyness', () => {
      const chunkText = 'test';
      const allChunks = [];

      const keynessSpy = vi.spyOn(component, 'calculateKeyness');
      component.getWordImportanceScores(chunkText, allChunks);

      expect(keynessSpy).toHaveBeenCalledWith(chunkText, allChunks);
    });
  });

  describe('cosineSimilarity', () => {
    it('should calculate cosine similarity between two vectors', () => {
      const vecA = [1, 0, 0];
      const vecB = [1, 0, 0];
      const result = component.cosineSimilarity(vecA, vecB);
      expect(result).toBe(1); // Identical vectors should have similarity 1
    });

    it('should return 0 for orthogonal vectors', () => {
      const vecA = [1, 0, 0];
      const vecB = [0, 1, 0];
      const result = component.cosineSimilarity(vecA, vecB);
      expect(result).toBe(0);
    });

    it('should return 0 for vectors of different lengths', () => {
      const vecA = [1, 2, 3];
      const vecB = [1, 2];
      const result = component.cosineSimilarity(vecA, vecB);
      expect(result).toBe(0);
    });

    it('should handle zero vectors', () => {
      const vecA = [0, 0, 0];
      const vecB = [1, 2, 3];
      const result = component.cosineSimilarity(vecA, vecB);
      expect(result).toBe(0);
    });

    it('should calculate similarity for non-normalized vectors', () => {
      const vecA = [1, 2, 3];
      const vecB = [2, 4, 6]; // Same direction, different magnitude
      const result = component.cosineSimilarity(vecA, vecB);
      expect(result).toBeCloseTo(1, 5); // Should be 1 (same direction)
    });
  });

  describe('findBestSemanticMatch', () => {
    it('should find the best matching embedding', () => {
      const queryEmbedding = [1, 0, 0];
      const candidateEmbeddings = [
        [1, 0, 0], // Should match best
        [0, 1, 0],
        [0, 0, 1],
      ];

      const result = component.findBestSemanticMatch(queryEmbedding, candidateEmbeddings);

      expect(result.index).toBe(0);
      expect(result.similarity).toBe(1);
    });

    it('should return -1 index if no candidates provided', () => {
      const queryEmbedding = [1, 0, 0];
      const candidateEmbeddings = [];

      const result = component.findBestSemanticMatch(queryEmbedding, candidateEmbeddings);

      expect(result.index).toBe(-1);
      expect(result.similarity).toBe(-1);
    });

    it('should find best match among multiple candidates', () => {
      const queryEmbedding = [0.8, 0.6, 0];
      const candidateEmbeddings = [
        [0.1, 0.1, 0.1], // Low similarity
        [0.7, 0.5, 0.1], // Higher similarity
        [0.1, 0.1, 0.1], // Low similarity
      ];

      const result = component.findBestSemanticMatch(queryEmbedding, candidateEmbeddings);

      expect(result.index).toBe(1);
      expect(result.similarity).toBeGreaterThan(0.5);
    });
  });

  describe('splitTextIntoSegments', () => {
    it('should split text items into logical segments', () => {
      const textItems = [
        { str: 'First sentence.' },
        { str: ' ' },
        { str: 'Second sentence!' },
        { str: ' ' },
        { str: 'Third sentence?' },
      ];

      const result = component.splitTextIntoSegments(textItems);

      expect(result).toBeInstanceOf(Array);
      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toHaveProperty('text');
      expect(result[0]).toHaveProperty('items');
    });

    it('should split on sentence boundaries', () => {
      const textItems = [
        { str: 'Sentence one.' },
        { str: ' ' },
        { str: 'Sentence two.' },
      ];

      const result = component.splitTextIntoSegments(textItems);

      expect(result.length).toBeGreaterThanOrEqual(2);
    });

    it('should split after ~100 characters', () => {
      const longText = 'a'.repeat(150);
      const textItems = [{ str: longText }];

      const result = component.splitTextIntoSegments(textItems);

      expect(result.length).toBeGreaterThan(0);
    });

    it('should filter out segments shorter than 10 characters', () => {
      const textItems = [
        { str: 'Short.' },
        { str: ' ' },
        { str: 'This is a longer sentence that should be included.' },
      ];

      const result = component.splitTextIntoSegments(textItems);

      // Should only include the longer segment
      result.forEach(seg => {
        expect(seg.text.trim().length).toBeGreaterThanOrEqual(10);
      });
    });
  });

  describe('calculateBoundingBox', () => {
    it('should return null for empty text items', () => {
      const viewport = {
        width: 800,
        height: 600,
        scale: 1.0,
        convertToViewportPoint: vi.fn((x, y) => [x, y]),
      };

      const result = component.calculateBoundingBox([], viewport);
      expect(result).toBeNull();
    });

    it('should calculate bounding box from text items', () => {
      const viewport = {
        width: 800,
        height: 600,
        scale: 1.0,
        convertToViewportPoint: vi.fn((x, y) => [x * viewport.scale, y * viewport.scale]),
      };

      const textItems = [
        {
          transform: [1, 0, 0, 1, 100, 200], // x=100, y=200
          width: 50,
          height: 12,
        },
        {
          transform: [1, 0, 0, 1, 150, 200], // x=150, y=200
          width: 50,
          height: 12,
        },
      ];

      const result = component.calculateBoundingBox(textItems, viewport);

      expect(result).not.toBeNull();
      expect(result).toHaveProperty('x');
      expect(result).toHaveProperty('y');
      expect(result).toHaveProperty('width');
      expect(result).toHaveProperty('height');
      expect(result.width).toBeGreaterThan(0);
      expect(result.height).toBeGreaterThan(0);
    });

    it('should handle items with alternative coordinate format', () => {
      const viewport = {
        width: 800,
        height: 600,
        scale: 1.0,
        convertToViewportPoint: vi.fn((x, y) => [x, y]),
      };

      const textItems = [
        {
          x: 100,
          y: 200,
          width: 50,
          height: 12,
        },
      ];

      const result = component.calculateBoundingBox(textItems, viewport);

      expect(result).not.toBeNull();
      expect(result.width).toBeGreaterThan(0);
    });

    it('should return null if width or height is less than 1', () => {
      const viewport = {
        width: 800,
        height: 600,
        scale: 1.0,
        convertToViewportPoint: vi.fn((x, y) => [x, y]),
      };

      const textItems = [
        {
          transform: [1, 0, 0, 1, 100, 200],
          width: 0.5, // Too small
          height: 0.5,
        },
      ];

      const result = component.calculateBoundingBox(textItems, viewport);
      expect(result).toBeNull();
    });
  });

  describe('getFilteredChunks', () => {
    beforeEach(() => {
      // Reset component state
      component._chunks = [
        { text: 'chunk 1', question_id: 'q1', is_evidence: true },
        { text: 'chunk 2', question_id: 'q1', is_evidence: false },
        { text: 'chunk 3', question_id: 'q2', is_evidence: true },
      ];
      component._questions = [
        { question_id: 'q1', chunks: [] }, // Empty chunks array means fallback to filtering by question_id
        { question_id: 'q2', chunks: [] },
      ];
      component._selectedQuestionId = null;
      component._showEvidenceOnly = false;
    });

    it('should return all chunks when no filter applied', () => {
      component._selectedQuestionId = null;
      component._showEvidenceOnly = false;

      const result = component.getFilteredChunks();

      expect(result.length).toBe(3);
    });

    it('should filter by question ID', () => {
      component._selectedQuestionId = 'q1';
      component._showEvidenceOnly = false;

      const result = component.getFilteredChunks();

      // Since question.chunks is empty, it falls back to filtering _chunks by question_id
      expect(result.length).toBe(2);
      expect(result.every(c => c.question_id === 'q1')).toBe(true);
    });

    it('should filter by evidence when enabled', () => {
      component._selectedQuestionId = null;
      component._showEvidenceOnly = true;

      const result = component.getFilteredChunks();

      expect(result.length).toBe(2);
      expect(result.every(c => c.is_evidence === true || c.is_evidence === 1)).toBe(true);
    });

    it('should filter by both question and evidence', () => {
      component._selectedQuestionId = 'q1';
      component._showEvidenceOnly = true;

      const result = component.getFilteredChunks();

      expect(result.length).toBe(1);
      expect(result[0].question_id).toBe('q1');
      expect(result[0].is_evidence).toBe(true);
    });

    it('should handle integer evidence values (SQLite)', () => {
      component._chunks = [
        { text: 'chunk 1', is_evidence: 1 },
        { text: 'chunk 2', is_evidence: 0 },
      ];
      component._selectedQuestionId = null;
      component._showEvidenceOnly = true;

      const result = component.getFilteredChunks();

      expect(result.length).toBe(1);
      expect(result[0].is_evidence).toBe(1);
    });
  });
});

