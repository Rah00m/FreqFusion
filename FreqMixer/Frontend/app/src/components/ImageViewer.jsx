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
  const modeRef = useRef("idle"); // idle | drawing | moving | resizing
  const activeHandleRef = useRef(null); // 'nw','n','ne','e','se','s','sw','w'
  const initialRectRef = useRef(null);
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
    // If clicking empty area -> start drawing
    const pos = getPosInNatural(e);
    if (!pos) return;
    drawingRef.current = true;
    modeRef.current = "drawing";
    startRef.current = pos;
    draftRef.current = { x: pos.x, y: pos.y, width: 0, height: 0 };
    forceRender();
  };

  const handleMouseMove = (e) => {
    if (!enableMask) return;
    const pos = getPosInNatural(e);
    if (!pos) return;
    if (modeRef.current === "drawing" && drawingRef.current) {
      if (!startRef.current) return;
      draftRef.current = normalizeRect(startRef.current, pos);
      forceRender();
      return;
    }
    if (
      modeRef.current === "moving" &&
      draftRef.current &&
      initialRectRef.current
    ) {
      const dx = pos.x - startRef.current.x;
      const dy = pos.y - startRef.current.y;
      const natW = pos.natW;
      const natH = pos.natH;
      const newX = Math.min(
        Math.max(initialRectRef.current.x + dx, 0),
        natW - initialRectRef.current.width
      );
      const newY = Math.min(
        Math.max(initialRectRef.current.y + dy, 0),
        natH - initialRectRef.current.height
      );
      draftRef.current = {
        ...initialRectRef.current,
        x: Math.round(newX),
        y: Math.round(newY),
      };
      forceRender();
      return;
    }
    if (
      modeRef.current === "resizing" &&
      draftRef.current &&
      initialRectRef.current
    ) {
      const start = startRef.current;
      const natW = pos.natW;
      const natH = pos.natH;
      const anchor = activeHandleRef.current;
      // Compute new rect based on handle
      let x1 = initialRectRef.current.x;
      let y1 = initialRectRef.current.y;
      let x2 = initialRectRef.current.x + initialRectRef.current.width;
      let y2 = initialRectRef.current.y + initialRectRef.current.height;
      // Determine which edges move
      if (anchor.includes("w")) x1 = Math.min(Math.max(pos.x, 0), x2 - 1);
      if (anchor.includes("e")) x2 = Math.max(Math.min(pos.x, natW), x1 + 1);
      if (anchor.includes("n")) y1 = Math.min(Math.max(pos.y, 0), y2 - 1);
      if (anchor.includes("s")) y2 = Math.max(Math.min(pos.y, natH), y1 + 1);
      const newRect = normalizeRect({ x: x1, y: y1 }, { x: x2, y: y2 });
      draftRef.current = newRect;
      forceRender();
      return;
    }
  };

  const handleMouseUp = (e) => {
    if (!enableMask) return;
    const pos = getPosInNatural(e);
    drawingRef.current = false;
    const mode = modeRef.current;
    modeRef.current = "idle";
    activeHandleRef.current = null;
    if (!pos || !startRef.current || !draftRef.current) {
      draftRef.current = null;
      startRef.current = null;
      initialRectRef.current = null;
      forceRender();
      return;
    }
    const finalRect = draftRef.current;
    draftRef.current = null;
    startRef.current = null;
    initialRectRef.current = null;
    forceRender();
    if (onMaskDraw && finalRect.width > 2 && finalRect.height > 2) {
      onMaskDraw(finalRect);
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

  const beginMove = (e) => {
    e.stopPropagation();
    const pos = getPosInNatural(e);
    if (!pos || !activeRect) return;
    modeRef.current = "moving";
    drawingRef.current = true;
    startRef.current = pos;
    initialRectRef.current = { ...activeRect };
    draftRef.current = { ...activeRect };
    forceRender();
  };

  const beginResize = (handle, e) => {
    e.stopPropagation();
    const pos = getPosInNatural(e);
    if (!pos || !activeRect) return;
    modeRef.current = "resizing";
    activeHandleRef.current = handle;
    drawingRef.current = true;
    startRef.current = pos;
    initialRectRef.current = { ...activeRect };
    draftRef.current = { ...activeRect };
    forceRender();
  };

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
                onMouseDown={beginMove}
              >
                <span className="mask-label">
                  {(mask?.type || "inner").toUpperCase()} ·{" "}
                  {Math.round(activeRect.width)}×{Math.round(activeRect.height)}
                </span>
                {/* Resize handles */}
                <div
                  className="mask-handle nw"
                  onMouseDown={(e) => beginResize("nw", e)}
                />
                <div
                  className="mask-handle n"
                  onMouseDown={(e) => beginResize("n", e)}
                />
                <div
                  className="mask-handle ne"
                  onMouseDown={(e) => beginResize("ne", e)}
                />
                <div
                  className="mask-handle e"
                  onMouseDown={(e) => beginResize("e", e)}
                />
                <div
                  className="mask-handle se"
                  onMouseDown={(e) => beginResize("se", e)}
                />
                <div
                  className="mask-handle s"
                  onMouseDown={(e) => beginResize("s", e)}
                />
                <div
                  className="mask-handle sw"
                  onMouseDown={(e) => beginResize("sw", e)}
                />
                <div
                  className="mask-handle w"
                  onMouseDown={(e) => beginResize("w", e)}
                />
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
