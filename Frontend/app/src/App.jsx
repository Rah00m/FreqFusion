import React, { useState, useEffect } from "react";
import "./App.css";
import ImageViewer from "./components/ImageViewer";
import ControlPanel from "./components/ControlPanel";
import MixerControls from "./components/MixerControls";

import API from "./services/api";

function App() {
  const toDataUrl = (b64) => {
    if (!b64) return null;
    return b64.startsWith("data:") ? b64 : `data:image/png;base64,${b64}`;
  };

  // States
  const [images, setImages] = useState(
    Array(4)
      .fill()
      .map((_, i) => ({
        id: i,
        image: null,
        size: null,
        ftMode: "magnitude",
        weights: {
          magnitude: 0.25,
            phase: 1,
          real: 0.25,
          imaginary: 0.25,
        },
        mask: null,
        maskType: "inner",
      }))
  );
  const [commonSize, setCommonSize] = useState(null);
  const [loadedCount, setLoadedCount] = useState(0);
  const [componentMode, setComponentMode] = useState("magnitude_phase");
  const [preserveEnergy, setPreserveEnergy] = useState(false);
  const [mixResult, setMixResult] = useState(null);
  const [outputImages, setOutputImages] = useState([null, null]);
  const [activeOutput, setActiveOutput] = useState(0);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [ftComponents, setFTComponents] = useState(
    Array(4)
      .fill()
      .map(() => ({}))
  );
  const [showWeights, setShowWeights] = useState(Array(4).fill(false));
  const [autoMixing, setAutoMixing] = useState(false);
  const [settingsChanged, setSettingsChanged] = useState(false);

  // Refs for request management
  const abortControllerRef = React.useRef(null);
  const mixTimeoutRef = React.useRef(null);
  const autoMixTimeoutRef = React.useRef(null);

  // Effects
  const fetchAllImages = async () => {
    try {
      const data = await API.getImages();
      const imgs = data?.images || [];
      setImages(
        Array(4)
          .fill()
          .map((_, i) => ({
            id: i,
            image: toDataUrl(imgs[i]?.base64),
            size: imgs[i]?.size || null,
            ftMode: "magnitude",
            weights: {
              magnitude: imgs[i]?.weights?.magnitude ?? 0.25,
              phase: imgs[i]?.weights?.phase ?? 1,
              real: imgs[i]?.weights?.real ?? 0.25,
              imaginary: imgs[i]?.weights?.imaginary ?? 0.25,
            },
            mask: imgs[i]?.rectangle || null,
            maskType: imgs[i]?.rectangle?.type || "inner",
          }))
      );
      setCommonSize(data?.common_size || null);
      setLoadedCount(data?.loaded_count || 0);
    } catch (err) {
      setError(err.message || "Failed to load images");
    }
  };

  useEffect(() => {
    const loaded = images.filter((img) => img.image);
    setLoadedCount(loaded.length);
    if (loaded.length > 0) {
      const maxW = Math.max(
        ...loaded.map((img) => img.size?.width || Infinity)
      );
      const maxH = Math.max(
        ...loaded.map((img) => img.size?.height || Infinity)
      );
      setCommonSize(maxW !== Infinity ? { width: maxW, height: maxH } : null);
    }
  }, [images]);

  useEffect(() => {
    fetchAllImages();

    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (mixTimeoutRef.current) {
        clearTimeout(mixTimeoutRef.current);
      }
    };
  }, []);

  const fetchFTComponent = async (id, mode) => {
    try {
      await API.calculateFT(id);
      const res = await API.getComponent(id, mode);
      const dataUrl = toDataUrl(res?.base64);
      setFTComponents((prev) =>
        prev.map((item, idx) =>
          idx === id ? { ...item, [mode]: dataUrl } : item
        )
      );
    } catch (err) {
      setError(err.message || "Failed to fetch FT component");
    }
  };

  // Handlers
  const handleImageLoad = async (id, file, imgSize) => {
    try {
      setLoading(true);
      setError(null);
      await API.uploadImage(id, file);
      try {
        await API.convertToGrayscale(id);
      } catch (err) {
        console.warn("grayscale failed", err);
      }
      try {
        await API.calculateFT(id);
      } catch (err) {
        console.warn("calculate FT failed", err);
      }
      await fetchAllImages();
      await fetchFTComponent(id, images[id]?.ftMode || "magnitude");
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleImageClear = async (id) => {
    try {
      setLoading(true);
      setError(null);
      await API.deleteImage(id);
      await fetchAllImages();
      setFTComponents((prev) =>
        prev.map((item, idx) => (idx === id ? {} : item))
      );
      setImages((prev) =>
        prev.map((img, idx) => (idx === id ? { ...img, mask: null } : img))
      );
    } catch (err) {
      setError(err.message || "Delete failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFTChange = (id, newMode) => {
    setImages((prev) =>
      prev.map((img, idx) => (idx === id ? { ...img, ftMode: newMode } : img))
    );
    fetchFTComponent(id, newMode);
  };

  const handleWeightChange = (id, component, value) => {
    const val = parseFloat(value);
    setImages((prev) =>
      prev.map((img, idx) =>
        idx === id
          ? {
              ...img,
              weights: {
                ...img.weights,
                [component]: Number.isFinite(val) ? val : 0,
              },
            }
          : img
      )
    );

    // Mark settings as changed for real-time mixing
    if (autoMixing) {
      setSettingsChanged(true);

      // Clear any previous auto-mix timeout
      if (autoMixTimeoutRef.current) {
        clearTimeout(autoMixTimeoutRef.current);
      }

      // Trigger re-mixing after a short delay to avoid too many requests
      autoMixTimeoutRef.current = setTimeout(() => {
        setSettingsChanged(false);
        triggerAutoMix();
      }, 500);
    }
  };

  const handleMaskDraw = (id, rect) => {
    setImages((prev) =>
      prev.map((img, idx) =>
        idx === id
          ? {
              ...img,
              mask: {
                ...rect,
                type: img.maskType || img.mask?.type || "inner",
              },
            }
          : img
      )
    );
  };

  const handleMaskClear = (id) => {
    setImages((prev) =>
      prev.map((img, idx) => (idx === id ? { ...img, mask: null } : img))
    );
  };

  const handleMaskTypeChange = (id, type) => {
    setImages((prev) =>
      prev.map((img, idx) =>
        idx === id
          ? {
              ...img,
              maskType: type,
              mask: img.mask ? { ...img.mask, type } : img.mask,
            }
          : img
      )
    );
  };

  const handleLoadSamples = () => {
    images.forEach((_, i) => {
      setTimeout(() => {
        const w = 300 + Math.floor(Math.random() * 100);
        const h = 300 + Math.floor(Math.random() * 100);

        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");

        const gray = 50 + i * 40;
        ctx.fillStyle = `rgb(${gray}, ${gray}, ${gray})`;
        ctx.fillRect(0, 0, w, h);

        ctx.fillStyle = `rgb(100, 150, 200)`;
        ctx.fillRect(30, 30, w - 60, h - 60);

        ctx.fillStyle = "white";
        ctx.font = "bold 30px Arial";
        ctx.textAlign = "center";
        ctx.fillText(`Sample ${i + 1}`, w / 2, h / 2);
        canvas.toBlob((blob) => {
          if (!blob) return;
          const file = new File([blob], `sample_${i + 1}.png`, {
            type: "image/png",
          });
          handleImageLoad(i, file, { width: w, height: h });
        }, "image/png");
      }, i * 200);
    });
  };

  const handleClearAll = async () => {
    try {
      setLoading(true);
      setError(null);
      await API.deleteAllImages();
      await fetchAllImages();
      setMixResult(null);
      setOutputImages([null, null]);
      setFTComponents(
        Array(4)
          .fill()
          .map(() => ({}))
      );
    } catch (err) {
      setError(err.message || "Clear failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    // Cancel the current request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    // Clear the queued mixing timeout
    if (mixTimeoutRef.current) {
      clearTimeout(mixTimeoutRef.current);
      mixTimeoutRef.current = null;
    }
    // Clear auto-mix timeout
    if (autoMixTimeoutRef.current) {
      clearTimeout(autoMixTimeoutRef.current);
      autoMixTimeoutRef.current = null;
    }
    setLoading(false);
    setProgress(0);
    setAutoMixing(false);
  };

  // Helper function to prepare and execute mixing
  const executeMixing = async (currentImages, abortSignal) => {
    const loaded = currentImages.filter((img) => img.image);
    if (loaded.length < 4) {
      setError("Please load all 4 images before mixing");
      return false;
    }

    try {
      setError(null);
      setProgress(10);

      // Normalize sizes on backend and calculate all FTs before mixing
      let mixingSize = commonSize;
      try {
        await API.resizeAll();
        const sizeResponse = await API.getCommonSize();
        mixingSize = sizeResponse?.common_size || mixingSize;
        setProgress(20);
        if (abortSignal.aborted) return false;
      } catch (_) {}

      try {
        await API.calculateAllFT();
        setProgress(30);
        if (abortSignal.aborted) return false;
      } catch (_) {}

      const clampRect = (rect, size) => {
        if (!rect || !size) return rect;
        const x = Math.max(0, Math.min(rect.x, size.width - 1));
        const y = Math.max(0, Math.min(rect.y, size.height - 1));
        const maxW = size.width - x;
        const maxH = size.height - y;
        const w = Math.max(1, Math.min(rect.width, maxW));
        const h = Math.max(1, Math.min(rect.height, maxH));
        return {
          x: Math.round(x),
          y: Math.round(y),
          width: Math.round(w),
          height: Math.round(h),
          type: rect.type,
        };
      };

      const prepareMixPayload = (
        images,
        rectanglesList,
        componentMode,
        preserveEnergy = false
      ) => {
        const weightPairs = images.map((img, idx) => {
          if (componentMode === "magnitude_phase") {
            const mag = Number(img.weights?.magnitude ?? 0);
            const phase = Number(img.weights?.phase ?? 0);
            if (!Number.isFinite(mag) || !Number.isFinite(phase)) {
              throw new Error(`Image ${idx + 1} has invalid magnitude/phase`);
            }
            return [mag, phase];
          }
          const real = Number(img.weights?.real ?? 0);
          const imag = Number(img.weights?.imaginary ?? 0);
          if (!Number.isFinite(real) || !Number.isFinite(imag)) {
            throw new Error(`Image ${idx + 1} has invalid real/imaginary`);
          }
          return [real, imag];
        });

        if (weightPairs.length !== images.length) {
          throw new Error("Mismatch between weights and images count");
        }

        return {
          weights: weightPairs,
          rectangles: rectanglesList,
          component_mode: componentMode,
          preserve_energy: preserveEnergy,
        };
      };

      const rectanglesList = currentImages.map((img) =>
        img.mask
          ? clampRect(
              { ...img.mask, type: img.mask.type || img.maskType || "inner" },
              mixingSize
            )
          : null
      );

      const payload = prepareMixPayload(
        currentImages,
        rectanglesList,
        componentMode,
        preserveEnergy
      );

      console.log("Sending mix payload:", JSON.stringify(payload, null, 2));

      setProgress(40);
      if (abortSignal.aborted) return false;

      // Perform mixing with progress simulation
      const res = await API.mixFT(payload);

      if (abortSignal.aborted) return false;

      setProgress(90);
      const img = toDataUrl(res?.base64);
      setMixResult({ ...res, base64: img });
      setOutputImages((prev) => {
        const next = [...prev];
        next[activeOutput] = img;
        return next;
      });

      setProgress(100);
      return true;
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Mix failed");
      }
      return false;
    }
  };

  const performMixing = async (abortSignal) => {
    try {
      setLoading(true);
      const success = await executeMixing(images, abortSignal);

      if (success) {
        // Keep 100% for a short moment then hide
        setTimeout(() => {
          setProgress(0);
          setLoading(false);
        }, 800);
      } else {
        setLoading(false);
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Mix failed");
      }
      setLoading(false);
    }
  };

  // Auto-mixing function - triggered by weight changes
  const triggerAutoMix = async () => {
    // Cancel any previous mixing operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      setLoading(true);
      const success = await executeMixing(
        images,
        abortControllerRef.current.signal
      );

      if (success) {
        // Auto-hide progress after completion
        setTimeout(() => {
          setProgress(0);
          setLoading(false);
        }, 500);
      } else {
        setLoading(false);
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Auto-mix failed");
      }
      setLoading(false);
    }
  };

  const handleStartMixing = async () => {
    // Enable auto-mixing mode
    setAutoMixing(true);
    setSettingsChanged(false);

    // Cancel any previous mixing operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Cancel any queued mixing timeout
    if (mixTimeoutRef.current) {
      clearTimeout(mixTimeoutRef.current);
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    await performMixing(abortControllerRef.current.signal);
  };

  // Outputs
  const outputs = [0, 1].map((id) => ({
    id,
    image: outputImages[id],
    active: id === activeOutput,
  }));

  const processing = loading;

  return (
    <div className="app">
      <header className="app-header">
        <h1>
          <i className="fas fa-wave-square"></i> FT Image Mixer
        </h1>
      </header>

      {/* استخدم ControlPanel هنا */}
      <ControlPanel
        loadedCount={loadedCount}
        commonSize={commonSize}
        activeOutput={activeOutput}
        onLoadSamples={handleLoadSamples}
        onClearAll={handleClearAll}
      />

      <div className="main-content">
        {/* Left Panel */}
        <div className="left-panel">
          {/* Original Images */}
          <div className="original-images-row">
            {images.map((img) => (
              <div key={`orig-${img.id}`} className="image-column">
                <div className="column-header">
                  <span>Image {img.id + 1}</span>
                </div>
                <ImageViewer
                  id={img.id}
                  image={img.image}
                  isOutput={false}
                  showFT={false}
                  onImageLoad={handleImageLoad}
                  onImageClear={handleImageClear}
                />

                {img.image && (
                  <>
                    <button
                      className="toggle-weights-btn"
                      onClick={() => {
                        setShowWeights((prev) =>
                          prev.map((val, idx) => (idx === img.id ? !val : val))
                        );
                      }}
                    >
                      <i
                        className={`fas fa-chevron-${
                          showWeights[img.id] ? "up" : "down"
                        }`}
                      ></i>
                      Weights
                    </button>
                    {showWeights[img.id] && (
                      <div className="weight-controls">
                        {["magnitude", "phase", "real", "imaginary"].map(
                          (comp) => (
                            <div
                              className="slider-group"
                              key={`${img.id}-${comp}`}
                            >
                              <div className="slider-label">
                                <span style={{ textTransform: "capitalize" }}>
                                  {comp}
                                </span>
                                <span>
                                  {((img.weights?.[comp] ?? 0) * 100).toFixed(
                                    0
                                  )}
                                  %
                                </span>
                              </div>
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.01"
                                value={img.weights?.[comp] ?? 0}
                                onChange={(e) =>
                                  handleWeightChange(
                                    img.id,
                                    comp,
                                    e.target.value
                                  )
                                }
                              />
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {/* FT Viewers */}
          <div className="ft-viewers-row">
            {images.map((img) => (
              <div key={`ft-${img.id}`} className="image-column">
                <div className="ft-controls">
                  <select
                    value={img.ftMode}
                    onChange={(e) => handleFTChange(img.id, e.target.value)}
                    disabled={!img.image}
                    className="ft-select"
                  >
                    <option value="magnitude">Magnitude</option>
                    <option value="phase">Phase</option>
                    <option value="real">Real</option>
                    <option value="imaginary">Imaginary</option>
                  </select>
                  <div className="mask-controls">
                    <label>Mask</label>
                    <select
                      value={img.maskType}
                      onChange={(e) =>
                        handleMaskTypeChange(img.id, e.target.value)
                      }
                      disabled={!img.image}
                    >
                      <option value="inner">Inner</option>
                      <option value="outer">Outer</option>
                    </select>
                    <button
                      className="btn-link"
                      onClick={() => handleMaskClear(img.id)}
                      disabled={!img.mask}
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <ImageViewer
                  id={img.id}
                  image={img.image}
                  isOutput={false}
                  showFT={true}
                  ftMode={img.ftMode}
                  ftImage={ftComponents[img.id]?.[img.ftMode] || null}
                  enableMask={true}
                  mask={img.mask}
                  onMaskDraw={(rect) => handleMaskDraw(img.id, rect)}
                  onMaskClear={() => handleMaskClear(img.id)}
                  onImageLoad={handleImageLoad}
                  onImageClear={handleImageClear}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel */}
        <div className="right-panel">
          <div className="outputs-panel">
            <h2>
              <i className="fas fa-desktop"></i> Output
            </h2>
            <div style={{ marginBottom: "12px", fontSize: "12px" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "4px",
                  fontWeight: "bold",
                }}
              >
                Mode:
              </label>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <label style={{ fontSize: "12px" }}>
                  <input
                    type="radio"
                    name="componentMode"
                    value="magnitude_phase"
                    checked={componentMode === "magnitude_phase"}
                    onChange={(e) => setComponentMode(e.target.value)}
                    style={{ marginRight: "2px" }}
                  />
                  Mag/Phase
                </label>
                <label style={{ fontSize: "12px" }}>
                  <input
                    type="radio"
                    name="componentMode"
                    value="real_imaginary"
                    checked={componentMode === "real_imaginary"}
                    onChange={(e) => setComponentMode(e.target.value)}
                    style={{ marginRight: "2px" }}
                  />
                  Real/Imag
                </label>
              </div>
            </div>
            <MixerControls
              processing={processing}
              progress={progress}
              onStartMixing={handleStartMixing}
              onCancel={handleCancel}
            />
            <div className="output-tabs">
              {outputs.map((output) => (
                <button
                  key={output.id}
                  className={`output-tab ${output.active ? "active" : ""}`}
                  onClick={() => setActiveOutput(output.id)}
                >
                  Output {output.id + 1}
                </button>
              ))}
            </div>
            <div className="outputs-grid" style={{ marginTop: "12px" }}>
              {outputs
                .filter((out) => out.active)
                .map((output) => (
                  <div key={output.id} className="output-container">
                    <ImageViewer
                      id={output.id}
                      image={output.image}
                      isOutput={true}
                      isActive={output.active}
                      onActivate={setActiveOutput}
                    />
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
