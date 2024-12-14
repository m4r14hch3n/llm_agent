import React, { useState } from 'react';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [paperAnalysis, setPaperAnalysis] = useState(null);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [error, setError] = useState(null);
  const [analysisStage, setAnalysisStage] = useState('initial'); // 'initial', 'summary', 'references'

  const analyzePaper = async () => {
    setLoading(true);
    setError(null);
    setAnalysisStage('initial');
    setPaperAnalysis(null);
    
    const BACKEND_URL = 'http://localhost:5001';

    try {
      // Initial analysis - get sections and original text
      const response = await fetch(`${BACKEND_URL}/analyze-paper`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze paper');
      }
      
      const initialData = await response.json();
      setPaperAnalysis(initialData);
      setCurrentSectionIndex(0);
      
      // Get overall summary
      setAnalysisStage('overall_summary');
      const summaryResponse = await fetch(`${BACKEND_URL}/get-overall-summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          fullText: initialData.sections.map(s => s.originalText).join('\n\n')
        }),
      });
      
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setPaperAnalysis(prev => ({
          ...prev,
          overallSummary: summaryData.overallSummary,
          mainFindings: summaryData.mainFindings
        }));
      }

      // Get section-by-section summaries
      setAnalysisStage('section_summaries');
      const sectionSummaries = [];
      for (const section of initialData.sections) {
        const sectionSummaryResponse = await fetch(`${BACKEND_URL}/analyze-section`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            sectionText: section.originalText,
            analysisType: 'summary'
          }),
        });
        
        if (sectionSummaryResponse.ok) {
          const sectionSummaryData = await sectionSummaryResponse.json();
          sectionSummaries.push(sectionSummaryData);
        }
      }
      
      setPaperAnalysis(prev => ({
        ...prev,
        sectionSummaries
      }));

      // Get section-by-section references
      setAnalysisStage('references');
      const sectionReferences = [];
      for (const section of initialData.sections) {
          const referencesResponse = await fetch(`${BACKEND_URL}/analyze-section`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            sectionText: section.originalText,
            analysisType: 'references'
          }),
        });
        
        if (referencesResponse.ok) {
          const referencesData = await referencesResponse.json();
          sectionReferences.push(referencesData);
        }
      }
      
      setPaperAnalysis(prev => ({
        ...prev,
        sectionReferences
      }));

    } catch (error) {
      console.error('Error analyzing paper:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const goToNextSection = () => {
    if (paperAnalysis?.sections && currentSectionIndex < paperAnalysis.sections.length - 1) {
      setCurrentSectionIndex(currentSectionIndex + 1);
    }
  };

  const goToPreviousSection = () => {
    if (currentSectionIndex > 0) {
      setCurrentSectionIndex(currentSectionIndex - 1);
    }
  };

  return (
    <div className="App">
      <div className="content">
        <div className="header-section">
          <h1>Research Paper Analyzer</h1>
          <p className="subtitle-text">Make research papers accessible and interactive</p>
        </div>

        {!paperAnalysis ? (
          <div className="input-section">
            <div className="url-input-container">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter PDF URL (e.g., https://example.com/paper.pdf)"
                className="url-input"
              />
              {error && <p className="error-message">{error}</p>}
            </div>
            <button 
              onClick={analyzePaper}
              disabled={loading || !url.trim()}
              className={`analyze-button ${loading ? 'loading' : ''}`}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  <span style={{ marginLeft: '12px' }}>Analyzing paper...</span>
                </>
              ) : (
                'Analyze Paper'
              )}
            </button>
          </div>
        ) : paperAnalysis.sections && paperAnalysis.sections.length > 0 ? (
          <div className="analysis-container">
            <div className="navigation-controls">
              <button 
                onClick={goToPreviousSection}
                disabled={currentSectionIndex === 0}
                className="nav-button"
              >
                ← Previous
              </button>
              <span className="section-counter">
                Section {currentSectionIndex + 1} of {paperAnalysis.sections.length}
              </span>
              <button 
                onClick={goToNextSection}
                disabled={currentSectionIndex === paperAnalysis.sections.length - 1}
                className="nav-button"
              >
                Next →
              </button>
            </div>

            <div className="section-content">
              <h2>{paperAnalysis.sections[currentSectionIndex]?.title}</h2>
              
              {/* Check if this is a References section */}
              {paperAnalysis.sections[currentSectionIndex]?.title.toLowerCase().includes('reference') ? (
                <div className="references-section">
                  {paperAnalysis.sections[currentSectionIndex]?.originalText
                    .split(/(?=\[\d+\])/) // Split on citation numbers
                    .filter(ref => ref.trim()) // Remove empty strings
                    .map((reference, idx) => {
                      // Extract citation number
                      const match = reference.match(/^\[(\d+)\]/);
                      const citation = match ? match[1] : null;
                      const text = match ? reference.substring(match[0].length).trim() : reference.trim();
                      
                      return (
                        <div key={idx} className="reference-item">
                          <span className="reference-number">[{citation}]</span>
                          <span className="reference-text">{text}</span>
                        </div>
                      );
                  })}
                </div>
              ) : (
                // Regular section display with all the additional analysis
                <>
                  <div className="section-original">
                    <h3>Original Text</h3>
                    <div className="text-content">
                      {paperAnalysis.sections[currentSectionIndex]?.originalText.split('\n\n').map((paragraph, idx) => (
                        <p key={idx} className="paragraph">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </div>

                  {analysisStage === 'initial' && (
                    <div className="analysis-progress">
                      <div className="spinner"></div>
                      <p>Analyzing content...</p>
                    </div>
                  )}

                  {analysisStage !== 'initial' && paperAnalysis.sectionSummaries && (
                    <div className="section-summary">
                      <h3>Summary</h3>
                      <div className="text-content">
                        <p>{paperAnalysis.sectionSummaries[currentSectionIndex]?.sectionSummary}</p>
                        <h4>Key Findings:</h4>
                        <ul>
                          {paperAnalysis.sectionSummaries[currentSectionIndex]?.keyFindings.map((finding, idx) => (
                            <li key={idx}>{finding}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {analysisStage === 'references' && paperAnalysis.sectionReferences && (
                    <>
                      <div className="section-related-topics">
                        <h3>Related Topics</h3>
                        <div className="text-content">
                          {paperAnalysis.sectionReferences[currentSectionIndex]?.relatedTopics?.map((topic, idx) => (
                            <div key={idx} className="related-topic">
                              <h4>{topic.title}</h4>
                              <p>{topic.description}</p>
                              {topic.url && (
                                <a href={topic.url} target="_blank" rel="noopener noreferrer">
                                  Learn more →
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="section-references">
                        <h3>References</h3>
                        <div className="text-content">
                          {paperAnalysis.sectionReferences[currentSectionIndex]?.references?.map((ref, idx) => (
                            <div key={idx} className="reference">
                              <span className="citation-number">[{ref.citation}]</span>
                              <span className="reference-title">{ref.title}</span>
                              {ref.url && (
                                <a href={ref.url} target="_blank" rel="noopener noreferrer">
                                  View reference →
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="error-message">No sections found in the paper analysis.</div>
        )}
      </div>
    </div>
  );
}

export default App;
