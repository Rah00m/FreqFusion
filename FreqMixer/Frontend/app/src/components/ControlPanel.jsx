import React from 'react'
import './ControlPanel.css'

const ControlPanel = ({
  loadedCount,
  commonSize,
  activeOutput,
  onLoadSamples,
  onClearAll
}) => {
  return (
    <div className="control-panel">
      {/* Status Info */}
      <div className="status-info">
        <div className="status-item">
          <i className="fas fa-images"></i>
          <div>
            <div className="status-label">Images Loaded</div>
            <div className="status-value">{loadedCount}/4</div>
          </div>
        </div>

        <div className="status-item">
          <i className="fas fa-expand-alt"></i>
          <div>
            <div className="status-label">Common Size</div>
            <div className="status-value">
              {commonSize 
                ? `${commonSize.width}×${commonSize.height}`
                : 'Not set'
              }
            </div>
          </div>
        </div>

        <div className="status-item">
          <i className="fas fa-desktop"></i>
          <div>
            <div className="status-label">Active Output</div>
            <div className="status-value">Output {activeOutput + 1}</div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button 
          className="btn btn-sample"
          onClick={onLoadSamples}
        >
          <i className="fas fa-vial"></i> Load Samples
        </button>

        <button 
          className="btn btn-clear"
          onClick={onClearAll}
          disabled={loadedCount === 0}
        >
          <i className="fas fa-trash-alt"></i> Clear All
        </button>
      </div>
    </div>
  )
}

export default ControlPanel