/**
 * Fourier Transform Utility Functions
 */

/**
 * حساب Fourier Transform لصورة
 */
export const calculateFT = async (imageData) => {
  return new Promise((resolve) => {
    // محاكاة حساب FT (في الإصدار الحقيقي، استخدم مكتبة مثل FFT.js)
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const grayData = rgbToGrayscale(imageData.data, canvas.width, canvas.height);
      
      // محاكاة FT (هنا نضع بيانات وهمية)
      const size = { width: canvas.width, height: canvas.height };
      const ftData = simulateFT(grayData, size);
      
      resolve(ftData);
    };
    img.src = imageData;
  });
};

/**
 * تحويل RGB إلى Grayscale
 */
const rgbToGrayscale = (data, width, height) => {
  const grayData = [];
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const gray = 0.299 * r + 0.587 * g + 0.114 * b;
    grayData.push(gray);
  }
  
  // تحويل إلى مصفوفة 2D
  const result = [];
  for (let y = 0; y < height; y++) {
    result.push(grayData.slice(y * width, (y + 1) * width));
  }
  
  return result;
};

/**
 * محاكاة Fourier Transform (للتوضيح فقط)
 */
const simulateFT = (grayData, size) => {
  const { width, height } = size;
  const magnitude = [];
  const phase = [];
  const real = [];
  const imaginary = [];
  
  // إنشاء بيانات وهمية للـFT
  for (let y = 0; y < height; y++) {
    const magRow = [];
    const phaseRow = [];
    const realRow = [];
    const imagRow = [];
    
    for (let x = 0; x < width; x++) {
      // محاكاة نمط FT
      const distance = Math.sqrt(
        Math.pow(x - width / 2, 2) + Math.pow(y - height / 2, 2)
      );
      
      const baseValue = grayData[y]?.[x] || 128;
      const frequency = distance / Math.max(width, height);
      
      // المقدار (ينخفض مع التردد)
      magRow.push(baseValue * Math.exp(-frequency * 5));
      
      // الطور (عشوائي)
      phaseRow.push(Math.random() * 2 * Math.PI - Math.PI);
      
      // المركبة الحقيقية
      realRow.push(baseValue * Math.cos(frequency * 10));
      
      // المركبة التخيلية
      imagRow.push(baseValue * Math.sin(frequency * 10));
    }
    
    magnitude.push(magRow);
    phase.push(phaseRow);
    real.push(realRow);
    imaginary.push(imagRow);
  }
  
  return {
    magnitude,
    phase,
    real,
    imaginary,
    size
  };
};

/**
 * Inverse Fourier Transform
 */
export const inverseFT = (magnitude, phase, real, imaginary, settings) => {
  const height = magnitude.length;
  const width = magnitude[0].length;
  const result = [];
  
  for (let y = 0; y < height; y++) {
    const row = [];
    for (let x = 0; x < width; x++) {
      let value;
      
      if (settings.method === 'weighted') {
        // خلط مركبين
        const magVal = magnitude[y][x] || 0;
        const phaseVal = phase[y][x] || 0;
        const realVal = real[y][x] || 0;
        // const imagVal = imaginary[y][x] || 0;
        
        // محاكاة Inverse FT
        value = (magVal * Math.cos(phaseVal) + realVal) / 2;
      } else {
        // استخدام المركبات مباشرة
        value = (real[y][x] + (imaginary[y][x] || 0)) / 2;
      }
      
      row.push(Math.max(0, Math.min(255, value)));
    }
    result.push(row);
  }
  
  return result;
};

/**
 * إنشاء قناع للمنطقة
 */
export const createMask = (width, height, regionSettings) => {
  const mask = Array(height).fill().map(() => Array(width).fill(0));
  
  const centerX = (regionSettings.position.x / 100) * width;
  const centerY = (regionSettings.position.y / 100) * height;
  
  const rectWidth = (regionSettings.width / 100) * width;
  const rectHeight = (regionSettings.height / 100) * height;
  
  const startX = Math.max(0, centerX - rectWidth / 2);
  const startY = Math.max(0, centerY - rectHeight / 2);
  const endX = Math.min(width, startX + rectWidth);
  const endY = Math.min(height, startY + rectHeight);
  
  // تعبئة المستطيل
  for (let y = Math.floor(startY); y < Math.ceil(endY); y++) {
    for (let x = Math.floor(startX); x < Math.ceil(endX); x++) {
      if (y >= 0 && y < height && x >= 0 && x < width) {
        mask[y][x] = 1;
      }
    }
  }
  
  return mask;
};

/**
 * تطبيق القناع على المركبات
 */
export const applyMask = (component, mask, regionType) => {
  const height = component.length;
  const width = component[0].length;
  const result = [];
  
  for (let y = 0; y < height; y++) {
    const row = [];
    for (let x = 0; x < width; x++) {
      const maskValue = mask[y][x] || 0;
      
      if (regionType === 'inner') {
        // المنطقة الداخلية تحتفظ بالقيمة
        row.push(component[y][x] * maskValue);
      } else {
        // المنطقة الخارجية تحتفظ بالقيمة
        row.push(component[y][x] * (1 - maskValue));
      }
    }
    result.push(row);
  }
  
  return result;
};

/**
 * خلط المركبات من صور متعددة
 */
export const blendComponents = (maskedComponents, blendSettings) => {
  const imageIds = Object.keys(maskedComponents);
  if (imageIds.length === 0) {
    return {
      magnitude: [],
      phase: [],
      real: [],
      imaginary: []
    };
  }
  
  const firstImageId = imageIds[0];
  const height = maskedComponents[firstImageId].magnitude.length;
  const width = maskedComponents[firstImageId].magnitude[0].length;
  
  const blended = {
    magnitude: Array(height).fill().map(() => Array(width).fill(0)),
    phase: Array(height).fill().map(() => Array(width).fill(0)),
    real: Array(height).fill().map(() => Array(width).fill(0)),
    imaginary: Array(height).fill().map(() => Array(width).fill(0))
  };
  
  // جمع جميع المركبات الموزونة
  for (const imgId of imageIds) {
    const components = maskedComponents[imgId];
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        blended.magnitude[y][x] += components.magnitude[y][x] || 0;
        blended.phase[y][x] += components.phase[y][x] || 0;
        blended.real[y][x] += components.real[y][x] || 0;
        blended.imaginary[y][x] += components.imaginary[y][x] || 0;
      }
    }
  }
  
  // حساب المتوسط
  const count = imageIds.length;
  if (blendSettings.method === 'weighted') {
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        blended.magnitude[y][x] /= count;
        blended.phase[y][x] /= count;
        blended.real[y][x] /= count;
        blended.imaginary[y][x] /= count;
      }
    }
  }
  
  return blended;
};