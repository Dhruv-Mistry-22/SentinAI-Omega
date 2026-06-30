document.addEventListener('DOMContentLoaded', () => {
    // ---- Navigation ----
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.module-view');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            views.forEach(v => v.classList.remove('active-view'));

            item.classList.add('active');
            document.getElementById(item.dataset.target).classList.add('active-view');
        });
    });

    // ---- Module 1: Document Analysis ----
    const docInput = document.getElementById('doc-input');
    const docZone = document.getElementById('doc-upload-zone');
    const docList = document.getElementById('doc-file-list');
    const btnAnalyzeDocs = document.getElementById('btn-analyze-docs');
    const docLoader = document.getElementById('doc-loader');
    const docResults = document.getElementById('doc-results');
    
    let selectedDocs = [];

    const handleDocFiles = (files) => {
        for(let file of files) {
            if(!selectedDocs.some(d => d.name === file.name)) {
                selectedDocs.push(file);
            }
        }
        renderDocList();
    };

    const renderDocList = () => {
        docList.innerHTML = '';
        selectedDocs.forEach((f, i) => {
            const li = document.createElement('li');
            li.className = 'file-item';
            li.innerHTML = `📄 ${f.name} <button class="btn-text" style="color:var(--accent-red); margin-left:8px;" onclick="removeDoc(${i})">×</button>`;
            docList.appendChild(li);
        });
        btnAnalyzeDocs.disabled = selectedDocs.length < 2;
    };

    window.removeDoc = (index) => {
        selectedDocs.splice(index, 1);
        renderDocList();
    };

    docInput.addEventListener('change', (e) => handleDocFiles(e.target.files));
    docZone.addEventListener('dragover', (e) => { e.preventDefault(); docZone.classList.add('dragover'); });
    docZone.addEventListener('dragleave', () => docZone.classList.remove('dragover'));
    docZone.addEventListener('drop', (e) => {
        e.preventDefault();
        docZone.classList.remove('dragover');
        handleDocFiles(e.dataTransfer.files);
    });

    btnAnalyzeDocs.addEventListener('click', async () => {
        if(selectedDocs.length < 2) return;
        
        docResults.style.display = 'none';
        docLoader.style.display = 'block';
        btnAnalyzeDocs.disabled = true;

        const formData = new FormData();
        selectedDocs.forEach(f => formData.append('files', f));

        try {
            const res = await fetch('/api/module1/analyze', {
                method: 'POST',
                body: formData
            });
            
            docLoader.style.display = 'none';
            btnAnalyzeDocs.disabled = false;

            if(!res.ok) {
                // Parse error JSON if possible
                const text = await res.text();
                let errMsg = 'Failed to analyze documents';
                try {
                    errMsg = JSON.parse(text).error || errMsg;
                } catch(e) {}
                throw new Error(errMsg);
            }

            // Read the response as a Blob (PDF)
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Auto-trigger download
            const a = document.createElement('a');
            a.href = url;
            a.download = `SentienOmega_Report_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            
            // Clean up
            setTimeout(() => window.URL.revokeObjectURL(url), 10000);

            docResults.innerHTML = '<div class="result-card" style="text-align:center; padding:3rem;"><h3 style="color:var(--accent-green)">Analysis Complete</h3><p>Your comprehensive PDF report has been downloaded automatically.</p></div>';
            docResults.style.display = 'block';
        } catch (err) {
            alert(err.message);
            docLoader.style.display = 'none';
            btnAnalyzeDocs.disabled = false;
        }
    });

    const renderDocResults = (data) => {
        // Obsolete: Results are now delivered directly as a PDF download.
    };


    // ---- Module 2: Image Classifier ----
    const imgInput = document.getElementById('img-input');
    const imgZone = document.getElementById('img-upload-zone');
    const imgPreviewCont = document.getElementById('img-preview-container');
    const imgPreview = document.getElementById('img-preview');
    const btnRemoveImg = document.getElementById('btn-remove-img');
    const imgCategory = document.getElementById('img-category');
    const btnClassifyImg = document.getElementById('btn-classify-img');
    const imgLoader = document.getElementById('img-loader');
    const imgResults = document.getElementById('img-results');

    let selectedImg = null;

    const handleImgFile = (file) => {
        if(!file.type.startsWith('image/')) return alert('Please upload an image file.');
        selectedImg = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            imgPreview.src = e.target.result;
            imgPreviewCont.style.display = 'inline-block';
            btnClassifyImg.disabled = false;
        };
        reader.readAsDataURL(file);
    };

    btnRemoveImg.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedImg = null;
        imgPreview.src = '';
        imgPreviewCont.style.display = 'none';
        btnClassifyImg.disabled = true;
        imgInput.value = '';
    });

    imgInput.addEventListener('change', (e) => { if(e.target.files[0]) handleImgFile(e.target.files[0]); });
    imgZone.addEventListener('dragover', (e) => { e.preventDefault(); imgZone.classList.add('dragover'); });
    imgZone.addEventListener('dragleave', () => imgZone.classList.remove('dragover'));
    imgZone.addEventListener('drop', (e) => {
        e.preventDefault();
        imgZone.classList.remove('dragover');
        if(e.dataTransfer.files[0]) handleImgFile(e.dataTransfer.files[0]);
    });

    btnClassifyImg.addEventListener('click', async () => {
        if(!selectedImg) return;
        
        imgResults.style.display = 'none';
        imgLoader.style.display = 'block';
        btnClassifyImg.disabled = true;

        const formData = new FormData();
        formData.append('image', selectedImg);
        if(imgCategory.value) formData.append('category', imgCategory.value);

        try {
            const res = await fetch('/api/module2/classify', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            imgLoader.style.display = 'none';
            btnClassifyImg.disabled = false;

            if(!res.ok) throw new Error(data.error || 'Failed to classify image');

            renderImgResults(data);
        } catch (err) {
            alert(err.message);
            imgLoader.style.display = 'none';
            btnClassifyImg.disabled = false;
        }
    });

    const renderImgResults = (data) => {
        const result = data.result;
        const verdict = result.verdict || "ERROR";
        
        let colorClass = 'verdict-orange';
        let barClass = 'fill-blue';
        if(verdict === 'AI') { colorClass = 'verdict-red'; barClass = 'fill-red'; }
        else if (verdict === 'REAL') { colorClass = 'verdict-green'; barClass = 'fill-green'; }

        let html = `
        <div class="result-card">
            <div class="card-header">
                <div>
                    <div class="card-title">${result.detector || 'Detector'}</div>
                    <div style="font-size:0.9rem; color:var(--text-secondary); margin-top:0.25rem;">
                        Category: <span style="color:var(--text-primary)">${data.detected_category || 'Unknown'}</span> 
                        (CLIP Conf: ${(data.clip_confidence * 100).toFixed(1)}%)
                    </div>
                </div>
                <div class="verdict-badge ${colorClass}">${verdict}</div>
            </div>
            
            <div class="progress-group" style="margin-top:2rem;">
                <div class="progress-label"><span>AI Probability</span><span>${(result.ai_probability*100).toFixed(1)}%</span></div>
                <div class="progress-track"><div class="progress-fill fill-red" style="width:${result.ai_probability*100}%"></div></div>
            </div>
            <div class="progress-group">
                <div class="progress-label"><span>Real Probability</span><span>${(result.real_probability*100).toFixed(1)}%</span></div>
                <div class="progress-track"><div class="progress-fill fill-green" style="width:${result.real_probability*100}%"></div></div>
            </div>

            ${result.reasons && result.reasons.length > 0 ? `
            <div style="margin-top:2rem;">
                <h4 style="margin-bottom:1rem; color:var(--text-secondary);">Evidence / Reasons</h4>
                <ul class="evidence-list">
                    ${result.reasons.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
        `;

        imgResults.innerHTML = html;
        imgResults.style.display = 'block';
    };
});
