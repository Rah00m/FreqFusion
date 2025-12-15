import React, { useRef } from "react";
import "./ImageViewer.css";

const ImageViewer = ({
  id,
  image,
  name,
  size,
  isOutput = false,
  isActive = false,
  showFT = false,
  ftMode = "magnitude",
  ftImage = null,
  enableMask = false,
  mask = null,
  onMaskDraw,
  onMaskClear,
  onImageLoad,
  onImageClear,
  onActivate,
}) => {
  const fileInputRef = useRef(null);
  const imgRef = useRef(null);
  const drawingRef = useRef(false);
  const startRef = useRef(null);
  const draftRef = useRef(null);
  const [, forceRender] = React.useReducer((x) => x + 1, 0);

  const handleDoubleClick = () => {
    if (showFT) return;
    if (isOutput) {
      onActivate(id);
    } else {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        onImageLoad(id, file, {
          width: img.width,
          height: img.height,
        });
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
    e.target.value = null;
  };

  const handleClear = (e) => {
    e.stopPropagation();
    onImageClear(id);
  };
  const displayImage = showFT ? ftImage : image;
  const hasImage = displayImage !== null;

  const getPosInNatural = (e) => {
    if (!imgRef.current) return null;
    const bounds = imgRef.current.getBoundingClientRect();
    const natW = imgRef.current.naturalWidth || bounds.width;
    const natH = imgRef.current.naturalHeight || bounds.height;
    const x = Math.min(Math.max(e.clientX - bounds.left, 0), bounds.width);
    const y = Math.min(Math.max(e.clientY - bounds.top, 0), bounds.height);
    const scaleX = natW / bounds.width;
    const scaleY = natH / bounds.height;
    return { x: x * scaleX, y: y * scaleY, bounds, natW, natH };
  };

  const toDisplayRect = (rect) => {
    if (!rect || !imgRef.current) return null;
    const bounds = imgRef.current.getBoundingClientRect();
    const natW = imgRef.current.naturalWidth || bounds.width;
    const natH = imgRef.current.naturalHeight || bounds.height;
    const scaleX = bounds.width / natW;
    const scaleY = bounds.height / natH;
    return {
      left: rect.x * scaleX,
      top: rect.y * scaleY,
      width: rect.width * scaleX,
      height: rect.height * scaleY,
    };
  };

  const normalizeRect = (start, end) => {
    const x = Math.min(start.x, end.x);
    const y = Math.min(start.y, end.y);
    const width = Math.abs(end.x - start.x);
    const height = Math.abs(end.y - start.y);
    return {
      x: Math.round(x),
      y: Math.round(y),
      width: Math.round(width),
      height: Math.round(height),
    };
  };

  const handleMouseDown = (e) => {
    if (!enableMask || !hasImage) return;
    const pos = getPosInNatural(e);
    if (!pos) return;
    drawingRef.current = true;
    startRef.current = pos;
    draftRef.current = { x: pos.x, y: pos.y, width: 0, height: 0 };
    forceRender();
  };

  const handleMouseMove = (e) => {
    if (!enableMask || !drawingRef.current) return;
    const pos = getPosInNatural(e);
    if (!pos || !startRef.current) return;
    draftRef.current = normalizeRect(startRef.current, pos);
    forceRender();
  };

  const handleMouseUp = (e) => {
    if (!enableMask || !drawingRef.current) return;
    const pos = getPosInNatural(e);
    drawingRef.current = false;
    if (!pos || !startRef.current) {
      draftRef.current = null;
      forceRender();
      return;
    }
    const rect = normalizeRect(startRef.current, pos);
    draftRef.current = null;
    startRef.current = null;
    forceRender();
    if (onMaskDraw && rect.width > 2 && rect.height > 2) {
      onMaskDraw(rect);
    }
  };

  const handleMouseLeave = () => {
    if (!enableMask) return;
    drawingRef.current = false;
    draftRef.current = null;
    startRef.current = null;
    forceRender();
  };

  const activeRect = draftRef.current || mask;
  const displayRect = toDisplayRect(activeRect);

  return (
    <div
      className={`image-viewer ${isOutput ? "output" : "input"} ${
        isActive ? "active" : ""
      } ${showFT ? "ft-mode" : ""}`}
      onDoubleClick={handleDoubleClick}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
    >
      <div className="viewer-container">
        {displayImage ? (
          <>
            <img
              src={displayImage}
              alt={name}
              className="displayed-image"
              style={{
                maxWidth: "100%",
                maxHeight: "100%",
                objectFit: "contain",
              }}
              ref={imgRef}
            />
            {enableMask && displayRect && (
              <div
                className="mask-rect"
                style={{
                  left: `${displayRect.left}px`,
                  top: `${displayRect.top}px`,
                  width: `${displayRect.width}px`,
                  height: `${displayRect.height}px`,
                }}
              >
                <span className="mask-label">{mask?.type || "inner"}</span>
                {onMaskClear && (
                  <button
                    className="clear-mask"
                    onClick={(e) => {
                      e.stopPropagation();
                      onMaskClear();
                    }}
                    title="Clear region"
                  >
                    ×
                  </button>
                )}
              </div>
            )}
            <button
              className="clear-btn"
              onClick={handleClear}
              title="Clear image"
            >
              <i className="fas fa-times"></i>
            </button>
          </>
        ) : (
          <div className="placeholder">
            <i className="fas fa-image"></i>
            <p>Double-click to {isOutput ? "activate" : "load image"}</p>
          </div>
        )}
      </div>

      {/* معلومات الصورة */}
      <div className="image-info">
        <div className="image-name">
          {name || (isOutput ? `Output ${id + 1}` : `Input ${id + 1}`)}
          {showFT && <span className="ft-mode-badge">{ftMode}</span>}
        </div>
        {size && (
          <div className="image-size">
            {size.width} × {size.height}
          </div>
        )}
      </div>

      {/* Input file مخفي */}
      {!isOutput && !showFT && (
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept="image/*"
          onChange={handleFileChange}
        />
      )}
    </div>
  );
};

export default ImageViewer;
