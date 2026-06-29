/* 文档上传 — 拖拽 + 进度条 */

document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('upload-modal');
  const dropzone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('file-input');
  const progressDiv = document.getElementById('upload-progress');
  const progressFill = document.getElementById('progress-fill');
  const uploadStatus = document.getElementById('upload-status');

  // 打开模态框
  document.getElementById('btn-upload').addEventListener('click', () => {
    modal.classList.remove('hidden');
    modal.classList.add('active');
    resetUpload();
    loadDocList();
  });

  // 关闭模态框
  document.getElementById('btn-close-modal').addEventListener('click', () => {
    modal.classList.add('hidden');
    modal.classList.remove('active');
  });

  document.querySelector('.modal-overlay').addEventListener('click', () => {
    modal.classList.add('hidden');
    modal.classList.remove('active');
  });

  // 点击选择文件
  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
  });

  // 拖拽上传
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-over');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) uploadFile(files[0]);
  });

  function resetUpload() {
    dropzone.style.display = '';
    progressDiv.classList.add('hidden');
    progressFill.style.width = '0%';
  }

  async function uploadFile(file) {
    // 客户端验证
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    const allowed = ['.pdf', '.docx', '.txt', '.md'];
    if (!allowed.includes(ext)) {
      alert('不支持的文件类型: ' + ext + '\n支持: ' + allowed.join(', '));
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      alert('文件大小超过 50MB 限制');
      return;
    }

    // 显示进度
    dropzone.style.display = 'none';
    progressDiv.classList.remove('hidden');
    uploadStatus.textContent = '正在上传 ' + file.name + ' ...';

    const formData = new FormData();
    formData.append('file', file);

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 50); // 上传占 50%
          progressFill.style.width = pct + '%';
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const data = JSON.parse(xhr.responseText);
          progressFill.style.width = '100%';
          uploadStatus.innerHTML = '✅ <strong>' + escapeHtml(data.filename) +
            '</strong> 索引完成！共 <strong>' + data.chunks_count + '</strong> 个文本块';

          // 刷新文档列表
          setTimeout(() => {
            loadDocList();
            // 延迟关闭
            setTimeout(() => {
              modal.classList.add('hidden');
              modal.classList.remove('active');
            }, 1500);
          }, 500);
        } else {
          let errMsg = '上传失败';
          try {
            const err = JSON.parse(xhr.responseText);
            errMsg = err.detail || errMsg;
          } catch (e) {}
          uploadStatus.innerHTML = '❌ <strong>错误:</strong> ' + escapeHtml(errMsg);
        }
      });

      xhr.addEventListener('error', () => {
        uploadStatus.innerHTML = '❌ <strong>网络错误</strong>，请重试';
      });

      xhr.open('POST', '/api/documents/upload');
      xhr.send(formData);
    } catch (err) {
      uploadStatus.innerHTML = '❌ <strong>错误:</strong> ' + escapeHtml(err.message);
    }
  }
});
