import React, { useState, useCallback } from 'react';
import { calculateFT, inverseFT, createMask, applyMask, blendComponents } from './fourierUtils';

/**
 * Main Mixer Component - Handles all mixing operations
 */
const useMainMixer = () => {
  const [mixSettings, setMixSettings] = useState({
    // أوزان الصور الأربعة
    imageWeights: {
      0: { magnitude: 0.25, phase: 0.25 },
      1: { magnitude: 0.25, phase: 0.25 },
      2: { magnitude: 0.25, phase: 0.25 },
      3: { magnitude: 0.25, phase: 0.25 }
    },
    
    // إعدادات المنطقة
    regionSettings: {
      type: 'inner', // 'inner' أو 'outer'
      size: 50,      // نسبة الحجم
      position: { x: 50, y: 50 }, // المركز بالنسبة المئوية
      width: 60,     // عرض المستطيل
      height: 60     // ارتفاع المستطيل
    },
    
    // إعدادات الخلط
    blendSettings: {
      method: 'weighted', // 'weighted' أو 'replace'
      preservePhase: true,
      normalize: true
    }
  });

  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [ftData, setFtData] = useState({});
  const [activeOutput, setActiveOutput] = useState(0);

  /**
   * حساب Fourier Transform لجميع الصور
   */
  const calculateAllFT = useCallback(async (images) => {
    const ftResults = {};
    
    for (const img of images) {
      if (img.image) {
        try {
          const ft = await calculateFT(img.image);
          ftResults[img.id] = ft;
          setProgress(prev => prev + 25 / images.length);
        } catch (error) {
          console.error(`Error calculating FT for image ${img.id}:`, error);
        }
      }
    }
    
    setFtData(ftResults);
    return ftResults;
  }, []);

  /**
   * إنشاء قناع المنطقة المحددة
   */
  const createRegionMask = useCallback((size, regionSettings) => {
    return createMask(size.width, size.height, regionSettings);
  }, []);

  /**
   * عملية الخلط الرئيسية
   */
  const performMixing = useCallback(async (images, settings = null) => {
    setProcessing(true);
    setProgress(0);
    
    try {
      const finalSettings = settings || mixSettings;
      
      // 1. التحقق من وجود صور كافية
      const loadedImages = images.filter(img => img.image);
      if (loadedImages.length < 2) {
        throw new Error('Please load at least 2 images');
      }

      // 2. حساب Fourier Transform
      setProgress(10);
      const ftResults = await calculateAllFT(loadedImages);

      // 3. إنشاء قناع المنطقة
      setProgress(30);
      const commonSize = {
        width: loadedImages[0].size.width,
        height: loadedImages[0].size.height
      };
      
      const mask = createRegionMask(commonSize, finalSettings.regionSettings);

      // 4. تطبيق القناع على مركبات FT
      setProgress(40);
      const maskedComponents = {};
      
      for (const [imgId, ft] of Object.entries(ftResults)) {
        const id = parseInt(imgId);
        const weights = finalSettings.imageWeights[id] || { magnitude: 0.25, phase: 0.25 };
        
        maskedComponents[id] = {
          magnitude: applyMask(ft.magnitude, mask, finalSettings.regionSettings.type),
          phase: applyMask(ft.phase, mask, finalSettings.regionSettings.type),
          real: applyMask(ft.real, mask, finalSettings.regionSettings.type),
          imaginary: applyMask(ft.imaginary, mask, finalSettings.regionSettings.type)
        };
        
        // تطبيق الأوزان
        maskedComponents[id].magnitude = maskedComponents[id].magnitude.map(row => 
          row.map(val => val * weights.magnitude)
        );
        maskedComponents[id].phase = maskedComponents[id].phase.map(row => 
          row.map(val => val * weights.phase)
        );
      }

      // 5. خلط المركبات
      setProgress(60);
      const blended = blendComponents(maskedComponents, finalSettings.blendSettings);

      // 6. حساب Inverse Fourier Transform
      setProgress(80);
      const resultImage = inverseFT(
        blended.magnitude,
        blended.phase,
        blended.real,
        blended.imaginary,
        finalSettings.blendSettings
      );

      // 7. التطبيع
      setProgress(90);
      const normalizedResult = finalSettings.blendSettings.normalize 
        ? normalizeImage(resultImage)
        : resultImage;

      setProgress(100);
      setResult(normalizedResult);
      
      return {
        success: true,
        result: normalizedResult,
        ftData: ftResults,
        blendedComponents: blended
      };

    } catch (error) {
      console.error('Mixing error:', error);
      return {
        success: false,
        error: error.message
      };
    } finally {
      setTimeout(() => {
        setProcessing(false);
        setProgress(0);
      }, 500);
    }
  }, [mixSettings, calculateAllFT, createRegionMask]);

  /**
   * تطبيع الصورة
   */
  const normalizeImage = (imageData) => {
    if (!imageData || !Array.isArray(imageData) || imageData.length === 0) {
      return imageData;
    }
    
    const flatArray = imageData.flat();
    const min = Math.min(...flatArray);
    const max = Math.max(...flatArray);
    
    if (max === min) return imageData;
    
    return imageData.map(row =>
      row.map(val => ((val - min) / (max - min)) * 255)
    );
  };

  /**
   * تحديث إعدادات الخلط
   */
  const updateMixSettings = useCallback((newSettings) => {
    setMixSettings(prev => ({
      ...prev,
      ...newSettings,
      imageWeights: newSettings.imageWeights || prev.imageWeights,
      regionSettings: newSettings.regionSettings || prev.regionSettings,
      blendSettings: newSettings.blendSettings || prev.blendSettings
    }));
  }, []);

  /**
   * تحديث أوزان صورة محددة
   */
  const updateImageWeights = useCallback((imageId, magnitudeWeight, phaseWeight) => {
    setMixSettings(prev => ({
      ...prev,
      imageWeights: {
        ...prev.imageWeights,
        [imageId]: {
          magnitude: Math.max(0, Math.min(1, magnitudeWeight)),
          phase: Math.max(0, Math.min(1, phaseWeight))
        }
      }
    }));
  }, []);

  /**
   * تحديث إعدادات المنطقة
   */
  const updateRegionSettings = useCallback((newRegionSettings) => {
    setMixSettings(prev => ({
      ...prev,
      regionSettings: {
        ...prev.regionSettings,
        ...newRegionSettings
      }
    }));
  }, []);

  /**
   * إلغاء العملية
   */
  const cancelProcessing = useCallback(() => {
    setProcessing(false);
    setProgress(0);
  }, []);

  /**
   * تصدير النتيجة كصورة
   */
  const exportResult = useCallback(() => {
    if (!result) return null;
    
    const canvas = document.createElement('canvas');
    canvas.width = result[0].length;
    canvas.height = result.length;
    
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(canvas.width, canvas.height);
    
    for (let y = 0; y < canvas.height; y++) {
      for (let x = 0; x < canvas.width; x++) {
        const value = result[y][x];
        const idx = (y * canvas.width + x) * 4;
        
        imageData.data[idx] = value;     // R
        imageData.data[idx + 1] = value; // G
        imageData.data[idx + 2] = value; // B
        imageData.data[idx + 3] = 255;   // A
      }
    }
    
    ctx.putImageData(imageData, 0, 0);
    return canvas.toDataURL('image/png');
  }, [result]);

  return {
    // الحالة
    mixSettings,
    processing,
    progress,
    result,
    ftData,
    activeOutput,
    
    // الدوال
    performMixing,
    updateMixSettings,
    updateImageWeights,
    updateRegionSettings,
    cancelProcessing,
    exportResult,
    setActiveOutput,
    
    // الدوال المساعدة
    normalizeImage,
    createRegionMask
  };
};

export default useMainMixer;