import React from 'react'
import './FTComponents.css'

const FTComponents = ({ 
  images, 
  ftData,
  ftModes = [], // أوضاع FT لكل صورة
  onFTModeChange 
}) => {
  const components = [
    { id: 'magnitude', name: 'FT Magnitude', icon: 'fas fa-chart-line', color: '#3498db' },
    { id: 'phase', name: 'FT Phase', icon: 'fas fa-wave-square', color: '#2ecc71' },
    { id: 'real', name: 'FT Real', icon: 'fas fa-project-diagram', color: '#e74c3c' },
    { id: 'imaginary', name: 'FT Imaginary', icon: 'fas fa-snowflake', color: '#9b59b6' }
  ]

  // الحصول على الصور المحملة
  const loadedImages = images.filter(img => img.image)
  
  // إحصائيات FT Modes
  const getFTModeStats = () => {
    const stats = {
      original: 0,
      magnitude: 0,
      phase: 0,
      real: 0,
      imaginary: 0
    }
    
    ftModes.forEach(mode => {
      if (stats[mode] !== undefined) {
        stats[mode]++
      }
    })
    
    return stats
  }

  const ftStats = getFTModeStats()

  return (
    <div className="ft-components-panel">
      <h3>
        <i className="fas fa-sliders-h"></i> Fourier Transform Components Display
      </h3>
      
      {/* معلومات حول مكونات FT */}
      <div className="components-info">
        <div className="info-card">
          <i className="fas fa-info-circle"></i>
          <div>
            <h4>How to Use FT Components</h4>
            <p>
              Each input image can display different FT components. 
              Use the dropdown menu above each image to select:
            </p>
            <ul>
              <li><strong>Original Image</strong>: The grayscale input image</li>
              <li><strong>FT Magnitude</strong>: Fourier Transform magnitude spectrum</li>
              <li><strong>FT Phase</strong>: Fourier Transform phase spectrum</li>
              <li><strong>FT Real</strong>: Real part of the Fourier Transform</li>
              <li><strong>FT Imaginary</strong>: Imaginary part of the Fourier Transform</li>
            </ul>
          </div>
        </div>

        {/* إحصائيات */}
        <div className="stats-card">
          <h4>
            <i className="fas fa-chart-bar"></i> Current Display Statistics
          </h4>
          <div className="stats-grid">
            {Object.entries(ftStats).map(([mode, count]) => (
              <div key={mode} className="stat-item">
                <div className="stat-label">
                  {mode === 'original' ? 'Original' : 
                   mode === 'magnitude' ? 'Magnitude' :
                   mode === 'phase' ? 'Phase' :
                   mode === 'real' ? 'Real' : 'Imaginary'}
                </div>
                <div className="stat-value">{count}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* مكونات FT النشطة */}
      <div className="active-components">
        <h4>
          <i className="fas fa-eye"></i> Active FT Components per Image
        </h4>
        
        {loadedImages.length === 0 ? (
          <div className="no-images">
            <i className="fas fa-image"></i>
            <p>Load images to see their FT components</p>
          </div>
        ) : (
          <div className="image-ft-status">
            {loadedImages.map((img, index) => {
              const currentMode = ftModes[index] || 'original'
              const component = components.find(c => c.id === currentMode)
              
              return (
                <div key={img.id} className="image-ft-item">
                  <div className="image-header">
                    <div className="image-title">
                      <i className="fas fa-image"></i>
                      <span>{img.name || `Image ${img.id + 1}`}</span>
                    </div>
                    <div className="image-size">
                      {img.size?.width}×{img.size?.height}
                    </div>
                  </div>
                  
                  <div className="ft-status">
                    <div className={`ft-mode ${currentMode}`}>
                      {component ? (
                        <>
                          <i className={component.icon} style={{ color: component.color }}></i>
                          <span>{component.name}</span>
                        </>
                      ) : (
                        <>
                          <i className="fas fa-image"></i>
                          <span>Original Image</span>
                        </>
                      )}
                    </div>
                    
                    <button 
                      className="btn-change-ft"
                      onClick={() => {
                        const currentIndex = components.findIndex(c => c.id === currentMode)
                        const nextIndex = (currentIndex + 1) % (components.length + 1)
                        let nextMode
                        
                        if (nextIndex === components.length) {
                          nextMode = 'original'
                        } else {
                          nextMode = components[nextIndex].id
                        }
                        
                        if (onFTModeChange) {
                          onFTModeChange(img.id, nextMode)
                        }
                      }}
                      title="Cycle through FT components"
                    >
                      <i className="fas fa-sync-alt"></i> Change
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* معاينة مكونات FT */}
      <div className="ft-preview-section">
        <h4>
          <i className="fas fa-desktop"></i> FT Components Preview
        </h4>
        
        <div className="components-preview">
          {components.map(comp => (
            <div key={comp.id} className="component-preview">
              <div className="preview-header" style={{ borderBottomColor: comp.color }}>
                <i className={comp.icon} style={{ color: comp.color }}></i>
                <span>{comp.name}</span>
              </div>
              
              <div className="preview-content">
                <div className="preview-visual">
                  {/* إنشاء معاينة بصرية للمكون */}
                  <svg width="100%" height="100%" viewBox="0 0 200 150">
                    <rect width="200" height="150" fill="#1a1a1a" />
                    
                    {comp.id === 'magnitude' && (
                      <>
                        {/* نمط دائري للمقدار */}
                        <circle cx="100" cy="75" r="20" fill="none" stroke={comp.color} strokeWidth="2" />
                        <circle cx="100" cy="75" r="40" fill="none" stroke={comp.color} strokeWidth="1.5" opacity="0.7" />
                        <circle cx="100" cy="75" r="60" fill="none" stroke={comp.color} strokeWidth="1" opacity="0.5" />
                        <text x="100" y="35" textAnchor="middle" fill="white" fontSize="12">
                          Magnitude Spectrum
                        </text>
                      </>
                    )}
                    
                    {comp.id === 'phase' && (
                      <>
                        {/* نمط موجي للطور */}
                        <path 
                          d="M20,75 Q50,25 80,75 T140,75 T200,75" 
                          fill="none" 
                          stroke={comp.color} 
                          strokeWidth="3"
                        />
                        <text x="100" y="35" textAnchor="middle" fill="white" fontSize="12">
                          Phase Spectrum
                        </text>
                      </>
                    )}
                    
                    {comp.id === 'real' && (
                      <>
                        {/* خطوط أفقية للمركبة الحقيقية */}
                        {[30, 50, 70, 90, 110, 130].map((y, i) => (
                          <line 
                            key={i}
                            x1="30" 
                            y1={y} 
                            x2="170" 
                            y2={y} 
                            stroke={comp.color} 
                            strokeWidth="2"
                            strokeDasharray={i % 2 === 0 ? "5,5" : "none"}
                          />
                        ))}
                        <text x="100" y="35" textAnchor="middle" fill="white" fontSize="12">
                          Real Component
                        </text>
                      </>
                    )}
                    
                    {comp.id === 'imaginary' && (
                      <>
                        {/* خطوط عمودية للمركبة التخيلية */}
                        {[40, 70, 100, 130, 160].map((x, i) => (
                          <line 
                            key={i}
                            x1={x} 
                            y1="40" 
                            x2={x} 
                            y2="110" 
                            stroke={comp.color} 
                            strokeWidth="2"
                            strokeDasharray={i % 2 === 0 ? "5,5" : "none"}
                          />
                        ))}
                        <text x="100" y="35" textAnchor="middle" fill="white" fontSize="12">
                          Imaginary Component
                        </text>
                      </>
                    )}
                  </svg>
                </div>
                
                <div className="preview-description">
                  <p>
                    {comp.id === 'magnitude' && 
                      "Represents the strength of each frequency component in the image."}
                    {comp.id === 'phase' && 
                      "Represents the phase information of each frequency component."}
                    {comp.id === 'real' && 
                      "The real part of the complex Fourier Transform."}
                    {comp.id === 'imaginary' && 
                      "The imaginary part of the complex Fourier Transform."}
                  </p>
                  
                  <div className="usage-count">
                    <i className="fas fa-images"></i>
                    <span>Currently used by: {ftStats[comp.id] || 0} images</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default FTComponents