import React from "react";
import "./MixerControls.css";

const MixerControls = ({ processing, progress, onStartMixing, onCancel }) => {
  return (
    <div className="mixer-controls">
      {/* Progress Bar */}
      {processing && (
        <div className="control-section">
          <h3>
            <i className="fas fa-spinner fa-spin"></i> Processing
          </h3>
          <div className="progress-container">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <span className="progress-text">{Math.round(progress)}%</span>
            <button className="btn-cancel" onClick={onCancel}>
              <i className="fas fa-stop"></i> Cancel
            </button>
          </div>
        </div>
      )}

      {/* Start Button */}
      <div className="action-section">
        <button
          className="btn-start"
          onClick={onStartMixing}
          disabled={processing}
        >
          <i className="fas fa-play"></i> Start Mixing
        </button>
      </div>
    </div>
  );
};

export default MixerControls;
