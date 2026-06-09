/**
 * compress.js - 前端图片压缩
 * 在上传前自动压缩图片，大幅提升上传速度
 */

/**
 * 压缩图片
 * @param {File} file - 原始文件
 * @param {number} maxWidth - 最大宽度（px）
 * @param {number} quality - JPEG 质量 0~1
 * @param {function(File)} callback - 压缩完成回调，返回新 File
 * @param {function(string)} errorCallback - 错误回调（可选）
 */
function compressImage(file, maxWidth, quality, callback, errorCallback) {
    // 如果不是图片，直接返回原文件
    if (!file.type.startsWith('image/')) {
        callback(file);
        return;
    }

    var reader = new FileReader();
    reader.onload = function(e) {
        var img = new Image();
        img.onload = function() {
            // 如果图片本来就很小，直接返回
            if (img.width <= maxWidth && file.size <= 100 * 1024) {
                callback(file);
                return;
            }

            var canvas = document.createElement('canvas');
            var w = img.width;
            var h = img.height;

            // 按最大宽度缩放
            if (w > maxWidth) {
                h = Math.round(h * maxWidth / w);
                w = maxWidth;
            }

            canvas.width = w;
            canvas.height = h;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, w, h);

            // 导出为 JPEG（统一用 JPEG 压缩更小）
            canvas.toBlob(function(blob) {
                if (!blob) {
                    if (errorCallback) errorCallback('压缩失败');
                    else callback(file);
                    return;
                }
                // 用原始文件名但改扩展名为 .jpg
                var name = file.name.replace(/\.[^.]+$/, '') + '.jpg';
                var compressedFile = new File([blob], name, {
                    type: 'image/jpeg',
                    lastModified: Date.now()
                });
                callback(compressedFile);
            }, 'image/jpeg', quality);
        };
        img.onerror = function() {
            if (errorCallback) errorCallback('图片加载失败');
            else callback(file);
        };
        img.src = e.target.result;
    };
    reader.onerror = function() {
        if (errorCallback) errorCallback('文件读取失败');
        else callback(file);
    };
    reader.readAsDataURL(file);
}
